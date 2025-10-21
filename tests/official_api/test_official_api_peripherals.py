#!/usr/bin/env python3
"""
Test Official Dobot API - Peripherals Test
Tests suction cup and gripper controls
"""

import sys
import os
import time

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'pwa-dobot-plc', 'backend'))

import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_peripherals():
    """Test suction cup and gripper controls"""
    print("=" * 60)
    print("Official Dobot API - Peripherals Test")
    print("=" * 60)
    print()

    try:
        from dobot_client_official import DobotClient

        # Create and connect
        client = DobotClient(use_usb=True, usb_path="")

        print("Connecting to Dobot...")
        if not client.connect():
            print(f"❌ Connection failed: {client.last_error}")
            return False

        print("✅ Connected")
        print()

        # Test Suction Cup
        print("=" * 60)
        print("Test 1: Suction Cup Control")
        print("=" * 60)

        print("Enabling suction...")
        client.set_suction(True)
        time.sleep(2)
        print("✅ Suction enabled for 2 seconds")

        print("Disabling suction...")
        client.set_suction(False)
        time.sleep(1)
        print("✅ Suction disabled")
        print()

        # Test Gripper
        print("=" * 60)
        print("Test 2: Gripper Control")
        print("=" * 60)

        print("Closing gripper...")
        client.set_gripper(False)  # False = close
        time.sleep(2)
        print("✅ Gripper closed for 2 seconds")

        print("Opening gripper...")
        client.set_gripper(True)  # True = open
        time.sleep(2)
        print("✅ Gripper opened")
        print()

        # Cleanup
        client.disconnect()

        print("=" * 60)
        print("🎉 PERIPHERALS TEST COMPLETED!")
        print("=" * 60)

        return True

    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        return False

    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_peripherals()
    sys.exit(0 if success else 1)
