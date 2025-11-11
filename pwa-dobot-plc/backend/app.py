"""
PWA Dobot-PLC Control Backend
Flask API with WebSocket support for real-time PLC monitoring
"""

from flask import Flask, jsonify, request, send_from_directory, Response
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import logging
import os
import time
import threading
import json
import subprocess
import sys
import cv2
from plc_client import PLCClient
from dobot_client import DobotClient
from camera_service import CameraService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, static_folder='../frontend')
app.config['SECRET_KEY'] = 'your-secret-key-here'
CORS(app)

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Initialize clients
plc_client = None
dobot_client = None
camera_service = None

# Polling state
poll_thread = None
poll_running = False
poll_interval = 0.1  # 100ms

def load_config():
    """Load configuration from config.json"""
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Return defaults if config doesn't exist
        return {
            "dobot": {
                "usb_path": "/dev/ttyACM0",
                "home_position": {"x": 200.0, "y": 0.0, "z": 150.0, "r": 0.0},
                "use_usb": True
            },
            "plc": {
                "ip": "192.168.1.150",
                "rack": 0,
                "slot": 1,
                "db_number": 1,
                "poll_interval": 2.0
            },
            "server": {"port": 8080}
        }

def save_config(config):
    """Save configuration to config.json"""
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)

def init_clients():
    """Initialize PLC and Dobot clients from config"""
    global plc_client, dobot_client, camera_service

    config = load_config()

    # PLC settings
    plc_config = config['plc']
    plc_client = PLCClient(
        plc_config['ip'],
        plc_config['rack'],
        plc_config['slot']
    )

    # Dobot settings
    dobot_config = config['dobot']
    dobot_client = DobotClient(
        use_usb=dobot_config.get('use_usb', True),
        usb_path=dobot_config.get('usb_path', '/dev/ttyACM0')
    )
    
    # Update home position if specified
    if 'home_position' in dobot_config:
        dobot_client.HOME_POSITION = dobot_config['home_position']

    # Camera settings
    camera_config = config.get('camera', {})
    camera_service = CameraService(
        camera_index=camera_config.get('index', 0),
        width=camera_config.get('width', 640),
        height=camera_config.get('height', 480)
    )
    # Initialize camera (but don't fail if camera not available)
    try:
        camera_service.initialize_camera()
        logger.info("Camera service initialized")
    except Exception as e:
        logger.warning(f"Camera initialization failed (may not be connected): {e}")

    logger.info(f"Clients initialized - PLC: {plc_config['ip']}, Dobot USB: {dobot_config.get('usb_path', 'auto-detect')}")

# ==================================================
# REST API Endpoints
# ==================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'timestamp': time.time()
    })

@app.route('/api/data', methods=['GET'])
def get_all_data():
    """Get all data in a single request to minimize PLC load"""
    # Connect if needed
    if not plc_client.is_connected():
        plc_client.connect()

    # Get all PLC data in optimized way with small delays between operations
    plc_status = plc_client.get_status()

    if plc_status['connected']:
        target_pose = plc_client.read_target_pose()
        time.sleep(0.15)  # 150ms delay to avoid job pending with S7-1200
        control_bits = plc_client.read_control_bits()
    else:
        target_pose = {'x': 0.0, 'y': 0.0, 'z': 0.0}
        control_bits = {}

    # Get Dobot data
    dobot_status_data = {
        'connected': dobot_client.connected,
        'last_error': dobot_client.last_error
    }
    dobot_pose = dobot_client.get_pose() if dobot_client.connected else {'x': 0.0, 'y': 0.0, 'z': 0.0, 'r': 0.0}

    return jsonify({
        'plc': {
            'status': plc_status,
            'pose': target_pose,
            'control': control_bits
        },
        'dobot': {
            'status': dobot_status_data,
            'pose': dobot_pose
        }
    })

@app.route('/api/plc/status', methods=['GET'])
def plc_status():
    """Get PLC connection status"""
    return jsonify(plc_client.get_status())

@app.route('/api/plc/connect', methods=['POST'])
def plc_connect():
    """Connect to PLC"""
    success = plc_client.connect()
    return jsonify({
        'success': success,
        'connected': plc_client.is_connected(),
        'error': plc_client.last_error if not success else None
    })

