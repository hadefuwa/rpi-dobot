#!/usr/bin/env python3
"""Test Improved Dobot Client"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'pwa-dobot-plc', 'backend'))

from dobot_client import DobotClient
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

print('='*60)
print('Testing Improved Dobot Client')
print('='*60)
print()

client = DobotClient(use_usb=True, usb_path='')

print('Connecting...')
if client.connect():
    print('✅ CONNECTED!')
    print()

    pose = client.get_pose()
    print(f'Current position: X={pose["x"]:.2f}, Y={pose["y"]:.2f}, Z={pose["z"]:.2f}')
    print()

    print('Testing movement to home position...')
    if client.home(wait=True):
        print('✅ Home command completed')

        pose_after = client.get_pose()
        print(f'Position after home: X={pose_after["x"]:.2f}, Y={pose_after["y"]:.2f}, Z={pose_after["z"]:.2f}')

    print()
    client.disconnect()
    print('✅ Test completed successfully!')
    sys.exit(0)
else:
    print(f'❌ Connection failed: {client.last_error}')
    sys.exit(1)
