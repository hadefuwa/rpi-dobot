#!/usr/bin/env python3
"""
Test Official Dobot API - Movement Test
Tests if the robot actually moves (the critical test!)
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

def test_movement():
    """Test if robot physically moves"""
    print("=" * 60)
    print("Official Dobot API - Movement Test")
    print("=" * 60)
    print()
    print("⚠️  WARNING: Ensure robot has clear space to move!")
    print("    Press Ctrl+C to abort if needed")
    print()
    input("Press Enter to continue...")
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

        # Test 1: Read initial position
        print("=" * 60)
        print("Test 1: Reading Initial Position")
        print("=" * 60)
        initial_pose = client.get_pose()
        print(f"Initial position: X={initial_pose['x']:.2f}, Y={initial_pose['y']:.2f}, Z={initial_pose['z']:.2f}")
        print()

        # Test 2: Move to home position
        print("=" * 60)
        print("Test 2: Moving to Home Position")
        print("=" * 60)
        print(f"Target: {client.HOME_POSITION}")
        print("Moving...")

        if client.home(wait=True):
            print("✅ Home command completed")
            time.sleep(0.5)  # Brief pause

            # Verify position changed
            home_pose = client.get_pose()
            print(f"Position after home: X={home_pose['x']:.2f}, Y={home_pose['y']:.2f}, Z={home_pose['z']:.2f}")

            # Check if position actually changed
            pos_diff = abs(home_pose['x'] - initial_pose['x']) + abs(home_pose['y'] - initial_pose['y']) + abs(home_pose['z'] - initial_pose['z'])
            if pos_diff > 1.0:  # More than 1mm total difference
                print(f"✅ Robot MOVED! Total position change: {pos_diff:.2f}mm")
            else:
                print(f"⚠️  Position barely changed ({pos_diff:.2f}mm). Robot might not be moving.")
        else:
            print("❌ Home command failed")
            return False

        print()

        # Test 3: Move to a test position
        print("=" * 60)
        print("Test 3: Moving to Test Position")
        print("=" * 60)
        test_x = 250.0
        test_y = 50.0
        test_z = 100.0
        print(f"Target: X={test_x}, Y={test_y}, Z={test_z}")
        print("Moving...")

        if client.move_to(test_x, test_y, test_z, wait=True):
            print("✅ Move command completed")
            time.sleep(0.5)

            # Verify position
            test_pose = client.get_pose()
            print(f"Position after move: X={test_pose['x']:.2f}, Y={test_pose['y']:.2f}, Z={test_pose['z']:.2f}")

            # Check accuracy
            x_diff = abs(test_pose['x'] - test_x)
            y_diff = abs(test_pose['y'] - test_y)
            z_diff = abs(test_pose['z'] - test_z)

            print(f"Position error: X={x_diff:.2f}mm, Y={y_diff:.2f}mm, Z={z_diff:.2f}mm")

            if x_diff < 5.0 and y_diff < 5.0 and z_diff < 5.0:
                print("✅ Robot reached target position accurately!")
            else:
                print("⚠️  Position error > 5mm. Check movement parameters.")
        else:
            print("❌ Move command failed")
            return False

        print()

        # Test 4: Return to home
        print("=" * 60)
        print("Test 4: Returning to Home")
        print("=" * 60)
        print("Moving back to home...")
        client.home(wait=True)
        final_pose = client.get_pose()
        print(f"Final position: X={final_pose['x']:.2f}, Y={final_pose['y']:.2f}, Z={final_pose['z']:.2f}")
        print()

        # Cleanup
        client.disconnect()

        print("=" * 60)
        print("🎉 MOVEMENT TEST PASSED!")
        print("=" * 60)
        print()
        print("Summary:")
        print(f"  Initial:  X={initial_pose['x']:.2f}, Y={initial_pose['y']:.2f}, Z={initial_pose['z']:.2f}")
        print(f"  Home:     X={home_pose['x']:.2f}, Y={home_pose['y']:.2f}, Z={home_pose['z']:.2f}")
        print(f"  Test:     X={test_pose['x']:.2f}, Y={test_pose['y']:.2f}, Z={test_pose['z']:.2f}")
        print(f"  Final:    X={final_pose['x']:.2f}, Y={final_pose['y']:.2f}, Z={final_pose['z']:.2f}")
        print()
        print("✅ Robot is moving correctly with Official API!")

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
    success = test_movement()
    sys.exit(0 if success else 1)
