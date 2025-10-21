"""
Dobot Robot Communication Client
Handles USB/Serial communication with Dobot Magician robot
"""

import logging
from typing import Dict, Optional

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
            usb_path: USB device path for Dobot
        """
        self.use_usb = use_usb
        self.usb_path = usb_path
        self.connected = False
        self.last_error = ""
        self.device = None

    def connect(self) -> bool:
        """Connect to Dobot robot"""
        if not self.use_usb or not DOBOT_AVAILABLE:
            logger.info("Dobot connection skipped (USB disabled or library not available)")
            return False

        try:
            logger.info(f"Connecting to Dobot on {self.usb_path}")
            self.device = PyDobot(port=self.usb_path, verbose=False)
            self.connected = True
            logger.info("✅ Connected to Dobot")
            return True
        except Exception as e:
            self.last_error = f"Connection error: {str(e)}"
            logger.error(f"Failed to connect to Dobot: {e}")
            self.connected = False
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

    def move_to(self, x: float, y: float, z: float, r: float = 0, wait: bool = False) -> bool:
        """
        Move robot to position

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
            return False

        try:
            self.device.move_to(x, y, z, r, wait=wait)
            logger.info(f"Move command {'completed' if wait else 'queued'}: ({x}, {y}, {z}, {r})")
            return True
        except Exception as e:
            self.last_error = f"Error moving: {str(e)}"
            logger.error(self.last_error)
            return False

    def home(self, wait: bool = True) -> bool:
        """
        Move robot to home position

        Args:
            wait: Wait for movement to complete before returning

        Returns:
            True if command sent successfully, False otherwise
        """
        if not self.connected or not self.device:
            self.last_error = "Dobot not connected"
            return False

        try:
            logger.info(f"Moving to home position: {self.HOME_POSITION}")
            self.device.move_to(
                self.HOME_POSITION['x'],
                self.HOME_POSITION['y'],
                self.HOME_POSITION['z'],
                self.HOME_POSITION['r'],
                wait=wait
            )
            logger.info(f"Home command {'completed' if wait else 'queued'}")
            return True
        except Exception as e:
            self.last_error = f"Error homing: {str(e)}"
            logger.error(self.last_error)
            return False

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
            logger.info(f"Suction cup {'enabled' if enable else 'disabled'}")
        except Exception as e:
            logger.error(f"Error setting suction: {e}")
