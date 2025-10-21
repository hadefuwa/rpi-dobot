#!/usr/bin/env python3
"""
Test if Dobot needs to be HOMED before it can move properly
"""

import sys
import time
from pydobot import Dobot

def test_dobot_homing(port='/dev/ttyACM0'):
    """Test Dobot homing sequence"""
    
    print("\n" + "="*60)
    print("🏠 DOBOT HOMING TEST")
    print("="*60)
    print("\nHypothesis: Robot must be HOMED before it can move")
    print("(Homing means moving to physical limit switches to")
    print(" establish the zero position coordinate system)")
    
    # Connect
    print(f"\n1️⃣ Connecting to Dobot on {port}...")
    try:
        device = Dobot(port=port, verbose=True)
        print("✅ Connected!")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False
    
    time.sleep(1)
    
    # Get current position BEFORE homing
    print("\n2️⃣ Current position BEFORE homing...")
    (x1, y1, z1, r1, j1, j2, j3, j4) = device.pose()
    print(f"   X: {x1:.2f} mm")
    print(f"   Y: {y1:.2f} mm")
    print(f"   Z: {z1:.2f} mm")
    print(f"   R: {r1:.2f}°")
    print(f"   Joints: J1={j1:.2f}° J2={j2:.2f}° J3={j3:.2f}° J4={j4:.2f}°")
    
    time.sleep(1)
    
    # Check if device has a 'home' method
    print("\n3️⃣ Checking for HOME command...")
    if hasattr(device, 'home'):
        print("   ✅ Device has .home() method!")
        print("\n4️⃣ Executing HOME sequence...")
        print("   ⚠️  WARNING: Robot will move to find limit switches!")
        print("   Make sure workspace is clear!")
        time.sleep(2)
        
        try:
            device.home()
            print("   ✅ Homing command sent!")
            print("   ⏳ Waiting 10 seconds for homing to complete...")
            time.sleep(10)
        except Exception as e:
            print(f"   ❌ Homing failed: {e}")
            device.close()
            return False
    else:
        print("   ❌ Device has NO .home() method")
        print("   Will try alternative homing approach...")
        
        # Alternative: Some robots home by reading joint positions
        # or by sending specific commands
        print("\n   Checking device methods...")
        methods = [m for m in dir(device) if not m.startswith('_')]
        print(f"   Available methods: {', '.join(methods)}")
    
    # Get position AFTER homing
    print("\n5️⃣ Position AFTER homing...")
    (x2, y2, z2, r2, j1, j2, j3, j4) = device.pose()
    print(f"   X: {x2:.2f} mm")
    print(f"   Y: {y2:.2f} mm")
    print(f"   Z: {z2:.2f} mm")
    print(f"   R: {r2:.2f}°")
    print(f"   Joints: J1={j1:.2f}° J2={j2:.2f}° J3={j3:.2f}° J4={j4:.2f}°")
    
    # Check if position changed significantly
    dist = ((x2-x1)**2 + (y2-y1)**2 + (z2-z1)**2)**0.5
    if dist > 10:
        print(f"\n   ✅ Position changed by {dist:.1f}mm - homing worked!")
    else:
        print(f"\n   ⚠️ Position barely changed ({dist:.1f}mm)")
    
    time.sleep(2)
    
    # NOW try to move
    print("\n6️⃣ Testing movement AFTER homing...")
    print("   Setting speed...")
    device.speed(100, 100)
    
    print(f"   Moving +50mm in X direction...")
    device.move_to(x2 + 50, y2, z2, r2, wait=True)
    time.sleep(3)
    
    (x3, y3, z3, r3, j1, j2, j3, j4) = device.pose()
    print(f"   New position: X={x3:.2f}, Y={y3:.2f}, Z={z3:.2f}")
    
    moved = abs(x3 - x2)
    print(f"   Actual X movement: {moved:.2f}mm (expected: 50mm)")
    
    if moved > 40:
        print("\n" + "="*60)
        print("🎉 SUCCESS! Homing fixed the movement issue!")
        print("="*60)
        result = True
    else:
        print("\n" + "="*60)
        print(f"❌ Still not moving correctly (only moved {moved:.2f}mm)")
        print("="*60)
        result = False
    
    # Close
    device.close()
    return result


if __name__ == "__main__":
    port = sys.argv[1] if len(sys.argv) > 1 else '/dev/ttyACM0'
    
    print(f"\nUsing port: {port}")
    print("(To use different port: python test_dobot_home.py /dev/ttyACM0)")
    
    success = test_dobot_homing(port)
    
    if success:
        print("\n✅ Solution: Robot must be HOMED before moving!")
        print("We'll add automatic homing to dobot_client.py")
    else:
        print("\n❌ Homing didn't fix it - different issue")
    
    sys.exit(0 if success else 1)

