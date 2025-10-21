"""
Dobot Robot Communication Client
Handles USB/Serial communication with Dobot Magician robot
"""

import logging
import glob
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)

# Try to import pydobot, but make it optional
try:
    from pydobot import Dobot as PyDobot
    DOBOT_AVAILABLE = True
except ImportError:
    DOBOT_AVAILABLE = False
    logger.warning("pydobot not installed - Dobot functionality disabled")

class DobotClient:
    """Dobot Robot Communication Client"""

    # Default home position for Dobot Magician
    HOME_POSITION = {
        'x': 200.0,
        'y': 0.0,
        'z': 150.0,
        'r': 0.0
    }

    def __init__(self, use_usb: bool = True, usb_path: str = '/dev/ttyACM0'):
        """
        Initialize Dobot client

        Args:
            use_usb: Use USB connection (True) or skip Dobot entirely (False)
            usb_path: USB device path for Dobot (will auto-detect if not found)
        """
        self.use_usb = use_usb
        self.usb_path = usb_path
        self.connected = False
        self.last_error = ""
        self.device = None
        self.actual_port = None  # Store the actual port that worked

    @staticmethod
    def find_dobot_ports() -> List[str]:
        """Find all potential Dobot USB ports"""
        ports = []
        
        # Check ttyACM devices (most common for Dobot)
        ports.extend(glob.glob('/dev/ttyACM*'))
        
        # Check ttyUSB devices (fallback)
        ports.extend(glob.glob('/dev/ttyUSB*'))
        
        return sorted(ports)

    def connect(self) -> bool:
        """Connect to Dobot robot with automatic port detection"""
        if not self.use_usb or not DOBOT_AVAILABLE:
            logger.info("Dobot connection skipped (USB disabled or library not available)")
            return False

        # Try configured port first
        if self._try_connect(self.usb_path):
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
                return True
        
        self.last_error = f"Dobot not found on any USB port: {', '.join(available_ports)}"
        logger.error(f"❌ {self.last_error}")
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

    def disconnect(self):
        """Disconnect from Dobot"""
        if self.connected and self.device:
            try:
                self.device.close()
                self.connected = False
                logger.info("Disconnected from Dobot")
            except Exception as e:
                logger.error(f"Error disconnecting from Dobot: {e}")

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
        Move robot to position

        Args:
            x: X coordinate in mm
            y: Y coordinate in mm
            z: Z coordinate in mm
            r: Rotation in degrees
            wait: Wait for movement to complete before returning (default True for reliable execution)

        Returns:
            True if command sent successfully, False otherwise
        """
        if not self.connected or not self.device:
            self.last_error = "Dobot not connected"
            logger.error("❌ Dobot not connected")
            return False

        try:
            logger.info(f"🤖 Executing move_to({x}, {y}, {z}, {r}, wait={wait})")
            self.device.move_to(x, y, z, r, wait=wait)
            logger.info(f"✅ Move command {'completed' if wait else 'queued'}: ({x}, {y}, {z}, {r})")
            return True
        except Exception as e:
            self.last_error = f"Error moving: {str(e)}"
            logger.error(f"❌ Move error: {self.last_error}")
            return False

    def home(self, wait: bool = True) -> bool:
        """
        Move robot to home position

        Args:
            wait: Wait for movement to complete before returning (default True for reliable execution)

        Returns:
            True if command sent successfully, False otherwise
        """
        if not self.connected or not self.device:
            self.last_error = "Dobot not connected"
            logger.error("❌ Dobot not connected")
            return False

        try:
            logger.info(f"🏠 Moving to home position: {self.HOME_POSITION}")
            self.device.move_to(
                self.HOME_POSITION['x'],
                self.HOME_POSITION['y'],
                self.HOME_POSITION['z'],
                self.HOME_POSITION['r'],
                wait=wait
            )
            logger.info(f"✅ Home command {'completed' if wait else 'queued'}")
            return True
        except Exception as e:
            self.last_error = f"Error homing: {str(e)}"
            logger.error(f"❌ Home error: {self.last_error}")
            return False

    def start_queue(self):
        """Start executing the command queue"""
        if not self.connected or not self.device:
            return
        
        try:
            # Try to start the queue if the method exists
            if hasattr(self.device, 'start_queue'):
                self.device.start_queue()
                logger.info("✅ Command queue started")
            else:
                logger.warning("⚠️ start_queue method not available - pydobot may auto-execute commands")
        except Exception as e:
            logger.error(f"❌ Error starting queue: {e}")

    def stop_queue(self):
        """Stop executing the command queue"""
        if not self.connected or not self.device:
            return
        
        try:
            # Try to stop the queue if the method exists
            if hasattr(self.device, 'stop_queue'):
                self.device.stop_queue()
                logger.info("Command queue stopped")
            else:
                logger.warning("⚠️ stop_queue method not available - using clear_queue instead")
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
