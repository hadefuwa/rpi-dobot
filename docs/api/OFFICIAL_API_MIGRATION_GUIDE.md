# Official Dobot API Migration Guide

## Quick Start

This guide walks you through migrating from `pydobot` to the official Dobot DLL API.

**Estimated Time:** 1-2 hours
**Difficulty:** Medium
**Prerequisites:** SSH access to Raspberry Pi, Dobot connected via USB

---

## Step-by-Step Instructions

### Step 1: Transfer Files to Raspberry Pi

From your Windows PC, transfer the new files to the Pi:

```bash
# Navigate to the project directory
cd c:\Users\Hamed\Documents\rpi-dobot

# Transfer all migration files
scp setup_official_dobot_api.sh pi@rpi:~/rpi-dobot/
scp migrate_to_official_api.sh pi@rpi:~/rpi-dobot/
scp test_official_api_*.py pi@rpi:~/rpi-dobot/
scp pwa-dobot-plc/backend/dobot_client_official.py pi@rpi:~/rpi-dobot/pwa-dobot-plc/backend/
```

Or use the password authentication:
```bash
sshpass -p "1" scp setup_official_dobot_api.sh pi@rpi:~/rpi-dobot/
sshpass -p "1" scp migrate_to_official_api.sh pi@rpi:~/rpi-dobot/
sshpass -p "1" scp test_official_api_*.py pi@rpi:~/rpi-dobot/
sshpass -p "1" scp pwa-dobot-plc/backend/dobot_client_official.py pi@rpi:~/rpi-dobot/pwa-dobot-plc/backend/
```

### Step 2: SSH into Raspberry Pi

```bash
ssh pi@rpi
# Or: sshpass -p "1" ssh pi@rpi
```

### Step 3: Download Official Dobot API

You have two options:

#### Option A: Download Directly on Pi (if internet available)

```bash
cd ~
# The script will guide you through downloading
```

#### Option B: Download on Windows PC and Transfer

1. On Windows, download from: https://www.dobot.cc/downloadcenter/dobot-magician.html
2. Look for "DobotDemoV2.0" or "Dobot Demo for Python"
3. Transfer to Pi:
   ```bash
   scp DobotDemoV2.0.zip pi@rpi:~/
   ```

### Step 4: Run Setup Script

```bash
cd ~/rpi-dobot
chmod +x setup_official_dobot_api.sh
bash setup_official_dobot_api.sh
```

**What this does:**
- Extracts DobotDemoV2.0.zip
- Locates DobotDLLType.py and DobotDll.so
- Copies them to the backend directory
- Tests that the DLL loads correctly

**Expected output:**
```
✅ DobotDLLType imported successfully!
✅ DLL loaded successfully!
🎉 Official Dobot API is ready to use!
```

### Step 5: Run Migration Script

```bash
chmod +x migrate_to_official_api.sh
bash migrate_to_official_api.sh
```

**What this does:**
- Backs up old dobot_client.py (as dobot_client_pydobot_backup.py)
- Installs new dobot_client.py with official API
- Removes pydobot from requirements.txt
- Runs connection test

**Expected output:**
```
✅ Migration Complete!
```

### Step 6: Test Connection

```bash
python3 test_official_api_connection.py
```

**Expected output:**
```
✅ CONNECTION SUCCESSFUL!
   Port: /dev/ttyACM0
✅ Current position:
   X: 189.06 mm
   Y: 0.00 mm
   Z: 150.00 mm
   R: 0.00 degrees
```

### Step 7: Test Movement (THE CRITICAL TEST!)

⚠️ **Important:** Make sure the robot has clear space to move!

```bash
python3 test_official_api_movement.py
```

**Expected output:**
```
✅ Robot MOVED! Total position change: 45.23mm
✅ Robot reached target position accurately!
🎉 MOVEMENT TEST PASSED!
```

**This is the moment of truth!** If you see the robot physically moving, the migration is successful! 🎉

### Step 8: Test Peripherals

```bash
python3 test_official_api_peripherals.py
```

Tests suction cup and gripper controls.

### Step 9: Test Web Application

```bash
cd ~/rpi-dobot/pwa-dobot-plc/backend
python3 app.py
```

Open web browser to: `http://rpi:8080`

Test all functionality:
- ✅ Connect to Dobot
- ✅ Read position
- ✅ Home button
- ✅ Manual X/Y/Z controls
- ✅ Preset positions
- ✅ Suction cup control
- ✅ Emergency stop

---

## Troubleshooting

### Problem: "DobotDLLType not found"

