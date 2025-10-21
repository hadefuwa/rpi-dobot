#!/usr/bin/env python3
"""
Test script to diagnose Dobot movement issues
Specifically tests speed/acceleration settings
"""

import sys
import time
from pydobot import Dobot

def test_dobot_speed(port='/dev/ttyACM0'):
    """Test Dobot with different speed settings"""
    
    print("\n" + "="*60)
    print("🔧 DOBOT SPEED DIAGNOSTIC TEST")
    print("="*60)
    
    # Connect
    print(f"\n1️⃣ Connecting to Dobot on {port}...")
    try:
        device = Dobot(port=port, verbose=True)
        print("✅ Connected!")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False
    
    time.sleep(1)
    
    # Get current position
    print("\n2️⃣ Getting current position...")
    (x, y, z, r, j1, j2, j3, j4) = device.pose()
    print(f"✅ Current position:")
    print(f"   X: {x:.2f} mm")
    print(f"   Y: {y:.2f} mm")
    print(f"   Z: {z:.2f} mm")
    print(f"   R: {r:.2f}°")
    
    time.sleep(1)
    
    # TEST 1: Try moving WITHOUT setting speed (current behavior)
    print("\n3️⃣ TEST 1: Moving WITHOUT setting speed...")
    print("   (This is what's currently failing)")
    device.move_to(x + 10, y, z, r, wait=True)
    time.sleep(2)
    (x2, y2, z2, r2, j1, j2, j3, j4) = device.pose()
    print(f"   New position: X={x2:.2f}, Y={y2:.2f}, Z={z2:.2f}")
    if abs(x2 - (x + 10)) < 1:
        print("   ❌ Robot did NOT move (as expected)")
    else:
        print("   ✅ Robot moved!")
    
    time.sleep(1)
    
    # TEST 2: Set speed and try again
    print("\n4️⃣ TEST 2: Setting speed to 100mm/s, acceleration 100mm/s²...")
    device.speed(velocity=100, acceleration=100)
    print("   ✅ Speed parameters set!")
    
    time.sleep(1)
    
    print("\n5️⃣ TEST 2: Moving WITH speed settings...")
    device.move_to(x + 20, y, z, r, wait=True)
    print("   ⏳ Waiting for movement to complete...")
    time.sleep(3)
    
    (x3, y3, z3, r3, j1, j2, j3, j4) = device.pose()
    print(f"   New position: X={x3:.2f}, Y={y3:.2f}, Z={z3:.2f}")
    
    if abs(x3 - (x + 20)) < 5:
        print("   ✅ SUCCESS! Robot moved to target!")
        print("\n" + "="*60)
        print("🎉 FIX CONFIRMED: Need to call .speed() before moving!")
        print("="*60)
        result = True
    else:
        print("   ❌ Robot still didn't move correctly")
        print("\n" + "="*60)
        print("⚠️ Speed setting didn't fix it - different issue")
        print("="*60)
        result = False
    
    # Move back to original position
    print("\n6️⃣ Moving back to original position...")
    device.move_to(x, y, z, r, wait=True)
    time.sleep(2)
    
    # Disconnect
    device.close()
    print("\n✅ Test complete!")
    
    return result


if __name__ == "__main__":
    # Get port from command line or use default
    port = sys.argv[1] if len(sys.argv) > 1 else '/dev/ttyACM0'
    
    print(f"\nUsing port: {port}")
    print("(To use different port: python test_dobot_speed.py /dev/ttyACM0)")
    
    success = test_dobot_speed(port)
    
    if success:
        print("\n" + "="*60)
        print("✅ SOLUTION FOUND!")
        print("="*60)
        print("\nThe fix is to add this line after connecting:")
        print("   device.speed(100, 100)")
        print("\nWe'll update dobot_client.py to do this automatically.")
        sys.exit(0)
    else:
        print("\n" + "="*60)
        print("❌ Issue still not resolved - need further investigation")
        print("="*60)
        sys.exit(1)

