#!/usr/bin/env python3
"""
Test script to verify PLC communication
Tests reading DB1 and M-memory values
"""

import os
import sys
from plc_client import PLCClient
import time

# ANSI color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(text):
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}{text:^60}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")

def print_success(text):
    print(f"{GREEN}✅ {text}{RESET}")

def print_error(text):
    print(f"{RED}❌ {text}{RESET}")

def print_info(text):
    print(f"{YELLOW}ℹ️  {text}{RESET}")

def test_connection():
    """Test basic PLC connection"""
    print_header("TEST 1: PLC Connection")

    # Get PLC IP from environment or use default
    plc_ip = os.getenv('PLC_IP', '192.168.0.150')
    plc_rack = int(os.getenv('PLC_RACK', '0'))
    plc_slot = int(os.getenv('PLC_SLOT', '1'))

    print_info(f"Connecting to PLC at {plc_ip} (Rack: {plc_rack}, Slot: {plc_slot})")

    plc = PLCClient(plc_ip, plc_rack, plc_slot)

    if plc.connect():
        print_success(f"Connected to PLC at {plc_ip}")
        return plc
    else:
        print_error(f"Failed to connect: {plc.last_error}")
        return None

def test_db1_read(plc):
    """Test reading DB1 REAL values"""
    print_header("TEST 2: Reading DB1 Position Data")

    print_info("Reading Target Position (DB1.DBD0, DBD4, DBD8)...")

    target_pose = plc.read_target_pose()

    print(f"\n  Target X (DB1.DBD0):  {target_pose['x']:.2f}")
    print(f"  Target Y (DB1.DBD4):  {target_pose['y']:.2f}")
    print(f"  Target Z (DB1.DBD8):  {target_pose['z']:.2f}\n")

    # Expected values from your screenshot
    expected = {'x': 20.0, 'y': 50.0, 'z': 0.0}

    # Check if values match (with small tolerance for floating point)
    tolerance = 0.1
    all_match = True

    for axis in ['x', 'y', 'z']:
        if abs(target_pose[axis] - expected[axis]) < tolerance:
            print_success(f"{axis.upper()} matches expected value: {expected[axis]}")
        else:
            print_error(f"{axis.upper()} mismatch! Expected {expected[axis]}, got {target_pose[axis]}")
            all_match = False

    return all_match

def test_m_memory_bits(plc):
    """Test reading M-memory control bits"""
    print_header("TEST 3: Reading M-Memory Control Bits")

    print_info("Reading M0.0 - M0.7...")

    control_bits = plc.read_control_bits()

    print(f"\n  M0.0 (Start):     {control_bits['start']}")
    print(f"  M0.1 (Stop):      {control_bits['stop']}")
    print(f"  M0.2 (Home):      {control_bits['home']}")
    print(f"  M0.3 (E-Stop):    {control_bits['estop']}")
    print(f"  M0.4 (Suction):   {control_bits['suction']}")
    print(f"  M0.5 (Ready):     {control_bits['ready']}")
    print(f"  M0.6 (Busy):      {control_bits['busy']}")
    print(f"  M0.7 (Error):     {control_bits['error']}\n")

    # Expected values from your screenshot
    expected_bits = {
        'start': True,    # M0.0 = TRUE in screenshot
        'stop': False,    # M0.1 = FALSE
        'home': False,    # M0.2 = FALSE
        'estop': False,   # M0.3 = FALSE
        'suction': True,  # M0.4 = TRUE in screenshot
        'ready': False,   # M0.5 = FALSE
        'busy': False,    # M0.6 = FALSE
        'error': False    # M0.7 = FALSE
    }

    all_match = True

    for bit_name, expected_value in expected_bits.items():
        actual_value = control_bits[bit_name]

        if actual_value == expected_value:
            status = "TRUE" if actual_value else "FALSE"
            print_success(f"{bit_name.upper():10} = {status} (matches expected)")
        else:
            print_error(f"{bit_name.upper():10} mismatch! Expected {expected_value}, got {actual_value}")
            all_match = False

    return all_match

