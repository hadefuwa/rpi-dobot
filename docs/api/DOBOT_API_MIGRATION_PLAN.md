# Official Dobot DLL API Migration Plan

## Executive Summary

**Problem:** The `pydobot` library is incompatible with your Dobot Magician's firmware. Movement commands are sent and acknowledged but the robot doesn't physically move.

**Solution:** Migrate from `pydobot` to the official Dobot DLL API, which is what Dobot Studio uses and is guaranteed to work with your hardware.

**Impact:** This requires rewriting `dobot_client.py` and updating the backend, but will provide full, reliable control over the Dobot.

---

## Why Switch to Official API?

### Current Situation with pydobot
- ❌ Movement commands fail (position stays fixed at 189.06mm)
- ✅ Position reading works
- ✅ Pump/gripper controls work
- ✅ Communication established
- ❌ Robot doesn't move at all

### Evidence from Testing
After extensive diagnostics (v4.1), we confirmed:
1. Commands are sent and acknowledged by Dobot
2. Queue indices are returned correctly
3. Speed/acceleration parameters are set
4. Robot reports "command executed"
5. **BUT physical position never changes**

### Why Official API Will Work
- ✅ Used by Dobot Studio (which DOES work on your hardware)
- ✅ Direct from manufacturer
- ✅ Fully documented with examples
- ✅ Supports all Dobot firmware versions
- ✅ Comprehensive error handling

---

## Understanding the Official Dobot API

### Architecture

```
┌─────────────────────────────────────────────────────┐
│  Python Application (Flask Backend)                 │
├─────────────────────────────────────────────────────┤
│  DobotDLLType.py (Python wrapper)                   │
│  - Loads platform-specific DLL                      │
│  - Provides Python function bindings                │
├─────────────────────────────────────────────────────┤
│  DobotDll.so (Linux) / DobotDll.dll (Windows)       │
│  - Official Dobot library                           │
│  - Low-level serial communication                   │
│  - Firmware-specific protocol                       │
├─────────────────────────────────────────────────────┤
│  USB Serial Connection (/dev/ttyACM0)               │
├─────────────────────────────────────────────────────┤
│  Dobot Magician Hardware                            │
└─────────────────────────────────────────────────────┘
```

### Key Differences from pydobot

| Feature | pydobot | Official API |
|---------|---------|--------------|
| Library type | Simplified wrapper | Full DLL with all features |
| Installation | `pip install pydobot` | Manual DLL installation |
| Initialization | `Dobot(port)` | Multi-step setup with parameters |
| Command queue | Auto-managed | Manual control required |
| Movement | `move_to(x,y,z)` | `SetPTPCmd()` + `SetQueuedCmdStartExec()` |
| Parameters | Optional `.speed()` | **Required** `SetPTPCommonParams()` |
| Error handling | Limited | Comprehensive error codes |

---

## Official API Workflow

### 1. Initialization Sequence
```python
import DobotDLLType as dType

# Load the DLL library
api = dType.load()

# Connect to Dobot
state = dType.ConnectDobot(api, "", 115200)

if state == dType.DobotConnect.DobotConnect_NoError:
    # CRITICAL: Set movement parameters BEFORE any commands
    dType.SetPTPCommonParams(api, velocityRatio=100, accelerationRatio=100, isQueued=1)
    
    # Set home position
    dType.SetHomeParams(api, x=200, y=0, z=150, r=0, isQueued=1)
    
    # Clear any existing commands
    dType.SetQueuedCmdClear(api)
    
    print("✅ Dobot initialized successfully")
else:
    print("❌ Connection failed")
```

### 2. Movement Commands
```python
# Queue a movement command
lastIndex = dType.SetPTPCmd(
    api, 
    dType.PTPMode.PTPMOVLXYZMode,  # Linear movement mode
    x=250, 
    y=0, 
    z=100, 
    r=0, 
    isQueued=1
)[0]

# Start executing queued commands
dType.SetQueuedCmdStartExec(api)

# Wait for completion
while lastIndex > dType.GetQueuedCmdCurrentIndex(api)[0]:
    dType.dSleep(100)  # Sleep 100ms

print("✅ Movement completed")
```

### 3. Peripheral Control
```python
# Suction cup control
dType.SetEndEffectorSuctionCup(api, enableControl=1, suck=1, isQueued=1)
dType.SetQueuedCmdStartExec(api)

# Gripper control (if available)
dType.SetEndEffectorGripper(api, enableControl=1, grip=1, isQueued=1)
dType.SetQueuedCmdStartExec(api)
```

### 4. Position Reading
```python
# Get current position
pose = dType.GetPose(api)
x = pose[0]
y = pose[1]
z = pose[2]
r = pose[3]
print(f"Position: X={x}, Y={y}, Z={z}, R={r}")
```

---

## Implementation Plan

### Phase 1: Setup & Installation (1-2 hours)

**On Raspberry Pi:**

