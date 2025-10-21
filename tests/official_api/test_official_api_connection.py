#!/usr/bin/env python3
"""
Test Official Dobot API - Connection Test
Tests basic connection and initialization
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'pwa-dobot-plc', 'backend'))

import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_connection():
    """Test basic connection to Dobot"""
    print("=" * 60)
    print("Official Dobot API - Connection Test")
    print("=" * 60)
    print()

    try:
        # Import the official API client
        from dobot_client_official import DobotClient

        print("✅ Successfully imported DobotClient")
        print()

        # Create client (auto-detect port)
        print("Creating Dobot client...")
        client = DobotClient(use_usb=True, usb_path="")
        print("✅ Client created")
        print()

        # Connect
        print("Connecting to Dobot...")
        if client.connect():
            print("✅ CONNECTION SUCCESSFUL!")
            print(f"   Port: {client.actual_port}")
            print()

            # Get initial position
            print("Reading current position...")
            pose = client.get_pose()
            print(f"✅ Current position:")
            print(f"   X: {pose['x']:.2f} mm")
            print(f"   Y: {pose['y']:.2f} mm")
            print(f"   Z: {pose['z']:.2f} mm")
            print(f"   R: {pose['r']:.2f} degrees")
            print()

            # Disconnect
            print("Disconnecting...")
            client.disconnect()
            print("✅ Disconnected cleanly")
            print()

            print("=" * 60)
            print("🎉 CONNECTION TEST PASSED!")
            print("=" * 60)
            return True

        else:
            print(f"❌ CONNECTION FAILED: {client.last_error}")
            print()
            print("Troubleshooting:")
            print("1. Check USB cable is connected")
            print("2. Check Dobot is powered on")
            print("3. Check user has permission to access USB (add to dialout group)")
            print("   sudo usermod -a -G dialout $USER")
            print("4. Try: ls -la /dev/ttyACM* /dev/ttyUSB*")
            return False

    except ImportError as e:
        print(f"❌ IMPORT ERROR: {e}")
        print()
        print("Please run: bash setup_official_dobot_api.sh")
        return False

    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
