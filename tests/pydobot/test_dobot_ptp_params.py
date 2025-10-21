#!/usr/bin/env python3
"""
Test if pydobot needs explicit PTP parameter initialization
Based on official Dobot API documentation
"""

import sys
import time
from pydobot import Dobot

def test_ptp_params(port='/dev/ttyACM0'):
    """Test setting PTP parameters explicitly through the underlying API"""
    
    print("\n" + "="*60)
    print("🔧 DOBOT PTP PARAMETER TEST")
    print("="*60)
    print("\nBased on official Dobot API documentation:")
    print("SetPTPCommonParams() must be called before movement!")
    
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
    print(f"   X: {x:.2f} mm, Y: {y:.2f} mm, Z: {z:.2f} mm")
    
    # Try to access the underlying serial object to send raw commands
    print("\n3️⃣ Checking if we can access underlying API...")
    if hasattr(device, 'ser'):
        print("   ✅ Found serial port object!")
        print(f"   Serial port: {device.ser.port if hasattr(device.ser, 'port') else 'unknown'}")
    else:
        print("   ❌ Cannot access serial port")
    
    # Check what attributes/methods the device has
    print("\n4️⃣ Examining pydobot Dobot object...")
    methods = [m for m in dir(device) if not m.startswith('_')]
    print(f"   Available methods: {', '.join(methods[:10])}...")
    
    # Try different approaches
    print("\n5️⃣ TEST 1: Set speed using pydobot's .speed() method")
    print("   Setting speed(200, 200)...")
    device.speed(200, 200)  # Try higher values
    time.sleep(1)
    
    print("\n6️⃣ TEST 1: Move +50mm in X...")
    device.move_to(x + 50, y, z, r, wait=True)
    time.sleep(3)
    
    (x2, y2, z2, r2, j1, j2, j3, j4) = device.pose()
    moved1 = abs(x2 - x)
    print(f"   Result: Moved {moved1:.2f}mm (expected 50mm)")
    
    if moved1 > 40:
        print("\n🎉 SUCCESS! Higher speed fixed it!")
        device.close()
        return True
    
    # If that didn't work, try checking if there are other initialization methods
    print("\n7️⃣ TEST 2: Looking for other initialization methods...")
    
    # Check if there's a way to access the raw DLL
    if hasattr(device, '_set_ptp_common_params'):
        print("   Found _set_ptp_common_params method!")
        try:
            device._set_ptp_common_params(200, 200)
            print("   ✅ Called _set_ptp_common_params")
        except Exception as e:
            print(f"   Error: {e}")
    
    if hasattr(device, '_set_ptp_cmd'):
        print("   Found _set_ptp_cmd method!")
    
    # Try moving again
    print("\n8️⃣ TEST 2: Move back to original position...")
    device.move_to(x, y, z, r, wait=True)
    time.sleep(3)
    
    (x3, y3, z3, r3, j1, j2, j3, j4) = device.pose()
    moved2 = abs(x3 - x2)
    print(f"   Result: Moved {moved2:.2f}mm")
    
    if moved2 > 40:
        print("\n🎉 SUCCESS!")
        device.close()
        return True
    
    print("\n" + "="*60)
    print("❌ CONCLUSION: PTP parameters aren't the issue")
    print("="*60)
    print("\nThe problem is likely:")
    print("1. Pydobot library is incompatible with your Dobot firmware")
    print("2. There's a low-level communication protocol mismatch")
    print("3. The Dobot might be in a locked/disabled state")
    print("\nRECOMMENDATION:")
    print("- Use the official Dobot DLL API instead of pydobot")
    print("- Check if firmware update is needed")
    print("- Try power cycling the Dobot completely")
    
    device.close()
    return False


if __name__ == "__main__":
    port = sys.argv[1] if len(sys.argv) > 1 else '/dev/ttyACM0'
    
    print(f"\nUsing port: {port}")
    print("⚠️ Robot will attempt to move! Clear workspace!")
    time.sleep(2)
    
    success = test_ptp_params(port)
    
    sys.exit(0 if success else 1)