@app.route('/api/plc/disconnect', methods=['POST'])
def plc_disconnect():
    """Disconnect from PLC"""
    plc_client.disconnect()
    return jsonify({'success': True})

@app.route('/api/plc/pose', methods=['GET'])
def get_plc_pose():
    """Get target pose from PLC"""
    if not plc_client.is_connected():
        plc_client.connect()

    pose = plc_client.read_target_pose()
    return jsonify(pose)

@app.route('/api/plc/pose', methods=['POST'])
def set_plc_pose():
    """Write current pose to PLC"""
    data = request.json
    if not all(k in data for k in ['x', 'y', 'z']):
        return jsonify({'error': 'Missing x, y, or z'}), 400

    if not plc_client.is_connected():
        plc_client.connect()

    plc_client.write_current_pose(data)
    return jsonify({'success': True})

@app.route('/api/plc/control', methods=['GET'])
def get_control_bits():
    """Get all control bits"""
    if not plc_client.is_connected():
        plc_client.connect()

    bits = plc_client.read_control_bits()
    return jsonify(bits)

@app.route('/api/plc/control/<bit_name>', methods=['POST'])
def set_control_bit(bit_name):
    """Set a single control bit"""
    data = request.json
    value = data.get('value', False)

    if not plc_client.is_connected():
        plc_client.connect()

    success = plc_client.write_control_bit(bit_name, value)
    return jsonify({'success': success})

@app.route('/api/dobot/status', methods=['GET'])
def dobot_status():
    """Get Dobot connection status"""
    return jsonify({
        'connected': dobot_client.connected,
        'last_error': dobot_client.last_error
    })

@app.route('/api/dobot/debug', methods=['GET'])
def dobot_debug():
    """Get detailed Dobot debug information"""
    import os
    import glob
    
    # Get available USB ports
    available_ports = dobot_client.find_dobot_ports()
    
    # Check if pydobot is available
    try:
        from pydobot import Dobot as PyDobot
        pydobot_available = True
    except ImportError:
        pydobot_available = False
    
    # Check port permissions
    port_info = []
    for port in available_ports:
        try:
            import stat
            port_stat = os.stat(port)
            permissions = oct(port_stat.st_mode)[-3:]
            port_info.append({
                'port': port,
                'exists': True,
                'permissions': permissions,
                'readable': bool(port_stat.st_mode & stat.S_IRUSR),
                'writable': bool(port_stat.st_mode & stat.S_IWUSR)
            })
        except Exception as e:
            port_info.append({
                'port': port,
                'exists': False,
                'error': str(e)
            })
    
    return jsonify({
        'pydobot_available': pydobot_available,
        'use_usb': dobot_client.use_usb,
        'configured_port': dobot_client.usb_path,
        'actual_port': dobot_client.actual_port,
        'connected': dobot_client.connected,
        'last_error': dobot_client.last_error,
        'available_ports': available_ports,
        'port_details': port_info
    })

@app.route('/api/dobot/connect', methods=['POST'])
def dobot_connect():
    """Connect to Dobot"""
    logger.info("🔌 Manual Dobot connection requested")
    success = dobot_client.connect()
    if success:
        logger.info("✅ Manual Dobot connection successful")
    else:
        logger.error(f"❌ Manual Dobot connection failed: {dobot_client.last_error}")
    return jsonify({
        'success': success,
        'connected': dobot_client.connected,
        'error': dobot_client.last_error if not success else None
    })

@app.route('/api/dobot/home', methods=['POST'])
def dobot_home():
    """Home Dobot robot"""
    if not dobot_client.connected:
        return jsonify({'error': 'Dobot not connected'}), 503

    logger.info("🏠 Home command received from web interface")
    success = dobot_client.home(wait=True)  # Wait=True for immediate execution
    logger.info(f"✅ Home command result: {success}")
    return jsonify({'success': success})

