"""
Dobot Robot Communication Client - Official API Version
Uses the official Dobot DLL API instead of pydobot
"""

import logging
import time
import sys
import os
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)

# Add DobotAPI to Python path
dobot_api_path = os.path.join(os.path.dirname(__file__), '..', '..', 'lib', 'DobotAPI')
dobot_api_path = os.path.abspath(dobot_api_path)
if os.path.exists(dobot_api_path) and dobot_api_path not in sys.path:
    sys.path.insert(0, dobot_api_path)
    logger.info(f"Added DobotAPI to path: {dobot_api_path}")

# Try to import official Dobot API
try:
    import DobotDLLType as dType
    DOBOT_AVAILABLE = True
    logger.info("✅ Official Dobot API loaded successfully")
except ImportError as e:
    DOBOT_AVAILABLE = False
    logger.warning(f"DobotDLLType not found - Dobot functionality disabled: {e}")
    logger.warning(f"Searched in: {dobot_api_path}")

class DobotClient:
    """Dobot Robot Communication Client using Official API"""

    # Default home position for Dobot Magician
    HOME_POSITION = {
        'x': 200.0,
        'y': 0.0,
        'z': 150.0,
        'r': 0.0
    }

    # Default movement parameters (can be adjusted via settings)
    DEFAULT_VELOCITY_RATIO = 100  # 1-100%
    DEFAULT_ACCELERATION_RATIO = 100  # 1-100%

    def __init__(self, use_usb: bool = True, usb_path: str = '/dev/ttyACM0'):
        """
        Initialize Dobot client with official API

        Args:
            use_usb: Use USB connection (True) or skip Dobot entirely (False)
            usb_path: USB device path for Dobot (empty string for auto-detect)
        """
        self.use_usb = use_usb
        self.usb_path = usb_path if usb_path else ""  # Empty string for auto-detect
        self.connected = False
        self.last_error = ""
        self.api = None
        self.last_index = 0
        self.actual_port = None

        # Movement parameters
        self.velocity_ratio = self.DEFAULT_VELOCITY_RATIO
        self.acceleration_ratio = self.DEFAULT_ACCELERATION_RATIO

    def connect(self) -> bool:
        """Connect to Dobot robot using official API"""
        if not self.use_usb or not DOBOT_AVAILABLE:
            logger.info("Dobot connection skipped (USB disabled or DLL not available)")
            return False

        try:
            logger.info("Loading Dobot DLL...")
            # Load the DLL library
            self.api = dType.load()
            logger.info("✅ DLL loaded successfully")

            # Connect to Dobot
            # Empty string or specific port - API will auto-detect if empty
            logger.info(f"Connecting to Dobot on {self.usb_path or 'auto-detect'}...")
            state = dType.ConnectDobot(self.api, self.usb_path, 115200)[0]

            if state == dType.DobotConnect.DobotConnect_NoError:
                self.connected = True
                self.actual_port = self.usb_path if self.usb_path else "auto-detected"

                logger.info(f"✅ Connected to Dobot on {self.actual_port}")

                # CRITICAL: Initialize robot parameters before any movement
                self._initialize_robot()

                logger.info("✅ Dobot initialized and ready")
                return True
            else:
                self.last_error = f"Connection failed with error code: {state}"
                logger.error(f"❌ {self.last_error}")
                return False

        except Exception as e:
            self.last_error = f"Connection error: {str(e)}"
            logger.error(f"❌ {self.last_error}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    def _initialize_robot(self):
        """Initialize robot parameters - MUST be called after connection"""
        if not self.api:
            return

        try:
            # Set PTP (Point-to-Point) movement parameters
            # These are REQUIRED for movement to work
            dType.SetPTPCommonParams(
                self.api,
                velocityRatio=self.velocity_ratio,
                accelerationRatio=self.acceleration_ratio,
                isQueued=1
            )
            logger.info(f"✅ Set PTP params: velocity={self.velocity_ratio}%, accel={self.acceleration_ratio}%")

            # Set PTP coordinate parameters (for different movement modes)
            dType.SetPTPCoordinateParams(
                self.api,
                xyzVelocity=200,      # mm/s
                rVelocity=200,        # degrees/s
                xyzAcceleration=200,  # mm/s²
                rAcceleration=200,    # degrees/s²
                isQueued=1
            )
            logger.info("✅ Set PTP coordinate params")

            # Set home position parameters
            dType.SetHOMEParams(
                self.api,
                x=self.HOME_POSITION['x'],
                y=self.HOME_POSITION['y'],
                z=self.HOME_POSITION['z'],
                r=self.HOME_POSITION['r'],
                isQueued=1
            )
            logger.info(f"✅ Set home position: {self.HOME_POSITION}")

            # Clear any existing queued commands
            dType.SetQueuedCmdClear(self.api)
            logger.info("✅ Cleared command queue")

            # Enable the device
            dType.SetDeviceSN(self.api, "1234567890")  # Doesn't matter for single device

        except Exception as e:
            logger.error(f"❌ Error initializing robot: {e}")
            import traceback
            logger.error(traceback.format_exc())

    def disconnect(self):
        """Disconnect from Dobot"""
        if self.connected and self.api:
            try:
                dType.DisconnectDobot(self.api)
                self.connected = False
                self.api = None
                logger.info("✅ Disconnected from Dobot")
            except Exception as e:
                logger.error(f"❌ Error disconnecting from Dobot: {e}")

    def get_pose(self) -> Dict[str, float]:
        """Get current robot position"""
        if not self.connected or not self.api:
            return {'x': 0.0, 'y': 0.0, 'z': 0.0, 'r': 0.0}

        try:
            # GetPose returns: (x, y, z, r, joint1, joint2, joint3, joint4)
            pose = dType.GetPose(self.api)
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
        Move robot to position using official API

        Args:
            x: X coordinate in mm
            y: Y coordinate in mm
            z: Z coordinate in mm
            r: Rotation in degrees
            wait: Wait for movement to complete before returning

        Returns:
            True if command sent successfully, False otherwise
        """
        if not self.connected or not self.api:
            self.last_error = "Dobot not connected"
            logger.error("❌ Dobot not connected")
            return False

        try:
            logger.info(f"🤖 Executing move_to({x}, {y}, {z}, {r}, wait={wait})")

            # Queue the movement command
            # PTPMode.PTPMOVLXYZMode = Linear movement in XYZ space
            result = dType.SetPTPCmd(
                self.api,
                dType.PTPMode.PTPMOVLXYZMode,  # Linear movement mode
                x, y, z, r,
                isQueued=1
            )
            self.last_index = result[0]

            logger.info(f"✅ Move command queued with index: {self.last_index}")

            # Start executing the queued commands
            dType.SetQueuedCmdStartExec(self.api)
            logger.info("✅ Command execution started")

            # Wait for completion if requested
            if wait:
                logger.info(f"⏳ Waiting for movement to complete (index {self.last_index})...")
                timeout = 30  # 30 second timeout
                start_time = time.time()

                while True:
                    current_index = dType.GetQueuedCmdCurrentIndex(self.api)[0]

                    if current_index >= self.last_index:
                        logger.info(f"✅ Movement completed (current index: {current_index})")
                        break

                    if time.time() - start_time > timeout:
                        logger.warning(f"⚠️ Movement timeout after {timeout}s")
                        break

                    dType.dSleep(50)  # Sleep 50ms between checks

                # Verify we reached the target
                final_pose = self.get_pose()
                logger.info(f"📍 Final position: X={final_pose['x']:.2f}, Y={final_pose['y']:.2f}, Z={final_pose['z']:.2f}")

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
        logger.info(f"🏠 Homing robot to {self.HOME_POSITION}")
        return self.move_to(
            self.HOME_POSITION['x'],
            self.HOME_POSITION['y'],
            self.HOME_POSITION['z'],
            self.HOME_POSITION['r'],
            wait=wait
        )

    def start_queue(self):
        """Start executing the command queue"""
        if not self.connected or not self.api:
            return

        try:
            dType.SetQueuedCmdStartExec(self.api)
            logger.info("✅ Command queue started")
        except Exception as e:
            logger.error(f"❌ Error starting queue: {e}")

    def stop_queue(self):
        """Stop executing the command queue"""
        if not self.connected or not self.api:
            return

        try:
            dType.SetQueuedCmdStopExec(self.api)
            logger.info("✅ Command queue stopped")
        except Exception as e:
            logger.error(f"❌ Error stopping queue: {e}")

    def clear_queue(self):
        """Clear command queue"""
        if not self.connected or not self.api:
            return

        try:
            dType.SetQueuedCmdClear(self.api)
            logger.info("✅ Command queue cleared")
        except Exception as e:
            logger.error(f"❌ Error clearing queue: {e}")

    def set_suction(self, enable: bool):
        """Enable/disable suction cup"""
        if not self.connected or not self.api:
            return

        try:
            # SetEndEffectorSuctionCup(api, enableCtrl, suck, isQueued)
            # enableCtrl=1 to enable control, suck=1 to suck, suck=0 to release
            dType.SetEndEffectorSuctionCup(
                self.api,
                enableCtrl=1,
                suck=1 if enable else 0,
                isQueued=1
            )
            dType.SetQueuedCmdStartExec(self.api)
            logger.info(f"💨 Suction cup {'enabled' if enable else 'disabled'}")
        except Exception as e:
            logger.error(f"❌ Error setting suction: {e}")

    def set_gripper(self, open_gripper: bool):
        """
        Control gripper (open/close)

        Args:
            open_gripper: True to open, False to close
        """
        if not self.connected or not self.api:
            logger.error("❌ Dobot not connected")
            return

        try:
            # SetEndEffectorGripper(api, enableCtrl, grip, isQueued)
            # enableCtrl=1 to enable control, grip=1 to grip (close), grip=0 to release (open)
            dType.SetEndEffectorGripper(
                self.api,
                enableCtrl=1,
                grip=0 if open_gripper else 1,  # Inverted: open=0, close=1
                isQueued=1
            )
            dType.SetQueuedCmdStartExec(self.api)
            logger.info(f"✋ Gripper {'opened' if open_gripper else 'closed'}")
        except Exception as e:
            logger.error(f"❌ Error controlling gripper: {e}")

    def set_speed(self, velocity_ratio: int, acceleration_ratio: int):
        """
        Set movement speed parameters

        Args:
            velocity_ratio: Velocity ratio 1-100%
            acceleration_ratio: Acceleration ratio 1-100%
        """
        if not self.connected or not self.api:
            return

        try:
            self.velocity_ratio = max(1, min(100, velocity_ratio))
            self.acceleration_ratio = max(1, min(100, acceleration_ratio))

            dType.SetPTPCommonParams(
                self.api,
                velocityRatio=self.velocity_ratio,
                accelerationRatio=self.acceleration_ratio,
                isQueued=1
            )
            logger.info(f"✅ Speed set: velocity={self.velocity_ratio}%, accel={self.acceleration_ratio}%")
        except Exception as e:
            logger.error(f"❌ Error setting speed: {e}")

    def emergency_stop(self):
        """Emergency stop - clears queue and stops execution"""
        if not self.connected or not self.api:
            return

        try:
            dType.SetQueuedCmdStopExec(self.api)
            dType.SetQueuedCmdClear(self.api)
            logger.warning("🛑 EMERGENCY STOP executed")
        except Exception as e:
            logger.error(f"❌ Error during emergency stop: {e}")

    @staticmethod
    def find_dobot_ports() -> List[str]:
        """Find all potential Dobot USB ports (for compatibility)"""
        import glob
        ports = []
        ports.extend(glob.glob('/dev/ttyACM*'))
        ports.extend(glob.glob('/dev/ttyUSB*'))
        return sorted(ports)
