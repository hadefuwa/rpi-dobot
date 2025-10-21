# Official Dobot API - Quick Reference Card

## Installation (One-time Setup)

```bash
# On Raspberry Pi
cd ~/rpi-dobot
bash setup_official_dobot_api.sh
bash migrate_to_official_api.sh
```

---

## Basic Usage Pattern

Every Dobot operation follows this pattern:

```python
from dobot_client import DobotClient

# 1. Create client
client = DobotClient(use_usb=True, usb_path="")

# 2. Connect
if client.connect():
    # 3. Perform operations
    client.move_to(200, 0, 150)

    # 4. Disconnect when done
    client.disconnect()
```

---

## Common Operations

### Movement

```python
# Move to specific position
client.move_to(x=250, y=50, z=100, r=0, wait=True)

# Move to home
client.home(wait=True)

# Get current position
pose = client.get_pose()
print(f"X: {pose['x']}, Y: {pose['y']}, Z: {pose['z']}")
```

### Suction Cup

```python
# Enable suction
client.set_suction(True)

# Disable suction
client.set_suction(False)
```

### Gripper

```python
# Open gripper
client.set_gripper(True)

# Close gripper
client.set_gripper(False)
```

### Speed Control

```python
# Set speed (1-100%)
client.set_speed(velocity_ratio=50, acceleration_ratio=50)
```

### Emergency Stop

```python
# Stop all movement immediately
client.emergency_stop()
```

---

## Movement Modes

The official API uses `PTPMOVLXYZMode` (linear movement) by default.

Other modes available in DobotDLLType:
- `PTPJUMPXYZMode` - Jump movement (arch)
- `PTPMOVJXYZMode` - Joint movement
- `PTPMOVLANGLEMode` - Linear angle movement

---

## Coordinate System

```
         Z (up)
         |
         |
         |_____ Y
        /
       /
      X
```

- **X**: Forward/backward (positive = away from base)
- **Y**: Left/right (positive = left when facing robot)
- **Z**: Up/down (positive = up)
- **R**: Rotation (degrees, around Z-axis)

### Safe Working Range
- X: 150 - 300 mm
- Y: -150 - 150 mm
- Z: 0 - 200 mm
- R: -90 - 90 degrees

---

## Error Handling

```python
client = DobotClient()

if not client.connect():
    print(f"Connection failed: {client.last_error}")
    exit(1)

if not client.move_to(200, 0, 150):
    print(f"Move failed: {client.last_error}")
```

---

## Testing Commands

```bash
# Test connection
python3 test_official_api_connection.py

# Test movement (ensure clear space!)
python3 test_official_api_movement.py

# Test suction/gripper
python3 test_official_api_peripherals.py
```

---

## Key Differences from pydobot

| Operation | pydobot | Official API |
|-----------|---------|--------------|
| Import | `from pydobot import Dobot` | `from dobot_client import DobotClient` |
| Connect | `Dobot(port='/dev/ttyACM0')` | `client.connect()` |
| Move | `device.move_to(x,y,z,r)` | `client.move_to(x,y,z,r)` |
| Suction | `device.suck(True)` | `client.set_suction(True)` |
| Gripper | `device.grip(True)` | `client.set_gripper(False)` ⚠️ inverted |
| Position | `device.pose()` | `client.get_pose()` |

---

## Troubleshooting

### Connection Issues
```bash
# Check USB devices
ls -la /dev/ttyACM* /dev/ttyUSB*

# Check permissions
sudo usermod -a -G dialout $USER
# Then logout/login

# Check Dobot power
# Check USB cable
```

### Movement Not Working
```python
# Ensure wait=True for blocking movement
client.move_to(200, 0, 150, wait=True)

# Check movement parameters were initialized
# (This is done automatically in client.connect())
```

### Import Errors
```bash
# Check DLL files exist
ls -la ~/rpi-dobot/pwa-dobot-plc/backend/DobotDLL*

# Re-run setup if missing
cd ~/rpi-dobot
bash setup_official_dobot_api.sh
```

---

## Web Application Integration

The web app uses the same API automatically.

Just ensure `dobot_client.py` is using the official API version:
```bash
# Check which version is active
head -20 ~/rpi-dobot/pwa-dobot-plc/backend/dobot_client.py
# Should say "Official API Version"
```

---

## Advanced: Direct DLL Usage

If you need lower-level control:

```python
import DobotDLLType as dType

# Load DLL
api = dType.load()

# Connect
state = dType.ConnectDobot(api, "", 115200)

# Set parameters (REQUIRED before movement)
dType.SetPTPCommonParams(api, velocityRatio=100, accelerationRatio=100, isQueued=1)

# Queue movement
index = dType.SetPTPCmd(api, dType.PTPMode.PTPMOVLXYZMode, 200, 0, 150, 0, isQueued=1)[0]

# Start execution
dType.SetQueuedCmdStartExec(api)

# Wait for completion
while index > dType.GetQueuedCmdCurrentIndex(api)[0]:
    dType.dSleep(50)

# Disconnect
dType.DisconnectDobot(api)
```

---

## Support Files

- **Full migration plan**: [DOBOT_API_MIGRATION_PLAN.md](DOBOT_API_MIGRATION_PLAN.md)
- **Step-by-step guide**: [OFFICIAL_API_MIGRATION_GUIDE.md](OFFICIAL_API_MIGRATION_GUIDE.md)
- **Source code**: [dobot_client_official.py](pwa-dobot-plc/backend/dobot_client_official.py)

---

**Quick Tip:** Always use `wait=True` for movements when you want them to complete before the next command. This ensures reliable sequential operations.

**Remember:** The official API provides much better control and reliability than pydobot, especially for movement commands!