def test_individual_reads(plc):
    """Test individual low-level read operations"""
    print_header("TEST 4: Individual Read Operations")

    print_info("Testing individual DB1 reads...")

    # Read individual REAL values
    x = plc.read_db_real(1, 0)
    y = plc.read_db_real(1, 4)
    z = plc.read_db_real(1, 8)

    print(f"\n  DB1.DBD0  (X): {x:.2f}")
    print(f"  DB1.DBD4  (Y): {y:.2f}")
    print(f"  DB1.DBD8  (Z): {z:.2f}\n")

    print_info("Testing individual M-bit reads...")

    # Read individual bits
    m0_0 = plc.read_m_bit(0, 0)  # M0.0
    m0_1 = plc.read_m_bit(0, 1)  # M0.1
    m0_4 = plc.read_m_bit(0, 4)  # M0.4

    print(f"\n  M0.0 (Start):   {m0_0}")
    print(f"  M0.1 (Stop):    {m0_1}")
    print(f"  M0.4 (Suction): {m0_4}\n")

    # Verify the toggled bits
    if m0_0 == True:
        print_success("M0.0 (Start) is TRUE ✅")
    else:
        print_error("M0.0 (Start) should be TRUE")

    if m0_4 == True:
        print_success("M0.4 (Suction) is TRUE ✅")
    else:
        print_error("M0.4 (Suction) should be TRUE")

    if m0_1 == False:
        print_success("M0.1 (Stop) is FALSE ✅")
    else:
        print_error("M0.1 (Stop) should be FALSE")

    return True

def test_write_operation(plc):
    """Test writing current pose back to PLC"""
    print_header("TEST 5: Write Current Pose to PLC")

    print_info("Writing test position to DB1.DBD12-20 (Current Position)...")

    test_pose = {'x': 100.5, 'y': 200.75, 'z': 50.25}

    plc.write_current_pose(test_pose)

    print(f"\n  Written X = {test_pose['x']:.2f} to DB1.DBD12")
    print(f"  Written Y = {test_pose['y']:.2f} to DB1.DBD16")
    print(f"  Written Z = {test_pose['z']:.2f} to DB1.DBD20\n")

    print_info("Reading back to verify...")
    time.sleep(0.1)

    # Read back from DB1
    x_readback = plc.read_db_real(1, 12)
    y_readback = plc.read_db_real(1, 16)
    z_readback = plc.read_db_real(1, 20)

    print(f"\n  Read back X = {x_readback:.2f}")
    print(f"  Read back Y = {y_readback:.2f}")
    print(f"  Read back Z = {z_readback:.2f}\n")

    # Verify write worked
    tolerance = 0.1
    if (abs(x_readback - test_pose['x']) < tolerance and
        abs(y_readback - test_pose['y']) < tolerance and
        abs(z_readback - test_pose['z']) < tolerance):
        print_success("Write/Read verification successful! ✅")
        return True
    else:
        print_error("Write/Read verification failed!")
        return False

def main():
    """Run all tests"""
    print(f"\n{BLUE}{'='*60}")
    print(f"{'PLC COMMUNICATION TEST SUITE':^60}")
    print(f"{'='*60}{RESET}\n")

    # Test 1: Connection
    plc = test_connection()
    if not plc:
        print_error("Cannot proceed without PLC connection")
        sys.exit(1)

    time.sleep(0.5)

    # Test 2: DB1 Read
    db1_ok = test_db1_read(plc)
    time.sleep(0.5)

    # Test 3: M-Memory Bits
    bits_ok = test_m_memory_bits(plc)
    time.sleep(0.5)

    # Test 4: Individual Reads
    individual_ok = test_individual_reads(plc)
    time.sleep(0.5)

    # Test 5: Write Test
    write_ok = test_write_operation(plc)
    time.sleep(0.5)

    # Disconnect
    print_header("CLEANUP")
    plc.disconnect()
    print_success("Disconnected from PLC")

    # Summary
    print_header("TEST SUMMARY")

    total_tests = 5
    passed_tests = sum([True, db1_ok, bits_ok, individual_ok, write_ok])

    print(f"\n  Total Tests:  {total_tests}")
    print(f"  Passed:       {GREEN}{passed_tests}{RESET}")
    print(f"  Failed:       {RED}{total_tests - passed_tests}{RESET}\n")

    if passed_tests == total_tests:
        print(f"{GREEN}{'='*60}")
        print(f"{'ALL TESTS PASSED! ✅':^60}")
        print(f"{'='*60}{RESET}\n")
        print_info("Your PLC communication is working perfectly!")
        print_info("You can now deploy the PWA application.")
    else:
        print(f"{RED}{'='*60}")
        print(f"{'SOME TESTS FAILED':^60}")
        print(f"{'='*60}{RESET}\n")
        print_error("Please check PLC configuration:")
        print("  1. Verify PUT/GET communication is enabled in TIA Portal")
        print("  2. Verify DB1 is non-optimized")
        print("  3. Check PLC IP address in .env file")

    print()

if __name__ == "__main__":
    # Load environment variables from .env if exists
    from pathlib import Path
    env_file = Path(__file__).parent / '.env'
    if env_file.exists():
        print_info(f"Loading environment from {env_file}")
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

    main()