1. **Download DobotDemoV2.0**
   ```bash
   cd ~/rpi-dobot
   wget https://www.dobot.cc/download/DobotDemoV2.0.zip
   unzip DobotDemoV2.0.zip
   ```

2. **Extract Python API files**
   ```bash
   cd DobotDemoV2.0/DobotDemoForPython
   # Copy DobotDLLType.py and DobotDll.so to our project
   cp DobotDLLType.py ~/rpi-dobot/pwa-dobot-plc/backend/
   cp DobotDll.so ~/rpi-dobot/pwa-dobot-plc/backend/
   ```

3. **Test basic connection**
   ```bash
   cd ~/rpi-dobot/pwa-dobot-plc/backend
   python3 -c "import DobotDLLType as dType; print('✅ DLL loaded')"
   ```

### Phase 2: Code Migration (3-4 hours)

**File: `pwa-dobot-plc/backend/dobot_client.py`**

Replace pydobot implementation with official API wrapper.

**Key changes:**

1. **Import statement:**
   ```python
   # OLD
   from pydobot import Dobot as PyDobot
   
   # NEW
   import DobotDLLType as dType
   ```

2. **Class initialization:**
   ```python
   def __init__(self, use_usb: bool = True, usb_path: str = '/dev/ttyACM0'):
       self.api = None
       self.connected = False
       self.use_usb = use_usb
       self.usb_path = usb_path
       self.last_error = ""
       self.last_index = 0
   ```

3. **Connection method:**
   ```python
   def connect(self) -> bool:
       if not self.use_usb:
           return False
       
       # Load DLL
       self.api = dType.load()
       
       # Connect
       state = dType.ConnectDobot(self.api, self.usb_path, 115200)
       
       if state == dType.DobotConnect.DobotConnect_NoError:
           self.connected = True
           
           # CRITICAL: Set parameters before any movement
           dType.SetPTPCommonParams(self.api, 100, 100, isQueued=1)
           dType.SetHomeParams(
               self.api, 
               self.HOME_POSITION['x'],
               self.HOME_POSITION['y'],
               self.HOME_POSITION['z'],
               self.HOME_POSITION['r'],
               isQueued=1
           )
           dType.SetQueuedCmdClear(self.api)
           
           logger.info("✅ Dobot connected and initialized")
           return True
       else:
           self.last_error = f"Connection failed with error: {state}"
           logger.error(self.last_error)
           return False
   ```

4. **Movement method:**
   ```python
   def move_to(self, x: float, y: float, z: float, r: float = 0, wait: bool = True) -> bool:
       if not self.connected:
           return False
       
       try:
           # Queue movement command
           self.last_index = dType.SetPTPCmd(
               self.api,
               dType.PTPMode.PTPMOVLXYZMode,
               x, y, z, r,
               isQueued=1
           )[0]
           
           # Start execution
           dType.SetQueuedCmdStartExec(self.api)
           
           # Wait if requested
           if wait:
               while self.last_index > dType.GetQueuedCmdCurrentIndex(self.api)[0]:
                   dType.dSleep(50)
           
           logger.info(f"✅ Move to ({x}, {y}, {z}) completed")
           return True
       except Exception as e:
           self.last_error = str(e)
           logger.error(f"❌ Move error: {e}")
           return False
   ```

5. **Other methods (suction, gripper, etc.):**
   Similar conversion pattern for all methods.

### Phase 3: Testing (2-3 hours)

**Test sequence:**

1. **Basic connection test**
   ```bash
   python test_official_api_connection.py
   ```

2. **Position reading test**
   ```bash
   python test_official_api_position.py
   ```

3. **Movement test** (the critical one!)
   ```bash
   python test_official_api_movement.py
   ```

4. **Full integration test**
   ```bash
   python app.py
   # Test via web interface
   ```

### Phase 4: Integration & Cleanup (1-2 hours)

1. Update `requirements.txt` (remove pydobot)
2. Update documentation
3. Clean up old test files
4. Final end-to-end testing

---

## File Changes Summary

### Files to Modify
1. **`dobot_client.py`** - Complete rewrite (core change)
2. **`app.py`** - Minor changes (method signatures might differ slightly)
3. **`requirements.txt`** - Remove `pydobot==1.3.2`
4. **`DEPLOY_TO_PI.md`** - Update installation instructions

### New Files to Add
1. **`DobotDLLType.py`** - Official Python wrapper (from DobotDemoV2.0)
2. **`DobotDll.so`** - Official library for Linux ARM (from DobotDemoV2.0)
3. **`test_official_api_connection.py`** - Test script
4. **`test_official_api_movement.py`** - Movement validation

### Files to Keep (No Changes)
- `plc_client.py` - PLC communication unaffected
- `config.json` - Configuration format stays same
- `frontend/index.html` - Frontend API calls unchanged

---

## Risks & Mitigation

