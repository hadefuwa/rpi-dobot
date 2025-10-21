"""
Dobot Robot Communication Client - Improved pydobot Version
Uses pydobot with proper parameter initialization and queue management
"""

import logging
import time
from typing import Dict, Optional, List
import struct

logger = logging.getLogger(__name__)

# Try to import pydobot
try:
    from pydobot import Dobot as PyDobot
    from serial.tools import list_ports
    import serial
    DOBOT_AVAILABLE = True
except ImportError:
    DOBOT_AVAILABLE = False
    logger.warning("pydobot not installed - Dobot functionality disabled")

class DobotClient:
    """Dobot Robot Communication Client using Improved pydobot"""

    # Default home position for Dobot Magician
    HOME_POSITION = {
        'x': 200.0,
        'y': 0.0,
        'z': 150.0,
        'r': 0.0
    }

    # Default movement parameters
    DEFAULT_VELOCITY_RATIO = 100  # 1-100%
    DEFAULT_ACCELERATION_RATIO = 100  # 1-100%

    # Protocol constants (from official Dobot protocol)
    PROTOCOL_PTP_COMMON_PARAMS = 83  # Set PTP common parameters
    PROTOCOL_PTP_CMD = 84  # PTP command
    PROTOCOL_QUEUE_START = 240  # Start queue execution
    PROTOCOL_QUEUE_STOP = 241  # Stop queue execution
    PROTOCOL_QUEUE_CLEAR = 245  # Clear queue

    def __init__(self, use_usb: bool = True, usb_path: str = '/dev/ttyACM0'):
        """
        Initialize Dobot client with improved pydobot

        Args:
            use_usb: Use USB connection (True) or skip Dobot entirely (False)
            usb_path: USB device path for Dobot
        """
        self.use_usb = use_usb
        self.usb_path = usb_path
        self.connected = False
        self.last_error = ""
        self.device = None
        self.actual_port = None

        # Movement parameters
        self.velocity_ratio = self.DEFAULT_VELOCITY_RATIO
        self.acceleration_ratio = self.DEFAULT_ACCELERATION_RATIO

    def connect(self) -> bool:
        """Connect to Dobot robot with improved initialization"""
        if not self.use_usb or not DOBOT_AVAILABLE:
            logger.info("Dobot connection skipped (USB disabled or library not available)")
            return False

        try:
            # Try configured port first
            if self._try_connect(self.usb_path):
                self._initialize_robot()
                return True

            # If configured port fails, scan all USB ports
            logger.warning(f"⚠️ {self.usb_path} not found, scanning all USB ports...")
            available_ports = self.find_dobot_ports()

            if not available_ports:
                self.last_error = "No USB devices found (ttyACM* or ttyUSB*)"
                logger.error(f"❌ {self.last_error}")
                return False

            logger.info(f"Found USB devices: {', '.join(available_ports)}")

            # Try each port
            for port in available_ports:
                if port == self.usb_path:
                    continue  # Already tried this one

                if self._try_connect(port):
                    logger.info(f"💡 TIP: Update your .env file to use DOBOT_USB_PATH={port}")
                    self._initialize_robot()
                    return True

            self.last_error = f"Dobot not found on any USB port: {', '.join(available_ports)}"
            logger.error(f"❌ {self.last_error}")
            return False

        except Exception as e:
            self.last_error = f"Connection error: {str(e)}"
            logger.error(f"❌ {self.last_error}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    def _try_connect(self, port: str) -> bool:
        """Try to connect to a specific port"""
        try:
            logger.info(f"Trying to connect to Dobot on {port}...")
            self.device = PyDobot(port=port, verbose=False)
            self.connected = True
            self.actual_port = port
            logger.info(f"✅ Connected to Dobot on {port}")
            return True
        except Exception as e:
            logger.debug(f"Port {port} failed: {e}")
            return False

    def _initialize_robot(self):
        """Initialize robot parameters - CRITICAL for movement to work"""
        if not self.device:
            return

        try:
            logger.info("🔧 Initializing robot parameters...")

            # CRITICAL: Clear all alarms first!
            # This was the issue preventing movement
            try:
                from pydobot.message import Message
                from pydobot.enums.CommunicationProtocolIDs import CommunicationProtocolIDs
                from pydobot.enums.ControlValues import ControlValues

                msg = Message()
                msg.id = CommunicationProtocolIDs.CLEAR_ALL_ALARMS_STATE
                msg.ctrl = ControlValues.ONE
                self.device._send_command(msg)
                logger.info("✅ Cleared all alarms")
            except Exception as e:
                logger.warning(f"⚠️ Could not clear alarms: {e}")

            # Clear any existing queue
            try:
                self.device.clear_command_queue()
                logger.info("✅ Cleared command queue")
            except:
                pass

            # Set speed parameters
            self.set_speed(self.velocity_ratio, self.acceleration_ratio)

            # Give the robot a moment to process
            time.sleep(0.1)

            logger.info("✅ Robot initialized successfully")

        except Exception as e:
            logger.error(f"❌ Error initializing robot: {e}")
            import traceback
            logger.error(traceback.format_exc())

    def disconnect(self):
        """Disconnect from Dobot"""
        if self.connected and self.device:
            try:
                self.device.close()
                self.connected = False
                self.device = None
                logger.info("✅ Disconnected from Dobot")
            except Exception as e:
                logger.error(f"❌ Error disconnecting from Dobot: {e}")

    def get_pose(self) -> Dict[str, float]:
        """Get current robot position"""
        if not self.connected or not self.device:
            return {'x': 0.0, 'y': 0.0, 'z': 0.0, 'r': 0.0}

        try:
            # pydobot.pose() returns tuple: (x, y, z, r, j1, j2, j3, j4)
            pose = self.device.pose()
            return {
                'x': float(pose[0]),
                'y': float(pose[1]),
                'z': float(pose[2]),
                'r': float(pose[3])
            }
        except Exception as e:
            self.last_error = f"Error getting pose: {str(e)}"
            logger.error(self.last_error)
            return {'x': 0.0, 'y': 0.0, 'z': 0.0, 'r': 0.0}

    def move_to(self, x: float, y: float, z: float, r: float = 0, wait: bool = True) -> bool:
        """
        Move robot to position with improved command handling

        Args:
            x: X coordinate in mm
            y: Y coordinate in mm
            z: Z coordinate in mm
            r: Rotation in degrees
            wait: Wait for movement to complete before returning

        Returns:
            True if command sent successfully, False otherwise
        """
        if not self.connected or not self.device:
            self.last_error = "Dobot not connected"
            logger.error("❌ Dobot not connected")
            return False

        try:
            logger.info(f"🤖 Executing move_to({x}, {y}, {z}, {r}, wait={wait})")

            # CRITICAL: Clear alarms AND reset pose before EVERY movement
            # This was the key difference in the working test!
            try:
                from pydobot.message import Message
                from pydobot.enums.CommunicationProtocolIDs import CommunicationProtocolIDs
                from pydobot.enums.ControlValues import ControlValues

                # Clear alarms
                msg = Message()
                msg.id = CommunicationProtocolIDs.CLEAR_ALL_ALARMS_STATE
                msg.ctrl = ControlValues.ONE
                self.device._send_command(msg)
                logger.info("✅ Cleared alarms before movement")

                # Reset pose (CRITICAL!)
                msg = Message()
                msg.id = CommunicationProtocolIDs.RESET_POSE
                msg.ctrl = ControlValues.ZERO
                msg.params = bytearray([0x01, 0x00, 0x00, 0x00])
                self.device._send_command(msg)
                logger.info("✅ Reset pose before movement")

                time.sleep(0.1)  # Brief pause after reset
            except Exception as e:
                logger.warning(f"⚠️ Could not reset before movement: {e}")

            # Get initial position for verification
            initial_pose = self.get_pose()
            logger.info(f"📍 Initial position: X={initial_pose['x']:.2f}, Y={initial_pose['y']:.2f}, Z={initial_pose['z']:.2f}")

            # Use pydobot's internal _set_ptp_cmd directly for more control
            from pydobot.enums import PTPMode
            self.device._set_ptp_cmd(x, y, z, r, mode=PTPMode.MOVL_XYZ, wait=wait)

            if wait:
                # Small delay to let movement complete
                time.sleep(0.2)

                # Verify final position
                final_pose = self.get_pose()
                logger.info(f"📍 Final position: X={final_pose['x']:.2f}, Y={final_pose['y']:.2f}, Z={final_pose['z']:.2f}")

                # Check if we actually moved
                distance_moved = (
                    abs(final_pose['x'] - initial_pose['x']) +
                    abs(final_pose['y'] - initial_pose['y']) +
                    abs(final_pose['z'] - initial_pose['z'])
                )

                if distance_moved > 1.0:
                    logger.info(f"✅ Movement completed! Moved {distance_moved:.2f}mm total")
                else:
                    logger.warning(f"⚠️ Position barely changed ({distance_moved:.2f}mm). Robot may not be moving.")

            logger.info(f"✅ Move command {'completed' if wait else 'queued'}: ({x}, {y}, {z}, {r})")
            return True

        except Exception as e:
            self.last_error = f"Error moving: {str(e)}"
            logger.error(f"❌ Move error: {self.last_error}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    def home(self, wait: bool = True) -> bool:
        """
        Move robot to home position

        Args:
            wait: Wait for movement to complete before returning

        Returns:
            True if command sent successfully, False otherwise
        """
        logger.info(f"🏠 Moving to home position: {self.HOME_POSITION}")
        return self.move_to(
            self.HOME_POSITION['x'],
            self.HOME_POSITION['y'],
            self.HOME_POSITION['z'],
            self.HOME_POSITION['r'],
            wait=wait
        )

    def set_speed(self, velocity_ratio: int, acceleration_ratio: int):
        """
        Set movement speed parameters

        Args:
            velocity_ratio: Velocity ratio 1-100%
            acceleration_ratio: Acceleration ratio 1-100%
        """
        if not self.connected or not self.device:
            return

        try:
            self.velocity_ratio = max(1, min(100, velocity_ratio))
            self.acceleration_ratio = max(1, min(100, acceleration_ratio))

            # Use pydobot's speed method if available
            if hasattr(self.device, 'speed'):
                self.device.speed(self.velocity_ratio, self.acceleration_ratio)
                logger.info(f"✅ Speed set: velocity={self.velocity_ratio}%, accel={self.acceleration_ratio}%")
            else:
                logger.warning("⚠️ Speed setting not available in this pydobot version")

        except Exception as e:
            logger.error(f"❌ Error setting speed: {e}")

    def start_queue(self):
        """Start executing the command queue"""
        if not self.connected or not self.device:
            return

        try:
            if hasattr(self.device, 'start_queue'):
                self.device.start_queue()
                logger.info("✅ Command queue started")
            else:
                logger.debug("start_queue method not available")
        except Exception as e:
            logger.error(f"❌ Error starting queue: {e}")

    def stop_queue(self):
        """Stop executing the command queue"""
        if not self.connected or not self.device:
            return

        try:
            if hasattr(self.device, 'stop_queue'):
                self.device.stop_queue()
                logger.info("Command queue stopped")
            else:
                self.clear_queue()
        except Exception as e:
            logger.error(f"❌ Error stopping queue: {e}")

    def clear_queue(self):
        """Clear command queue"""
        if not self.connected or not self.device:
            return

        try:
            self.device.clear_command_queue()
            logger.info("Command queue cleared")
        except Exception as e:
            logger.error(f"Error clearing queue: {e}")

    def set_suction(self, enable: bool):
        """Enable/disable suction cup"""
        if not self.connected or not self.device:
            return

        try:
            self.device.suck(enable)
            logger.info(f"💨 Suction cup {'enabled' if enable else 'disabled'}")
        except Exception as e:
            logger.error(f"❌ Error setting suction: {e}")

    def set_gripper(self, open_gripper: bool):
        """
        Control gripper (open/close)

        Args:
            open_gripper: True to open, False to close
        """
        if not self.connected or not self.device:
            logger.error("❌ Dobot not connected")
            return

        try:
            # PyDobot gripper control
            # grip() method: True = grip (close), False = release (open)
            # So we need to invert the logic: open_gripper=True means grip=False
            self.device.grip(not open_gripper)
            logger.info(f"✋ Gripper {'opened' if open_gripper else 'closed'}")
        except Exception as e:
            logger.error(f"❌ Error controlling gripper: {e}")

    def emergency_stop(self):
        """Emergency stop - clears queue"""
        if not self.connected or not self.device:
            return

        try:
            self.clear_queue()
            logger.warning("🛑 EMERGENCY STOP executed")
        except Exception as e:
            logger.error(f"❌ Error during emergency stop: {e}")

    @staticmethod
    def find_dobot_ports() -> List[str]:
        """Find all potential Dobot USB ports"""
        import glob
        ports = []
        ports.extend(glob.glob('/dev/ttyACM*'))
        ports.extend(glob.glob('/dev/ttyUSB*'))
        return sorted(ports)
