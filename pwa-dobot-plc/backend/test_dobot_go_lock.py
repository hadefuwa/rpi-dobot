#!/usr/bin/env python3
"""
Test pydobot's mysterious .go() and .lock() methods
These might be the missing initialization!
"""

import sys
import time
from pydobot import Dobot

def test_go_and_lock(port='/dev/ttyACM0'):
    """Test if .go() or .lock() enables movement"""
    
    print("\n" + "="*60)
    print("🔓 DOBOT GO/LOCK TEST")
    print("="*60)
    print("\nHypothesis: Robot motors might be 'locked' or need '.go()'")
    
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
    print("\n2️⃣ Current position...")
    (x, y, z, r, j1, j2, j3, j4) = device.pose()
    print(f"   X: {x:.2f} mm, Y: {y:.2f} mm, Z: {z:.2f} mm, R: {r:.2f}°")
    
    # TEST 1: Try .lock() method
    print("\n3️⃣ TEST: Trying .lock() method...")
    try:
        # Try lock with different parameters
        print("   Calling device.lock(False)  [hopefully unlocks motors]")
        result = device.lock(False)
        print(f"   Result: {result}")
        time.sleep(1)
    except Exception as e:
        print(f"   Error: {e}")
    
    # TEST 2: Set speed and try movement
    print("\n4️⃣ Setting speed to 100mm/s...")
    device.speed(100, 100)
    
    print("\n5️⃣ TEST: Moving +50mm in X (after unlock)...")
    device.move_to(x + 50, y, z, r, wait=False)  # Queue it
    time.sleep(1)
    
    # TEST 3: Try .go() method
    print("\n6️⃣ TEST: Calling .go() to start movement...")
    try:
        result = device.go()
        print(f"   .go() returned: {result}")
        time.sleep(3)  # Wait for movement
    except Exception as e:
        print(f"   Error: {e}")
    
    # Check new position
    (x2, y2, z2, r2, j1, j2, j3, j4) = device.pose()
    print(f"\n7️⃣ New position after .go():")
    print(f"   X: {x2:.2f} mm, Y: {y2:.2f} mm, Z: {z2:.2f} mm")
    
    moved = abs(x2 - x)
    print(f"   Actual X movement: {moved:.2f}mm (expected: 50mm)")
    
    if moved > 40:
        print("\n" + "="*60)
        print("🎉 SUCCESS! .go() or .lock(False) fixed it!")
        print("="*60)
        result = True
    else:
        print("\n   ❌ Still not moving correctly")
        
        # TEST 4: Try joint movement instead of Cartesian
        print("\n8️⃣ TEST: Try joint movement instead...")
        print(f"   Current J1: {j1:.2f}°")
        print(f"   Moving J1 to {j1 + 10:.2f}°")
        
        try:
            device.j1(j1 + 10, wait=False)
            device.go()
            time.sleep(3)
            
            (x3, y3, z3, r3, j1_new, j2, j3, j4) = device.pose()
            joint_moved = abs(j1_new - j1)
            print(f"   New J1: {j1_new:.2f}° (moved {joint_moved:.2f}°)")
            
            if joint_moved > 5:
                print("\n" + "="*60)
                print("🎉 JOINT movement works! Use .j1(), .j2(), etc.")
                print("="*60)
                result = True
            else:
                print("\n   ❌ Joint movement also failed")
                result = False
                
        except Exception as e:
            print(f"   Error: {e}")
            result = False
    
    # Cleanup
    device.close()
    return result


if __name__ == "__main__":
    port = sys.argv[1] if len(sys.argv) > 1 else '/dev/ttyACM0'
    
    print(f"\nUsing port: {port}")
    print("(To use different port: python test_dobot_go_lock.py /dev/ttyACM0)")
    print("\n⚠️ Robot will attempt to move! Clear workspace!")
    time.sleep(2)
    
    success = test_go_and_lock(port)
    
    if success:
        print("\n✅ We found the fix!")
    else:
        print("\n❌ Still investigating...")
    
    sys.exit(0 if success else 1)