### Risk 1: DLL Not Available for ARM Linux
**Likelihood:** Low  
**Impact:** High  
**Mitigation:** DobotDemoV2.0 includes pre-compiled ARM binaries. If missing, we can compile from source (Dobot provides C++ source code).

### Risk 2: Learning Curve for New API
**Likelihood:** Medium  
**Impact:** Low  
**Mitigation:** Official documentation is comprehensive. Examples in DobotDemoV2.0 cover all use cases.

### Risk 3: Breaking Existing Features
**Likelihood:** Medium  
**Impact:** Medium  
**Mitigation:** 
- Keep old code in git history
- Incremental testing after each change
- Feature parity checklist before considering complete

### Risk 4: Firmware Incompatibility
**Likelihood:** Very Low  
**Impact:** High  
**Mitigation:** Official API works with all Dobot firmware versions. Dobot Studio already proves compatibility with your hardware.

---

## Success Criteria

✅ **Must Have (Phase 1 success):**
1. Dobot connects successfully
2. Position reading works
3. **Robot physically moves** when commanded
4. Home position command works
5. Manual X/Y/Z movement works in web app

✅ **Should Have (Phase 2 success):**
6. Preset positions work
7. Suction cup control works
8. Gripper control works (if applicable)
9. Emergency stop works
10. Settings page updates work

✅ **Nice to Have (Phase 3 polish):**
11. Smooth acceleration/deceleration
12. Path planning for linear movements
13. Collision detection
14. Advanced queue management

---

## Timeline Estimate

| Phase | Task | Duration | Dependencies |
|-------|------|----------|--------------|
| 1 | Download & install DLL | 1 hour | Internet access |
| 1 | Test basic DLL loading | 30 min | Phase 1.1 |
| 2 | Rewrite `dobot_client.py` | 2 hours | Phase 1 |
| 2 | Update `app.py` routes | 1 hour | Phase 2.1 |
| 3 | Connection testing | 30 min | Phase 2 |
| 3 | Movement testing | 1 hour | Phase 3.1 |
| 3 | Full integration test | 1 hour | Phase 3.2 |
| 4 | Documentation updates | 30 min | Phase 3 |
| 4 | Code cleanup | 30 min | Phase 4.1 |

**Total Estimated Time:** 8-10 hours

**Recommended Schedule:**
- **Day 1 (3 hours):** Phase 1 + 2.1 (Setup & start coding)
- **Day 2 (3 hours):** Phase 2.2 + 3.1 (Finish coding & basic tests)
- **Day 3 (2 hours):** Phase 3.2 + 4 (Integration & polish)

---

## Alternative Options Considered

### Option A: Try Different pydobot Fork
**Pros:** Faster, less code change  
**Cons:** No guarantee of success, still third-party  
**Decision:** Rejected - we've already proven pydobot doesn't work

### Option B: Direct Serial Protocol Implementation
**Pros:** Full control, no dependencies  
**Cons:** Extremely complex, error-prone, would take weeks  
**Decision:** Rejected - reinventing the wheel

### Option C: Use ROS (Robot Operating System)
**Pros:** Industry standard, powerful features  
**Cons:** Massive overhead for this project, steep learning curve  
**Decision:** Rejected - overkill for our use case

### Option D: Official Dobot DLL API (SELECTED)
**Pros:** 
- Guaranteed to work
- Official support
- Comprehensive features
- Well documented
**Cons:** 
- Requires code rewrite
- 8-10 hour time investment
**Decision:** ✅ **SELECTED** - Best balance of reliability and effort

---

## Next Steps

1. **Get your approval** on this plan
2. **Download DobotDemoV2.0** on your Raspberry Pi
3. **Test basic DLL loading** to confirm library works on ARM
4. **Begin Phase 2** (code migration)
5. **Incremental testing** after each major change

---

## Questions to Resolve

Before starting, we need to confirm:

1. ✅ **Is internet available on your Raspberry Pi?** (To download DobotDemoV2.0)
2. ❓ **Do you want to keep pydobot as a fallback?** (Can maintain both implementations temporarily)
3. ❓ **Should we implement queue management now or keep it simple?** (Queue allows choreographed movements)
4. ❓ **Any specific Dobot features you need?** (Conveyor belt, sliding rail, laser, etc.)

---

## References

- [Dobot Official Downloads](https://www.dobot.cc/downloadcenter/dobot-magician.html)
- [DobotDemoV2.0 - Python Examples](https://www.dobot.cc/downloadcenter/dobot-magician.html?sub_cat=72#sub-download)
- [StarterGuide - Dobot with Python](https://github.com/SERLatBTH/StarterGuide-Dobot-Magician-with-Python)
- [Dobot Magician API Description](https://www.dobot.cc/downloadcenter.html?sub_cat=72#sub-download)

---

**Document Version:** 1.0  
**Created:** 2025-10-21  
**Status:** Awaiting approval to proceed  
**Related Tag:** v4.1 (diagnostic work completed)

