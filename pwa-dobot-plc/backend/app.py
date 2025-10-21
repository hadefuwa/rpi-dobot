"""
PWA Dobot-PLC Control Backend
Flask API with WebSocket support for real-time PLC monitoring
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import logging
import os
import time
import threading
from plc_client import PLCClient
from dobot_client import DobotClient

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

# Polling state
poll_thread = None
poll_running = False
poll_interval = 0.1  # 100ms

def init_clients():
    """Initialize PLC and Dobot clients from environment variables"""
    global plc_client, dobot_client

    # PLC settings
    plc_ip = os.getenv('PLC_IP', '192.168.0.150')
    plc_rack = int(os.getenv('PLC_RACK', '0'))
    plc_slot = int(os.getenv('PLC_SLOT', '1'))

    # Dobot settings
    dobot_usb = os.getenv('DOBOT_USE_USB', 'true').lower() == 'true'
    dobot_usb_path = os.getenv('DOBOT_USB_PATH', '/dev/ttyACM0')

    plc_client = PLCClient(plc_ip, plc_rack, plc_slot)
    dobot_client = DobotClient(use_usb=dobot_usb, usb_path=dobot_usb_path)

    logger.info(f"Clients initialized - PLC: {plc_ip}, Dobot USB: {dobot_usb}")

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

@app.route('/api/dobot/connect', methods=['POST'])
def dobot_connect():
    """Connect to Dobot"""
    success = dobot_client.connect()
    return jsonify({
        'success': success,
        'connected': dobot_client.connected
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

    logger.info(f"▶️ Move command received: ({data['x']}, {data['y']}, {data['z']}, {data.get('r', 0)})")
    success = dobot_client.move_to(
        data['x'],
        data['y'],
        data['z'],
        data.get('r', 0),
        wait=True  # Wait=True for immediate execution
    )
    logger.info(f"✅ Move command result: {success}")
    return jsonify({'success': success, 'executed': success})

@app.route('/api/dobot/pose', methods=['GET'])
def get_dobot_pose():
    """Get current Dobot pose"""
    if not dobot_client.connected:
        return jsonify({'error': 'Dobot not connected'}), 503

    pose = dobot_client.get_pose()
    return jsonify(pose)

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
    dobot_client.connect()

    # Start polling
    start_polling_thread()

    # Start server
    port = int(os.getenv('PORT', 8080))
    logger.info(f"Starting server on port {port}")
    socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)