@app.route('/api/dobot/move', methods=['POST'])
def dobot_move():
    """Move Dobot to position"""
    data = request.json
    if not all(k in data for k in ['x', 'y', 'z']):
        return jsonify({'error': 'Missing x, y, or z'}), 400

    if not dobot_client.connected:
        return jsonify({'error': 'Dobot not connected'}), 503

    # Get position before move
    pos_before = dobot_client.get_pose()
    logger.info(f"▶️ Move command: ({data['x']}, {data['y']}, {data['z']}, {data.get('r', 0)}) - Current: ({pos_before['x']:.1f}, {pos_before['y']:.1f}, {pos_before['z']:.1f})")

    success = dobot_client.move_to(
        data['x'],
        data['y'],
        data['z'],
        data.get('r', 0),
        wait=True  # Wait=True for immediate execution
    )

    if success:
        # Verify robot actually moved
        time.sleep(0.3)  # Brief delay to ensure movement settled
        pos_after = dobot_client.get_pose()

        # Calculate distance moved
        distance = ((pos_after['x'] - pos_before['x'])**2 +
                   (pos_after['y'] - pos_before['y'])**2 +
                   (pos_after['z'] - pos_before['z'])**2)**0.5

        if distance > 1.0:  # Moved more than 1mm
            logger.info(f"✅ ACTUAL MOVEMENT: Moved {distance:.1f}mm to ({pos_after['x']:.1f}, {pos_after['y']:.1f}, {pos_after['z']:.1f})")
            return jsonify({'success': True, 'executed': True, 'distance_moved': round(distance, 1)})
        else:
            logger.error(f"⚠️ ROBOT DID NOT MOVE! Distance: {distance:.1f}mm - Position: ({pos_after['x']:.1f}, {pos_after['y']:.1f}, {pos_after['z']:.1f})")
            return jsonify({'success': False, 'error': f'Robot did not move (only {distance:.1f}mm)', 'distance_moved': round(distance, 1)}), 500
    else:
        error_msg = dobot_client.last_error or 'Movement failed'
        logger.error(f"❌ Move command failed: {error_msg}")
        return jsonify({'success': False, 'error': error_msg}), 500

@app.route('/api/dobot/pose', methods=['GET'])
def get_dobot_pose():
    """Get current Dobot pose"""
    if not dobot_client.connected:
        return jsonify({'error': 'Dobot not connected'}), 503

    pose = dobot_client.get_pose()
    return jsonify(pose)

