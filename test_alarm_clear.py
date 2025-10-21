#!/usr/bin/env python3
"""Check and clear Dobot alarms"""

import sys
import os
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'pwa-dobot-plc', 'backend'))

from pydobot import Dobot
from pydobot.message import Message
from pydobot.enums.CommunicationProtocolIDs import CommunicationProtocolIDs
from pydobot.enums.ControlValues import ControlValues

print('Checking for alarms and errors...')
print('='*60)

device = Dobot(port='/dev/ttyACM0', verbose=True)

# Get current position
print('\n1. Current position:')
pose = device.pose()
print(f'   X={pose[0]:.2f}, Y={pose[1]:.2f}, Z={pose[2]:.2f}')

# Get alarms
print('\n2. Checking alarms...')
msg = Message()
msg.id = CommunicationProtocolIDs.GET_ALARMS_STATE
msg.ctrl = ControlValues.ZERO
response = device._send_command(msg)
print(f'   Alarm data (hex): {response.params.hex() if response and response.params else "None"}')

# Clear all alarms
print('\n3. Clearing all alarms...')
msg = Message()
msg.id = CommunicationProtocolIDs.CLEAR_ALL_ALARMS_STATE
msg.ctrl = ControlValues.ONE
device._send_command(msg)
print('   ✅ Clear command sent')

# Try resetting pose
print('\n4. Trying RESET_POSE command...')
msg = Message()
msg.id = CommunicationProtocolIDs.RESET_POSE
msg.ctrl = ControlValues.ZERO
msg.params = bytearray([0x01, 0x00, 0x00, 0x00])  # Manual mode, auto level off
device._send_command(msg)
print('   ✅ Reset pose sent')

time.sleep(0.5)

# Try moving
print('\n5. Attempting movement with verbose output...')
print('   Moving to X=200, Y=0, Z=150...')
device.move_to(200.0, 0.0, 150.0, 0.0, wait=True)

time.sleep(1)

# Check final position
print('\n6. Final position:')
final_pose = device.pose()
print(f'   X={final_pose[0]:.2f}, Y={final_pose[1]:.2f}, Z={final_pose[2]:.2f}')

distance = ((final_pose[0] - pose[0])**2 + (final_pose[1] - pose[1])**2 + (final_pose[2] - pose[2])**2)**0.5
print(f'\n   Distance moved: {distance:.2f}mm')

if distance > 5.0:
    print('\n✅ SUCCESS - Robot moved!')
else:
    print('\n❌ Robot still not moving')

device.close()
