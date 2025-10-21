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

    def move_to(self, x: float, y: float, z: float, r: float = 0) -> Optional[int]:
        """Move robot to position"""
        if not self.connected or not self.device:
            return None

        try:
            queued_index = self.device.move_to(x, y, z, r, wait=False)
            logger.info(f"Move command queued: ({x}, {y}, {z}, {r}) - index {queued_index}")
            return queued_index
        except Exception as e:
            self.last_error = f"Error moving: {str(e)}"
            logger.error(self.last_error)
            return None

    def home(self) -> Optional[int]:
        """Home the robot"""
        if not self.connected or not self.device:
            return None

        try:
            queued_index = self.device.home()
            logger.info(f"Home command queued - index {queued_index}")
            return queued_index
        except Exception as e:
            self.last_error = f"Error homing: {str(e)}"
            logger.error(self.last_error)
            return None

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