@app.route('/api/dobot/suction', methods=['POST'])
def dobot_suction():
    """Control suction cup"""
    if not dobot_client.connected:
        return jsonify({'error': 'Dobot not connected'}), 503

    data = request.json
    enable = data.get('enable', False)
    
    try:
        logger.info(f"💨 Suction cup: {'ON' if enable else 'OFF'}")
        dobot_client.set_suction(enable)
        return jsonify({'success': True, 'enabled': enable})
    except Exception as e:
        logger.error(f"❌ Suction control failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/dobot/gripper', methods=['POST'])
def dobot_gripper():
    """Control gripper (if available)"""
    if not dobot_client.connected:
        return jsonify({'error': 'Dobot not connected'}), 503

    data = request.json
    open_gripper = data.get('open', True)
    
    try:
        # Check if gripper control method exists
        if hasattr(dobot_client, 'set_gripper'):
            logger.info(f"✋ Gripper: {'OPEN' if open_gripper else 'CLOSE'}")
            dobot_client.set_gripper(open_gripper)
            return jsonify({'success': True, 'open': open_gripper})
        else:
            logger.warning("⚠️ Gripper not available on this Dobot model")
            return jsonify({
                'success': False,
                'message': 'Gripper not available. This Dobot model only has suction cup.'
            })
    except Exception as e:
        logger.error(f"❌ Gripper control failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/emergency-stop', methods=['POST'])
def emergency_stop():
    """Emergency stop - stop both Dobot and signal PLC"""
    logger.error("🛑 EMERGENCY STOP TRIGGERED")

    results = {}

    # Stop Dobot
    if dobot_client.connected:
        dobot_client.stop_queue()  # Stop queue execution first
        dobot_client.clear_queue()  # Then clear queued commands
        results['dobot'] = 'stopped'

    # Signal PLC
    if plc_client.is_connected():
        plc_client.write_control_bit('estop', True)
        results['plc'] = 'signaled'

    return jsonify({'success': True, **results})

@app.route('/api/dobot/test', methods=['POST'])
def dobot_test():
    """Run comprehensive Dobot test sequence"""
    if not dobot_client.connected:
        return jsonify({'error': 'Dobot not connected', 'steps': []}), 503

    results = []
    success = True

    try:
        # Step 1: Get current position
        logger.info("🧪 Test Step 1: Getting current position...")
        pos = dobot_client.get_pose()
        results.append({
            'step': 1,
            'name': 'Get Current Position',
            'success': True,
            'message': f"X: {pos['x']:.2f}, Y: {pos['y']:.2f}, Z: {pos['z']:.2f}, R: {pos['r']:.2f}"
        })
        time.sleep(0.5)

        # Step 2: Move to home position
        logger.info("🧪 Test Step 2: Moving to HOME position...")
        if dobot_client.home(wait=True):
            results.append({
                'step': 2,
                'name': 'Move to Home',
                'success': True,
                'message': f"Moved to ({dobot_client.HOME_POSITION['x']}, {dobot_client.HOME_POSITION['y']}, {dobot_client.HOME_POSITION['z']})"
            })
        else:
            results.append({'step': 2, 'name': 'Move to Home', 'success': False, 'message': 'Failed to move'})
            success = False
        time.sleep(1)

        # Step 3: Verify home position
        logger.info("🧪 Test Step 3: Verifying position...")
        pos = dobot_client.get_pose()
        results.append({
            'step': 3,
            'name': 'Verify Position',
            'success': True,
            'message': f"X: {pos['x']:.2f}, Y: {pos['y']:.2f}, Z: {pos['z']:.2f}"
        })
        time.sleep(0.5)

        # Step 4: Small movement test (20mm forward)
        logger.info("🧪 Test Step 4: Small movement test...")
        home = dobot_client.HOME_POSITION
        if dobot_client.move_to(home['x'] + 20, home['y'], home['z'], home['r'], wait=True):
            results.append({
                'step': 4,
                'name': 'Small Movement (forward 20mm)',
                'success': True,
                'message': 'Movement completed successfully'
            })
            time.sleep(1)
            
            # Move back
            logger.info("🧪 Test Step 4b: Moving back...")
            dobot_client.home(wait=True)
            time.sleep(0.5)
        else:
            results.append({'step': 4, 'name': 'Small Movement', 'success': False, 'message': 'Failed to move'})
            success = False

        # Step 5: Suction test
        logger.info("🧪 Test Step 5: Testing suction cup...")
        try:
            dobot_client.set_suction(True)
            time.sleep(2)
            dobot_client.set_suction(False)
            results.append({
                'step': 5,
                'name': 'Suction Cup Test',
                'success': True,
                'message': 'ON/OFF cycle completed'
            })
        except Exception as e:
            results.append({'step': 5, 'name': 'Suction Cup Test', 'success': False, 'message': str(e)})
            success = False

        logger.info("✅ Dobot test sequence completed!")
        return jsonify({
            'success': success,
            'steps': results,
            'message': 'All tests passed!' if success else 'Some tests failed'
        })

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return jsonify({
            'success': False,
            'steps': results,
            'error': str(e)
        }), 500

@app.route('/api/config', methods=['GET'])
def get_config():
    """Get current configuration"""
    try:
        config = load_config()
        # Ensure vision config exists
        if 'vision' not in config:
            config['vision'] = {
                'fault_bit_enabled': False,
                'fault_bit_byte': 1,
                'fault_bit_bit': 0
            }
        return jsonify(config)
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/config', methods=['POST'])
def update_config():
    """Update configuration (for vision config)"""
    try:
        new_config = request.json
        current_config = load_config()
        
        # Update vision config if provided
        if 'vision' in new_config:
            current_config.setdefault('vision', {})
            current_config['vision'].update(new_config['vision'])
            save_config(current_config)
            return jsonify({'success': True, 'message': 'Configuration saved'})
        
        return jsonify({'error': 'No vision config provided'}), 400
    except Exception as e:
        logger.error(f"Error saving config: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/settings', methods=['GET'])
def get_settings():
    """Get current configuration"""
    try:
        config = load_config()
        
        # Add available USB ports to the response
        available_ports = dobot_client.find_dobot_ports() if dobot_client else []
        config['available_usb_ports'] = available_ports
        
        return jsonify(config)
    except Exception as e:
        logger.error(f"Error loading settings: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/settings', methods=['POST'])
def update_settings():
    """Update configuration"""
    try:
        new_config = request.json
        
        # Validate required fields
        if 'dobot' not in new_config or 'plc' not in new_config:
            return jsonify({'error': 'Missing required config sections'}), 400
        
        # Load current config and merge
        current_config = load_config()
        current_config['dobot'].update(new_config['dobot'])
        current_config['plc'].update(new_config['plc'])
        
        # Update vision config if provided
        if 'vision' in new_config:
            current_config.setdefault('vision', {})
            current_config['vision'].update(new_config['vision'])
        
        # Save to file
        save_config(current_config)
        
        logger.info("⚙️ Settings updated - restart required to apply changes")
        return jsonify({
            'success': True,
            'message': 'Settings saved. Restart server to apply changes.'
        })
    except Exception as e:
        logger.error(f"Error saving settings: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/restart', methods=['POST'])
def restart_server():
    """Restart the server"""
    try:
        logger.info("🔄 Server restart requested")
        
        # Try PM2 restart first (if running under PM2)
        try:
            result = subprocess.run(['pm2', 'restart', 'pwa-dobot-plc'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                logger.info("✅ PM2 restart successful")
                return jsonify({
                    'success': True,
                    'message': 'Server restarting via PM2...'
                })
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        # Fallback: try systemctl restart (if running as service)
        try:
            result = subprocess.run(['sudo', 'systemctl', 'restart', 'pwa-dobot-plc'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                logger.info("✅ Systemctl restart successful")
                return jsonify({
                    'success': True,
                    'message': 'Server restarting via systemctl...'
                })
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        # Last resort: exit the process (will be restarted by supervisor/PM2)
        logger.info("⚠️ No restart method available, exiting process")
        threading.Timer(2.0, lambda: sys.exit(0)).start()
        return jsonify({
            'success': True,
            'message': 'Server will restart in 2 seconds...'
        })
        
    except Exception as e:
        logger.error(f"Error restarting server: {e}")
        return jsonify({'error': str(e)}), 500

# ==================================================
# WebSocket Events
# ==================================================

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info(f"Client connected: {request.sid}")
    emit('connection_status', {'connected': True})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info(f"Client disconnected: {request.sid}")

@socketio.on('start_polling')
def handle_start_polling():
    """Start real-time polling"""
    global poll_running
    if not poll_running:
        start_polling_thread()
    emit('polling_status', {'running': True})

@socketio.on('stop_polling')
def handle_stop_polling():
    """Stop real-time polling"""
    global poll_running
    poll_running = False
    emit('polling_status', {'running': False})

# ==================================================
# Background Polling Thread
# ==================================================

def start_polling_thread():
    """Start background polling thread"""
    global poll_thread, poll_running

    if poll_thread and poll_thread.is_alive():
        return

    poll_running = True
    poll_thread = threading.Thread(target=poll_loop, daemon=True)
    poll_thread.start()
    logger.info("Polling thread started")

def poll_loop():
    """Background polling loop for real-time data"""
    global poll_running

    while poll_running:
        try:
            # Ensure PLC connection
            if not plc_client.is_connected():
                plc_client.connect()

            # Read PLC data
            control_bits = plc_client.read_control_bits()
            target_pose = plc_client.read_target_pose()

            # Read Dobot data
            dobot_pose = None
            if dobot_client.connected:
                dobot_pose = dobot_client.get_pose()

            # Emit data to all connected clients
            socketio.emit('plc_data', {
                'control_bits': control_bits,
                'target_pose': target_pose,
                'timestamp': time.time()
            })

            if dobot_pose:
                socketio.emit('dobot_data', {
                    'pose': dobot_pose,
                    'timestamp': time.time()
                })

        except Exception as e:
            logger.error(f"Polling error: {e}")

        time.sleep(poll_interval)

    logger.info("Polling thread stopped")

# ==================================================
# Camera & Vision System Endpoints
# ==================================================

def write_plc_fault_bit(defects_found: bool):
    """Write vision fault status to PLC memory bit"""
    try:
        config = load_config()
        vision_config = config.get('vision', {})
        
        # Check if fault bit is enabled
        if not vision_config.get('fault_bit_enabled', False):
            return {'written': False, 'reason': 'disabled'}
        
        # Get bit address
        byte_offset = vision_config.get('fault_bit_byte', 1)
        bit_offset = vision_config.get('fault_bit_bit', 0)
        
        # Ensure PLC is connected
        if not plc_client.is_connected():
            plc_client.connect()
        
        # Write fault bit (True = defects found, False = no defects)
        if plc_client.is_connected():
            success = plc_client.write_m_bit(byte_offset, bit_offset, defects_found)
            if success:
                logger.info(f"Vision fault bit M{byte_offset}.{bit_offset} set to {defects_found}")
                return {'written': True, 'address': f'M{byte_offset}.{bit_offset}', 'value': defects_found}
            else:
                logger.warning(f"Failed to write vision fault bit M{byte_offset}.{bit_offset}")
                return {'written': False, 'reason': 'write_failed', 'address': f'M{byte_offset}.{bit_offset}'}
        else:
            logger.warning("PLC not connected, cannot write vision fault bit")
            return {'written': False, 'reason': 'plc_not_connected'}
    except Exception as e:
        logger.error(f"Error writing vision fault bit to PLC: {e}")
        return {'written': False, 'reason': str(e)}

def generate_frames():
    """Generator function for MJPEG streaming"""
    while True:
        if camera_service is None:
            break
        
        frame_bytes = camera_service.get_frame_jpeg(quality=85)
        if frame_bytes is None:
            time.sleep(0.1)
            continue
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        time.sleep(0.033)  # ~30 FPS

@app.route('/api/camera/stream')
def camera_stream():
    """MJPEG video stream endpoint"""
    if camera_service is None:
        return jsonify({'error': 'Camera service not initialized'}), 503
    
    return Response(
        generate_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

@app.route('/api/camera/status', methods=['GET'])
def camera_status():
    """Get camera connection status"""
    if camera_service is None:
        return jsonify({
            'initialized': False,
            'connected': False,
            'error': 'Camera service not initialized'
        })
    
    try:
        frame = camera_service.read_frame()
        connected = frame is not None
        
        return jsonify({
            'initialized': True,
            'connected': connected,
            'camera_index': camera_service.camera_index,
            'resolution': {
                'width': camera_service.width,
                'height': camera_service.height
            },
            'last_frame_time': camera_service.frame_time
        })
    except Exception as e:
        logger.error(f"Error checking camera status: {e}")
        return jsonify({
            'initialized': True,
            'connected': False,
            'error': str(e)
        }), 500

@app.route('/api/camera/connect', methods=['POST'])
def camera_connect():
    """Initialize and connect to camera"""
    global camera_service
    
    try:
        data = request.json or {}
        camera_index = data.get('index', 0)
        width = data.get('width', 640)
        height = data.get('height', 480)
        
        if camera_service is None:
            camera_service = CameraService(
                camera_index=camera_index,
                width=width,
                height=height
            )
        
        success = camera_service.initialize_camera()
        
        if success:
            # Update config
            config = load_config()
            config['camera'] = {
                'index': camera_index,
                'width': width,
                'height': height
            }
            save_config(config)
        
        return jsonify({
            'success': success,
            'connected': success,
            'error': None if success else 'Failed to initialize camera'
        })
    except Exception as e:
        logger.error(f"Error connecting camera: {e}")
        return jsonify({
            'success': False,
            'connected': False,
            'error': str(e)
        }), 500

@app.route('/api/camera/disconnect', methods=['POST'])
def camera_disconnect():
    """Disconnect and release camera"""
    global camera_service
    
    try:
        if camera_service is not None:
            camera_service.release_camera()
        
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error disconnecting camera: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/camera/capture', methods=['GET'])
def camera_capture():
    """Capture a single frame as JPEG"""
    if camera_service is None:
        return jsonify({'error': 'Camera service not initialized'}), 503
    
    try:
        frame_bytes = camera_service.get_frame_jpeg(quality=95)
        if frame_bytes is None:
            return jsonify({'error': 'Failed to capture frame'}), 500
        
        return Response(
            frame_bytes,
            mimetype='image/jpeg',
            headers={'Content-Disposition': 'inline; filename=capture.jpg'}
        )
    except Exception as e:
        logger.error(f"Error capturing frame: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/vision/detect', methods=['POST'])
def vision_detect():
    """Run defect detection on current frame"""
    if camera_service is None:
        return jsonify({'error': 'Camera service not initialized'}), 503
    
    try:
        data = request.json or {}
        method = data.get('method', 'combined')  # 'blob', 'contour', 'edge', 'combined'
        
        # Read current frame
        frame = camera_service.read_frame()
        if frame is None:
            return jsonify({'error': 'Failed to read frame from camera'}), 500
        
        # Extract detection parameters
        detection_params = data.get('params', {})
        
        # Run defect detection with parameters
        results = camera_service.detect_defects(frame, method=method, params=detection_params)
        
        # Write to PLC fault bit if enabled
        plc_write_result = write_plc_fault_bit(results.get('defects_found', False))
        if plc_write_result:
            results['plc_write'] = plc_write_result
        
        # Optionally draw defects on frame
        if data.get('annotate', False) and results['defects_found']:
            annotated_frame = camera_service.draw_defects(frame, results['defects'])
            # Encode annotated frame
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 85]
            ret, buffer = cv2.imencode('.jpg', annotated_frame, encode_param)
            if ret:
                results['annotated_image'] = buffer.tobytes().hex()  # Send as hex string
        
        return jsonify(results)
    except Exception as e:
        logger.error(f"Error in defect detection: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/vision/analyze', methods=['POST'])
def vision_analyze():
    """Analyze frame and return annotated image"""
    if camera_service is None:
        return jsonify({'error': 'Camera service not initialized'}), 503
    
    try:
        data = request.json or {}
        method = data.get('method', 'combined')
        
        # Read current frame
        frame = camera_service.read_frame()
        if frame is None:
            return jsonify({'error': 'Failed to read frame from camera'}), 500
        
        # Extract detection parameters
        detection_params = data.get('params', {})
        
        # Run defect detection with parameters
        results = camera_service.detect_defects(frame, method=method, params=detection_params)
        
        # Write to PLC fault bit if enabled
        plc_write_result = write_plc_fault_bit(results.get('defects_found', False))
        if plc_write_result:
            results['plc_write'] = plc_write_result
        
        # Draw defects on frame
        annotated_frame = camera_service.draw_defects(frame, results['defects'])
        
        # Encode as JPEG
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
        ret, buffer = cv2.imencode('.jpg', annotated_frame, encode_param)
        
        if not ret:
            return jsonify({'error': 'Failed to encode annotated image'}), 500
        
        # Return both JSON results and image
        return Response(
            buffer.tobytes(),
            mimetype='image/jpeg',
            headers={
                'X-Defect-Count': str(results['defect_count']),
                'X-Defects-Found': str(results['defects_found']).lower(),
                'X-Confidence': str(results['confidence']),
                'Content-Disposition': 'inline; filename=analyzed.jpg'
            }
        )
    except Exception as e:
        logger.error(f"Error in vision analysis: {e}")
        return jsonify({'error': str(e)}), 500

# ==================================================
# Serve PWA Frontend
# ==================================================

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_pwa(path):
    """Serve PWA frontend"""
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

# ==================================================
# Application Startup
# ==================================================

if __name__ == '__main__':
    init_clients()

    # Auto-connect to PLC
    plc_client.connect()

    # Auto-connect to Dobot
    logger.info("🤖 Attempting to connect to Dobot robot...")
    dobot_connected = dobot_client.connect()
    if dobot_connected:
        logger.info("✅ Dobot connected successfully")
    else:
        logger.error(f"❌ Dobot connection failed: {dobot_client.last_error}")
        logger.error("💡 Check the debug logs above for detailed troubleshooting steps")

    # Start polling
    start_polling_thread()

    # Start server
    port = int(os.getenv('PORT', 8080))
    logger.info(f"Starting server on port {port}")
    socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)
