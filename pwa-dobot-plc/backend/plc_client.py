"""
PLC Communication Module using python-snap7
Handles S7 protocol communication with Siemens S7-1200/1500 PLCs
"""

import snap7
from snap7.util import get_bool, get_real, get_int, set_bool, set_real
import time
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class PLCClient:
    """S7 PLC Communication Client"""

    def __init__(self, ip: str = '192.168.0.150', rack: int = 0, slot: int = 1):
        """
        Initialize PLC client

        Args:
            ip: PLC IP address
            rack: PLC rack number (0 for S7-1200)
            slot: PLC slot number (1 for S7-1200)
        """
        self.ip = ip
        self.rack = rack
        self.slot = slot
        self.client = snap7.client.Client()
        self.connected = False
        self.last_error = ""

        # Connection retry settings
        self.max_retries = 3
        self.retry_delay = 1.0
        self.last_connection_attempt = 0
        self.connection_attempt_interval = 5.0

    def connect(self) -> bool:
        """Connect to PLC with retry logic"""
        try:
            current_time = time.time()

            # Don't attempt connection too frequently
            if (current_time - self.last_connection_attempt) < self.connection_attempt_interval:
                return self.connected

            self.last_connection_attempt = current_time

            # Check if already connected
            if self.connected and self.client.get_connected():
                return True

            logger.info(f"Connecting to PLC at {self.ip}, rack {self.rack}, slot {self.slot}")

            # Try to connect with retries
            for attempt in range(self.max_retries):
                try:
                    self.client.connect(self.ip, self.rack, self.slot)

                    if self.client.get_connected():
                        self.connected = True
                        self.last_error = ""
                        logger.info(f"✅ Connected to S7 PLC at {self.ip}")
                        return True

                except Exception as e:
                    self.last_error = f"Connection error: {str(e)}"
                    logger.error(f"{self.last_error} (attempt {attempt + 1}/{self.max_retries})")

                # Wait before retry
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)

            self.connected = False
            return False

        except Exception as e:
            self.last_error = f"Connection error: {str(e)}"
            logger.error(self.last_error)
            self.connected = False
            return False

    def disconnect(self):
        """Disconnect from PLC"""
        try:
            if self.connected:
                self.client.disconnect()
                self.connected = False
                logger.info("Disconnected from PLC")
        except Exception as e:
            logger.error(f"Error disconnecting: {e}")

    def is_connected(self) -> bool:
        """Check if connected to PLC"""
        return self.connected and self.client.get_connected()

    def read_db_real(self, db_number: int, offset: int) -> Optional[float]:
        """Read REAL (float) value from data block"""
        try:
            if not self.is_connected():
                return None

            data = self.client.db_read(db_number, offset, 4)
            return get_real(data, 0)
        except Exception as e:
            self.last_error = f"Error reading DB{db_number}.DBD{offset}: {str(e)}"
            logger.error(self.last_error)
            return None

    def write_db_real(self, db_number: int, offset: int, value: float) -> bool:
        """Write REAL (float) value to data block"""
        try:
            if not self.is_connected():
                return False

            data = bytearray(4)
            set_real(data, 0, value)
            self.client.db_write(db_number, offset, data)
            return True
        except Exception as e:
            self.last_error = f"Error writing DB{db_number}.DBD{offset}: {str(e)}"
            logger.error(self.last_error)
            return False

    def read_db_bool(self, db_number: int, byte_offset: int, bit_offset: int) -> Optional[bool]:
        """Read BOOL value from data block"""
        try:
            if not self.is_connected():
                return None

            data = self.client.db_read(db_number, byte_offset, 1)
            return get_bool(data, 0, bit_offset)
        except Exception as e:
            self.last_error = f"Error reading DB{db_number}.DBX{byte_offset}.{bit_offset}: {str(e)}"
            logger.error(self.last_error)
            return None

    def write_db_bool(self, db_number: int, byte_offset: int, bit_offset: int, value: bool) -> bool:
        """Write BOOL value to data block"""
        try:
            if not self.is_connected():
                return False

            # Read-modify-write for bit operations
            data = bytearray(self.client.db_read(db_number, byte_offset, 1))
            set_bool(data, 0, bit_offset, value)
            self.client.db_write(db_number, byte_offset, data)
            return True
        except Exception as e:
            self.last_error = f"Error writing DB{db_number}.DBX{byte_offset}.{bit_offset}: {str(e)}"
            logger.error(self.last_error)
            return False

    def read_m_bit(self, byte_offset: int, bit_offset: int) -> Optional[bool]:
        """Read Merker (M memory) bit"""
        try:
            if not self.is_connected():
                return None

            data = self.client.mb_read(byte_offset, 1)
            return get_bool(data, 0, bit_offset)
        except Exception as e:
            self.last_error = f"Error reading M{byte_offset}.{bit_offset}: {str(e)}"
            logger.error(self.last_error)
            return None

    def write_m_bit(self, byte_offset: int, bit_offset: int, value: bool) -> bool:
        """Write Merker (M memory) bit"""
        try:
            if not self.is_connected():
                return False

            # Read-modify-write
            data = bytearray(self.client.mb_read(byte_offset, 1))
            set_bool(data, 0, bit_offset, value)
            self.client.mb_write(byte_offset, data)
            return True
        except Exception as e:
            self.last_error = f"Error writing M{byte_offset}.{bit_offset}: {str(e)}"
            logger.error(self.last_error)
            return False

    # High-level methods for Dobot robot control

    def read_target_pose(self, db_number: int = 1) -> Dict[str, float]:
        """Read target X, Y, Z position from PLC (offset 0, 4, 8) in one operation"""
        try:
            if not self.is_connected():
                return {'x': 0.0, 'y': 0.0, 'z': 0.0}

            # Read all 3 REAL values (12 bytes total) in one operation
            data = self.client.db_read(db_number, 0, 12)
            return {
                'x': get_real(data, 0),
                'y': get_real(data, 4),
                'z': get_real(data, 8)
            }
        except Exception as e:
            self.last_error = f"Error reading target pose from DB{db_number}: {str(e)}"
            logger.error(self.last_error)
            return {'x': 0.0, 'y': 0.0, 'z': 0.0}

    def read_current_pose(self, db_number: int = 1) -> Dict[str, float]:
        """Read current X, Y, Z position from PLC (offset 12, 16, 20) in one operation"""
        try:
            if not self.is_connected():
                return {'x': 0.0, 'y': 0.0, 'z': 0.0}

            # Read all 3 REAL values (12 bytes total) in one operation
            data = self.client.db_read(db_number, 12, 12)
            return {
                'x': get_real(data, 0),
                'y': get_real(data, 4),
                'z': get_real(data, 8)
            }
        except Exception as e:
            self.last_error = f"Error reading current pose from DB{db_number}: {str(e)}"
            logger.error(self.last_error)
            return {'x': 0.0, 'y': 0.0, 'z': 0.0}

    def write_current_pose(self, pose: Dict[str, float], db_number: int = 1) -> bool:
        """Write current X, Y, Z position to PLC (offset 12, 16, 20) in one operation"""
        try:
            if not self.is_connected():
                return False

            # Write all 3 REAL values (12 bytes total) in one operation
            data = bytearray(12)
            set_real(data, 0, pose.get('x', 0.0))
            set_real(data, 4, pose.get('y', 0.0))
            set_real(data, 8, pose.get('z', 0.0))
            self.client.db_write(db_number, 12, data)
            return True
        except Exception as e:
            self.last_error = f"Error writing current pose to DB{db_number}: {str(e)}"
            logger.error(self.last_error)
            return False

    def read_control_bits(self) -> Dict[str, bool]:
        """Read all control bits from M0.0 - M0.7 in one operation"""
        try:
            if not self.is_connected():
                return {
                    'start': False, 'stop': False, 'home': False, 'estop': False,
                    'suction': False, 'ready': False, 'busy': False, 'error': False
                }

            # Read entire byte M0 at once (contains all 8 bits)
            data = self.client.mb_read(0, 1)
            byte_value = data[0]

            # Extract individual bits from the byte
            return {
                'start': bool((byte_value >> 0) & 1),
                'stop': bool((byte_value >> 1) & 1),
                'home': bool((byte_value >> 2) & 1),
                'estop': bool((byte_value >> 3) & 1),
                'suction': bool((byte_value >> 4) & 1),
                'ready': bool((byte_value >> 5) & 1),
                'busy': bool((byte_value >> 6) & 1),
                'error': bool((byte_value >> 7) & 1)
            }
        except Exception as e:
            self.last_error = f"Error reading control bits: {str(e)}"
            logger.error(self.last_error)
            return {
                'start': False, 'stop': False, 'home': False, 'estop': False,
                'suction': False, 'ready': False, 'busy': False, 'error': False
            }

    def write_control_bit(self, bit_name: str, value: bool) -> bool:
        """Write a single control bit"""
        bit_map = {
            'start': (0, 0),
            'stop': (0, 1),
            'home': (0, 2),
            'estop': (0, 3),
            'suction': (0, 4),
            'ready': (0, 5),
            'busy': (0, 6),
            'error': (0, 7)
        }

        if bit_name not in bit_map:
            return False

        byte_offset, bit_offset = bit_map[bit_name]
        return self.write_m_bit(byte_offset, bit_offset, value)

    def get_status(self) -> Dict[str, Any]:
        """Get current PLC connection status"""
        return {
            'connected': self.is_connected(),
            'ip': self.ip,
            'rack': self.rack,
            'slot': self.slot,
            'last_error': self.last_error
        }
