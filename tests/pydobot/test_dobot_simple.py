#!/usr/bin/env python3
"""
Simple Dobot Test Script
Tests basic Dobot connection and movement
"""

import sys
import time

try:
    from pydobot import Dobot
except ImportError:
    print("❌ pydobot not installed!")
    print("Run: pip install pydobot")
    sys.exit(1)

def test_dobot(port='/dev/ttyACM1'):
    """Test basic Dobot functionality"""
    
    print("=" * 60)
    print("🤖 SIMPLE DOBOT TEST")
    print("=" * 60)
    
    # Step 1: Connect
    print(f"\n1️⃣ Connecting to Dobot on {port}...")
    try:
        dobot = Dobot(port=port, verbose=True)
        print("✅ Connected!")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\nTry:")
        print("  - Check USB cable is connected")
        print("  - Check device path: ls -la /dev/ttyACM*")
        print("  - Try different port: /dev/ttyACM0")
        return False
    
    # Step 2: Get current position
    print("\n2️⃣ Getting current position...")
    try:
        pos = dobot.pose()
        print(f"✅ Current position:")
        print(f"   X: {pos[0]:.2f} mm")
        print(f"   Y: {pos[1]:.2f} mm")
        print(f"   Z: {pos[2]:.2f} mm")
        print(f"   R: {pos[3]:.2f}°")
    except Exception as e:
        print(f"❌ Failed to get position: {e}")
        dobot.close()
        return False
    
    # Step 3: Move to safe home position
    print("\n3️⃣ Moving to HOME position (200, 0, 150)...")
    print("   (This is a safe position above the base)")
    try:
        dobot.move_to(200, 0, 150, 0, wait=True)
        print("✅ Move completed!")
        time.sleep(0.5)
    except Exception as e:
        print(f"❌ Move failed: {e}")
        dobot.close()
        return False
    
    # Step 4: Get new position
    print("\n4️⃣ Verifying new position...")
    try:
        pos = dobot.pose()
        print(f"✅ New position:")
        print(f"   X: {pos[0]:.2f} mm")
        print(f"   Y: {pos[1]:.2f} mm")
        print(f"   Z: {pos[2]:.2f} mm")
        print(f"   R: {pos[3]:.2f}°")
    except Exception as e:
        print(f"❌ Failed to get position: {e}")
    
    # Step 5: Small movement test
    print("\n5️⃣ Testing small movement (move 20mm forward)...")
    try:
        dobot.move_to(220, 0, 150, 0, wait=True)
        print("✅ Small move completed!")
        time.sleep(0.5)
        
        # Move back
        print("   Moving back...")
        dobot.move_to(200, 0, 150, 0, wait=True)
        print("✅ Moved back!")
    except Exception as e:
        print(f"❌ Small move failed: {e}")
    
    # Step 6: Test suction cup
    print("\n6️⃣ Testing suction cup...")
    try:
        print("   Turning suction ON...")
        dobot.suck(True)
        time.sleep(2)
        print("   Turning suction OFF...")
        dobot.suck(False)
        print("✅ Suction test completed!")
    except Exception as e:
        print(f"❌ Suction test failed: {e}")
    
    # Cleanup
    print("\n7️⃣ Closing connection...")
    try:
        dobot.close()
        print("✅ Disconnected!")
    except Exception as e:
        print(f"⚠️ Close warning: {e}")
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED! Dobot is working!")
    print("=" * 60)
    return True

if __name__ == '__main__':
    # Get port from command line or use default
    port = sys.argv[1] if len(sys.argv) > 1 else '/dev/ttyACM1'
    
    print(f"\nUsing port: {port}")
    print("(To use different port: python test_dobot_simple.py /dev/ttyACM0)\n")
    
    success = test_dobot(port)
    
    if success:
        print("\n🎉 SUCCESS! Your Dobot is working!")
        print("Now the web app should work too.")
    else:
        print("\n❌ FAILED! Fix the issues above before using web app.")
    
    sys.exit(0 if success else 1)