**Solution:**
```bash
# Check if files are in the right place
ls -la ~/rpi-dobot/pwa-dobot-plc/backend/DobotDLL*

# If missing, re-run setup script
cd ~/rpi-dobot
bash setup_official_dobot_api.sh
```

### Problem: "Connection failed"

**Solution:**
```bash
# Check USB connection
ls -la /dev/ttyACM* /dev/ttyUSB*

# Check permissions
sudo usermod -a -G dialout $USER
# Then logout and login again

# Check Dobot is powered on
# Check USB cable is connected
```

### Problem: "DLL not found" or "cannot open shared object"

**Solution:**
```bash
# Check DLL exists and is executable
ls -la ~/rpi-dobot/pwa-dobot-plc/backend/DobotDll.so
chmod +x ~/rpi-dobot/pwa-dobot-plc/backend/DobotDll.so

# Check architecture
file ~/rpi-dobot/pwa-dobot-plc/backend/DobotDll.so
# Should say "ARM" or "aarch64"
```

### Problem: Robot connects but still doesn't move

**Possible causes:**
1. Movement parameters not set correctly
2. Command queue not started
3. Robot in error state

**Solution:**
```bash
# Check the logs carefully for error messages
python3 test_official_api_movement.py

# Try power cycling the Dobot
# Restart Dobot Studio on Windows to verify hardware works
```

---

## Rollback Instructions

If something goes wrong and you need to go back to pydobot:

```bash
cd ~/rpi-dobot/pwa-dobot-plc/backend

# Restore old dobot_client.py
cp dobot_client_pydobot_backup.py dobot_client.py

# Restore pydobot in requirements.txt
echo "pydobot==1.3.2" >> requirements.txt

# Reinstall pydobot
pip3 install pydobot==1.3.2

# Restart application
python3 app.py
```

---

## File Changes Summary

### New Files Added
- `DobotDLLType.py` - Official Python wrapper
- `DobotDll.so` - Official Dobot library (Linux ARM)
- `dobot_client_official.py` - New implementation
- `test_official_api_connection.py` - Connection test
- `test_official_api_movement.py` - Movement test
- `test_official_api_peripherals.py` - Peripherals test

### Files Modified
- `dobot_client.py` - Replaced with official API version
- `requirements.txt` - Removed pydobot dependency

### Backup Files Created
- `dobot_client_pydobot_backup.py` - Original pydobot implementation

---

## Key Differences from pydobot

### Old Way (pydobot)
```python
from pydobot import Dobot

device = Dobot(port='/dev/ttyACM0')
device.move_to(200, 0, 150, 0, wait=True)
device.suck(True)
```

### New Way (Official API)
```python
import DobotDLLType as dType

api = dType.load()
dType.ConnectDobot(api, "", 115200)
dType.SetPTPCommonParams(api, 100, 100, isQueued=1)  # Required!
dType.SetPTPCmd(api, dType.PTPMode.PTPMOVLXYZMode, 200, 0, 150, 0, isQueued=1)
dType.SetQueuedCmdStartExec(api)  # Required!
```

### What Changed
1. **Explicit parameter setting** - Must call `SetPTPCommonParams()` before movement
2. **Queue management** - Must explicitly start command execution with `SetQueuedCmdStartExec()`
3. **More control** - Can control velocity, acceleration, movement modes
4. **Better error handling** - Detailed error codes and states

---

## Success Criteria

✅ **Phase 1 Success:**
- [ ] DLL loads without errors
- [ ] Dobot connects successfully
- [ ] Position reading works
- [ ] **Robot physically moves when commanded** ← MOST IMPORTANT!

✅ **Phase 2 Success:**
- [ ] Web application connects to Dobot
- [ ] All manual controls work
- [ ] Preset positions work
- [ ] Suction cup control works
- [ ] Emergency stop works

✅ **Phase 3 Success:**
- [ ] Movement is smooth and accurate
- [ ] No strange errors in logs
- [ ] System stable over multiple operations

---

## Next Steps After Migration

1. **Update documentation** - Update README.md with new API details
2. **Test integration** - Test with PLC if applicable
3. **Performance tuning** - Adjust velocity/acceleration parameters
4. **Add advanced features** - Implement queue-based choreography if needed

---

## Support & References

- [Official Dobot Downloads](https://www.dobot.cc/downloadcenter/dobot-magician.html)
- [DobotDemo Python Examples](https://github.com/topics/dobot-magician)
- [Migration Plan (detailed)](DOBOT_API_MIGRATION_PLAN.md)

---

**Document Version:** 1.0
**Last Updated:** 2025-10-21
**Status:** Ready for deployment
