# DOBOT Magician API Commands Reference

## Table of Contents
1. [Overview](#overview)
2. [Connection & Setup](#connection--setup)
3. [Movement Commands](#movement-commands)
4. [End Effector Commands](#end-effector-commands)
5. [I/O Commands](#io-commands)
6. [Queue Management](#queue-management)
7. [Device Information](#device-information)
8. [Advanced Features](#advanced-features)
9. [Error Handling](#error-handling)
10. [Code Examples](#code-examples)
11. [Troubleshooting](#troubleshooting)

---

## Overview

This document provides a comprehensive reference for all DOBOT Magician API commands available through the official DobotDLLType.py library. The DOBOT Magician uses a command queue system where commands are queued and then executed in sequence.

### Key Concepts

- **Command Queue**: All movement and control commands are queued and executed sequentially
- **isQueued Parameter**: Most commands have an `isQueued` parameter (0=immediate, 1=queued)
- **Queue Execution**: Commands must be explicitly started with `SetQueuedCmdStartExec()`
- **Coordinate System**: X(forward/back), Y(left/right), Z(up/down), R(rotation)

---

## Connection & Setup

### Basic Connection Pattern

```python
import DobotDLLType as dType

# Load the DLL
api = dType.load()

# Connect to DOBOT (empty string for auto-detect)
state = dType.ConnectDobot(api, "", 115200)[0]

if state == dType.DobotConnect.DobotConnect_NoError:
    print("Connected successfully!")
    
    # Initialize robot parameters
    dType.SetPTPCommonParams(api, 100, 100, isQueued=1)
    dType.SetQueuedCmdStartExec(api)
    
    # Your commands here...
    
    # Disconnect when done
    dType.DisconnectDobot(api)
```

### Connection Commands

| Function | Purpose | Parameters |
|----------|---------|------------|
| `ConnectDobot(api, port, baudrate)` | Connect to DOBOT | port: "" for auto-detect, baudrate: 115200 |
| `DisconnectDobot(api)` | Disconnect from DOBOT | None |
| `SearchDobot(api, maxLen)` | Search for available DOBOT devices | maxLen: buffer size |

---

## Movement Commands

### Point-to-Point (PTP) Movement

#### Basic Movement
```python
# Move to position (X, Y, Z, R)
dType.SetPTPCmd(api, dType.PTPMode.PTPMOVLXYZMode, 200, 0, 150, 0, isQueued=1)
dType.SetQueuedCmdStartExec(api)
```

#### Movement Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| `PTPMOVLXYZMode` | Linear movement in XYZ space | Smooth, straight-line movement |
| `PTPMOVJXYZMode` | Joint movement in XYZ space | Fastest movement, may not be straight |
| `PTPJUMPXYZMode` | Jump movement (arch) | Avoid obstacles, curved path |
| `PTPMOVLANGLEMode` | Linear movement in joint space | Precise joint control |

#### Movement Parameters

```python
# Set velocity and acceleration ratios (1-100%)
dType.SetPTPCommonParams(api, velocityRatio=50, accelerationRatio=50, isQueued=1)

# Set coordinate-specific parameters
dType.SetPTPCoordinateParams(api, 
    xyzVelocity=200,      # mm/s
    rVelocity=200,        # degrees/s
    xyzAcceleration=200,  # mm/s²
    rAcceleration=200,    # degrees/s²
    isQueued=1
)

# Set joint-specific parameters
dType.SetPTPJointParams(api,
    j1Velocity=200, j1Acceleration=200,
    j2Velocity=200, j2Acceleration=200,
    j3Velocity=200, j3Acceleration=200,
    j4Velocity=200, j4Acceleration=200,
    isQueued=1
)
```

### Home Commands

```python
# Set home position
dType.SetHOMEParams(api, x=200, y=0, z=150, r=0, isQueued=1)

# Move to home
dType.SetHOMECmd(api, temp=0, isQueued=1)
dType.SetQueuedCmdStartExec(api)
```

### Continuous Path (CP) Movement

```python
# Set CP parameters
dType.SetCPParams(api,
    planAcc=50,           # Planning acceleration
    juncitionVel=10,     # Junction velocity
    acc=50,              # Acceleration
    realTimeTrack=0,      # Real-time tracking
    isQueued=1
)

# CP movement command
dType.SetCPCmd(api, 
    cpMode=dType.ContinuousPathMode.CPAbsoluteMode,
    x=200, y=0, z=150, velocity=50,
    isQueued=1
)
```

### Arc Movement

```python
# Set arc parameters
dType.SetARCParams(api,
    xyzVelocity=200,
    rVelocity=200,
    xyzAcceleration=200,
    rAcceleration=200,
    isQueued=1
)

# Arc movement (through intermediate point)
cirPoint = [250, 50, 100, 0]  # Intermediate point
toPoint = [300, 0, 150, 0]     # Final point
dType.SetARCCmd(api, cirPoint, toPoint, isQueued=1)
```

### JOG Movement

```python
# Set JOG parameters
dType.SetJOGCommonParams(api, velocityRatio=50, accelerationRatio=50, isQueued=1)

# JOG joint parameters
dType.SetJOGJointParams(api,
    j1Velocity=200, j1Acceleration=200,
    j2Velocity=200, j2Acceleration=200,
    j3Velocity=200, j3Acceleration=200,
    j4Velocity=200, j4Acceleration=200,
    isQueued=1
)

# JOG coordinate parameters
dType.SetJOGCoordinateParams(api,
    xVelocity=200, xAcceleration=200,
    yVelocity=200, yAcceleration=200,
    zVelocity=200, zAcceleration=200,
    rVelocity=200, rAcceleration=200,
    isQueued=1
)

# Execute JOG command
dType.SetJOGCmd(api, isJoint=0, cmd=dType.JC.JogAPPressed, isQueued=1)
```

---

## End Effector Commands

### Suction Cup Control

```python
# Enable/disable suction cup
dType.SetEndEffectorSuctionCup(api, 
    enableCtrl=1,    # 1=enable control
    suck=1,          # 1=suck, 0=release
    isQueued=1
)

# Get suction cup status
status = dType.GetEndEffectorSuctionCup(api)
print(f"Suction cup status: {status}")
```

### Gripper Control

```python
# Open/close gripper
dType.SetEndEffectorGripper(api,
    enableCtrl=1,    # 1=enable control
    grip=1,         # 1=close, 0=open
    isQueued=1
)

# Get gripper status
status = dType.GetEndEffectorGripper(api)
print(f"Gripper status: {status}")
```

### Laser Control

```python
# Turn laser on/off
dType.SetEndEffectorLaser(api,
    enableCtrl=1,    # 1=enable control
    on=1,            # 1=on, 0=off
    isQueued=1
)

# Get laser status
status = dType.GetEndEffectorLaser(api)
print(f"Laser status: {status}")
```

### End Effector Parameters

```python
# Set end effector bias (offset)
dType.SetEndEffectorParams(api,
    xBias=0,    # X offset in mm
    yBias=0,    # Y offset in mm
    zBias=0,    # Z offset in mm
    isQueued=1
)

# Get end effector parameters
params = dType.GetEndEffectorParams(api)
print(f"End effector bias: X={params[0]}, Y={params[1]}, Z={params[2]}")
```

---

## I/O Commands

### Digital Output (DO)

```python
# Set digital output
dType.SetIODO(api, address=1, level=1, isQueued=1)  # Port 1, High

# Get digital output status
level = dType.GetIODO(api, addr=1)
print(f"DO Port 1 level: {level[0]}")
```

### Digital Input (DI)

```python
# Read digital input
level = dType.GetIODI(api, addr=1)
print(f"DI Port 1 level: {level[0]}")
```

### Analog Input (ADC)

```python
# Read analog input
value = dType.GetIOADC(api, addr=1)
print(f"ADC Port 1 value: {value[0]}")
```

### PWM Output

```python
# Set PWM output
dType.SetIOPWM(api,
    address=1,          # Port number
    frequency=1000,     # Frequency in Hz
    dutyCycle=50,       # Duty cycle 0-100%
    isQueued=1
)

# Get PWM parameters
params = dType.GetIOPWM(api, addr=1)
print(f"PWM Port 1: Freq={params[0]}, Duty={params[1]}")
```

### I/O Multiplexing

```python
# Set I/O multiplexing
dType.SetIOMultiplexing(api, address=1, multiplex=1, isQueued=1)

# Get I/O multiplexing
multiplex = dType.GetIOMultiplexing(api, addr=1)
print(f"I/O Port 1 multiplex: {multiplex[0]}")
```

---

## Queue Management

### Essential Queue Commands

```python
# Clear command queue
dType.SetQueuedCmdClear(api)

# Start executing queued commands
dType.SetQueuedCmdStartExec(api)

# Stop executing queued commands
dType.SetQueuedCmdStopExec(api)

# Force stop (emergency)
dType.SetQueuedCmdForceStopExec(api)

# Get current execution index
current_index = dType.GetQueuedCmdCurrentIndex(api)
print(f"Current command index: {current_index[0]}")
```

### Queue Download Commands

```python
# Start downloading commands
dType.SetQueuedCmdStartDownload(api, totalLoop=1, linePerLoop=10)

# Stop downloading
dType.SetQueuedCmdStopDownload(api)
```

---

## Device Information

### Basic Device Info

```python
# Get device serial number
sn = dType.GetDeviceSN(api)
print(f"Device SN: {sn}")

# Get device name
name = dType.GetDeviceName(api)
print(f"Device name: {name}")

# Get device version
version = dType.GetDeviceVersion(api)
print(f"Version: {version[0]}.{version[1]}.{version[2]}")

# Get device time
time = dType.GetDeviceTime(api)
print(f"Device time: {time[0]}")
```

### Pose and Kinematics

```python
# Get current pose
pose = dType.GetPose(api)
print(f"Position: X={pose[0]}, Y={pose[1]}, Z={pose[2]}, R={pose[3]}")
print(f"Joints: J1={pose[4]}, J2={pose[5]}, J3={pose[6]}, J4={pose[7]}")

# Get kinematics
kinematics = dType.GetKinematics(api)
print(f"Velocity: {kinematics[0]}, Acceleration: {kinematics[1]}")

# Get pose with L parameter (for L model)
l_value = dType.GetPoseL(api)
print(f"L parameter: {l_value[0]}")
```

### Device Configuration

```python
# Set device serial number
dType.SetDeviceSN(api, "1234567890")

# Set device name
dType.SetDeviceName(api, "MyDOBOT")

# Set device with L model
dType.SetDeviceWithL(api, isWithL=True)

# Get device with L model status
is_with_l = dType.GetDeviceWithL(api)
print(f"Device with L: {is_with_l}")
```

---

## Advanced Features

### Wait Commands

```python
# Wait for specified time (seconds)
dType.SetWAITCmd(api, waitTime=2.0, isQueued=1)
```

### Trigger Commands

```python
# Set trigger condition
dType.SetTRIGCmd(api,
    address=1,                              # Input address
    mode=dType.TRIGMode.TRIGInputIOMode,    # Trigger mode
    condition=dType.TRIGInputIOCondition.TRIGInputIOEqual,  # Condition
    threshold=1,                            # Threshold value
    isQueued=1
)
```

### External Motor Control

```python
# Control external motor
dType.SetEMotor(api,
    index=1,        # Motor index
    isEnabled=1,    # 1=enabled, 0=disabled
    speed=100,      # Speed value
    isQueued=1
)

# Control external motor with steps
dType.SetEMotorS(api,
    index=1,        # Motor index
    isEnabled=1,    # 1=enabled, 0=disabled
    deltaPulse=1000,  # Step count
    isQueued=1
)
```

### Color Sensor

```python
# Enable color sensor
dType.SetColorSensor(api, isEnable=True)

# Get color sensor values
rgb = dType.GetColorSensor(api)
print(f"Color: R={rgb[0]}, G={rgb[1]}, B={rgb[2]}")
```

### WiFi Configuration

```python
# Set WiFi configuration mode
dType.SetWIFIConfigMode(api, enable=True)

# Set WiFi SSID
dType.SetWIFISSID(api, "MyWiFi")

# Set WiFi password
dType.SetWIFIPassword(api, "password123")

# Set WiFi IP address
dType.SetWIFIIPAddress(api, dhcp=0, addr1=192, addr2=168, addr3=1, addr4=100)

# Get WiFi status
connected = dType.GetWIFIConnectStatus(api)
print(f"WiFi connected: {connected}")
```

---

## Error Handling

### Alarm Management

```python
# Get alarm state
alarms = dType.GetAlarmsState(api, maxLen=1000)
print(f"Alarm state: {alarms[0]}, Length: {alarms[1]}")

# Clear all alarms
dType.ClearAllAlarmsState(api)
```

### Command Timeout

```python
# Set command timeout (milliseconds)
dType.SetCmdTimeout(api, times=5000)
```

### Reset Pose

```python
# Reset pose manually
dType.ResetPose(api, manual=True, rearArmAngle=0, frontArmAngle=0)
```

---

## Code Examples

### Complete Pick and Place Example

```python
import DobotDLLType as dType
import time

def pick_and_place_example():
    # Load and connect
    api = dType.load()
    state = dType.ConnectDobot(api, "", 115200)[0]
    
    if state != dType.DobotConnect.DobotConnect_NoError:
        print("Failed to connect")
        return
    
    try:
        # Initialize parameters
        dType.SetPTPCommonParams(api, 50, 50, isQueued=1)
        dType.SetPTPCoordinateParams(api, 200, 200, 200, 200, isQueued=1)
        
        # Clear queue
        dType.SetQueuedCmdClear(api)
        
        # Pick sequence
        print("Moving to pick position...")
        dType.SetPTPCmd(api, dType.PTPMode.PTPMOVLXYZMode, 250, 50, 50, 0, isQueued=1)
        dType.SetPTPCmd(api, dType.PTPMode.PTPMOVLXYZMode, 250, 50, 30, 0, isQueued=1)
        
        # Activate suction
        print("Activating suction...")
        dType.SetEndEffectorSuctionCup(api, 1, 1, isQueued=1)
        
        # Lift object
        dType.SetPTPCmd(api, dType.PTPMode.PTPMOVLXYZMode, 250, 50, 100, 0, isQueued=1)
        
        # Place sequence
        print("Moving to place position...")
        dType.SetPTPCmd(api, dType.PTPMode.PTPMOVLXYZMode, 200, -50, 100, 0, isQueued=1)
        dType.SetPTPCmd(api, dType.PTPMode.PTPMOVLXYZMode, 200, -50, 30, 0, isQueued=1)
        
        # Release suction
        print("Releasing object...")
        dType.SetEndEffectorSuctionCup(api, 1, 0, isQueued=1)
        
        # Return to safe position
        dType.SetPTPCmd(api, dType.PTPMode.PTPMOVLXYZMode, 200, -50, 100, 0, isQueued=1)
        
        # Start execution
        dType.SetQueuedCmdStartExec(api)
        
        # Wait for completion
        print("Executing sequence...")
        time.sleep(10)  # Adjust based on sequence length
        
        print("Pick and place completed!")
        
    finally:
        dType.DisconnectDobot(api)

if __name__ == "__main__":
    pick_and_place_example()
```

### Safe Movement with Error Handling

```python
def safe_move_to(api, x, y, z, r, timeout=30):
    """Safely move to position with error handling"""
    try:
        # Check for alarms first
        alarms = dType.GetAlarmsState(api)
        if alarms[1] > 0:  # If there are alarms
            print("Clearing alarms...")
            dType.ClearAllAlarmsState(api)
            time.sleep(1)
        
        # Get current position
        current_pose = dType.GetPose(api)
        print(f"Current position: X={current_pose[0]:.2f}, Y={current_pose[1]:.2f}, Z={current_pose[2]:.2f}")
        
        # Queue movement
        dType.SetPTPCmd(api, dType.PTPMode.PTPMOVLXYZMode, x, y, z, r, isQueued=1)
        dType.SetQueuedCmdStartExec(api)
        
        # Wait for completion
        start_time = time.time()
        while time.time() - start_time < timeout:
            current_index = dType.GetQueuedCmdCurrentIndex(api)[0]
            if current_index >= 1:  # Assuming we queued 1 command
                break
            time.sleep(0.1)
        
        # Verify final position
        final_pose = dType.GetPose(api)
        print(f"Final position: X={final_pose[0]:.2f}, Y={final_pose[1]:.2f}, Z={final_pose[2]:.2f}")
        
        return True
        
    except Exception as e:
        print(f"Movement error: {e}")
        dType.SetQueuedCmdStopExec(api)
        return False
```

### I/O Monitoring Example

```python
def monitor_io_example():
    """Monitor I/O ports and respond to inputs"""
    api = dType.load()
    state = dType.ConnectDobot(api, "", 115200)[0]
    
    if state != dType.DobotConnect.DobotConnect_NoError:
        return
    
    try:
        print("Monitoring I/O ports... Press Ctrl+C to stop")
        
        while True:
            # Read digital inputs
            for port in range(1, 5):  # Ports 1-4
                try:
                    di_value = dType.GetIODI(api, port)[0]
                    if di_value == 1:  # Input high
                        print(f"DI Port {port} triggered!")
                        
                        # Respond with output
                        dType.SetIODO(api, port, 1, isQueued=1)
                        dType.SetQueuedCmdStartExec(api)
                        
                        # Wait a bit
                        time.sleep(0.5)
                        
                        # Turn off output
                        dType.SetIODO(api, port, 0, isQueued=1)
                        dType.SetQueuedCmdStartExec(api)
                        
                except:
                    pass  # Ignore read errors
            
            time.sleep(0.1)  # 100ms polling rate
            
    except KeyboardInterrupt:
        print("Stopping monitor...")
    finally:
        dType.DisconnectDobot(api)
```

---

## Troubleshooting

### Common Issues

#### 1. Robot Doesn't Move
**Symptoms:** Commands are sent but robot doesn't move
**Solutions:**
- Check if `SetQueuedCmdStartExec()` is called after queuing commands
- Verify movement parameters are set: `SetPTPCommonParams()`
- Clear alarms: `ClearAllAlarmsState()`
- Check for physical obstructions

#### 2. Connection Failed
**Symptoms:** Cannot connect to DOBOT
**Solutions:**
- Check USB connection and cable
- Verify DOBOT is powered on
- Try different USB port
- Check device permissions (Linux): `sudo usermod -a -G dialout $USER`

#### 3. Commands Not Executing
**Symptoms:** Commands queue but don't execute
**Solutions:**
- Ensure `SetQueuedCmdStartExec()` is called
- Check command queue isn't full
- Verify `isQueued=1` parameter is used
- Clear queue and restart: `SetQueuedCmdClear()`

#### 4. Position Reading Errors
**Symptoms:** `GetPose()` returns incorrect values
**Solutions:**
- Check if robot is in valid position
- Verify coordinate system understanding
- Reset pose if needed: `ResetPose()`

#### 5. End Effector Not Working
**Symptoms:** Suction cup or gripper doesn't respond
**Solutions:**
- Check `enableCtrl=1` parameter
- Verify end effector is properly connected
- Check power supply to end effector
- Test with `GetEndEffectorSuctionCup()` or `GetEndEffectorGripper()`

### Debug Commands

```python
def debug_robot_status(api):
    """Debug robot status and configuration"""
    print("=== Robot Debug Information ===")
    
    # Connection status
    try:
        pose = dType.GetPose(api)
        print(f"✅ Connected - Position: X={pose[0]:.2f}, Y={pose[1]:.2f}, Z={pose[2]:.2f}")
    except:
        print("❌ Not connected")
        return
    
    # Alarm status
    try:
        alarms = dType.GetAlarmsState(api)
        if alarms[1] == 0:
            print("✅ No alarms")
        else:
            print(f"⚠️ Alarms detected: {alarms[1]} bytes")
    except:
        print("❌ Cannot read alarm status")
    
    # Queue status
    try:
        current_index = dType.GetQueuedCmdCurrentIndex(api)[0]
        print(f"📋 Queue index: {current_index}")
    except:
        print("❌ Cannot read queue status")
    
    # Device info
    try:
        version = dType.GetDeviceVersion(api)
        print(f"🔧 Firmware: {version[0]}.{version[1]}.{version[2]}")
    except:
        print("❌ Cannot read device version")
    
    # End effector status
    try:
        suction = dType.GetEndEffectorSuctionCup(api)
        print(f"💨 Suction cup: {suction[0]}")
    except:
        print("❌ Cannot read suction cup status")
    
    try:
        gripper = dType.GetEndEffectorGripper(api)
        print(f"✋ Gripper: {gripper[0]}")
    except:
        print("❌ Cannot read gripper status")

# Usage
debug_robot_status(api)
```

### Performance Optimization

```python
def optimize_robot_performance(api):
    """Optimize robot performance settings"""
    
    # Set optimal movement parameters
    dType.SetPTPCommonParams(api, velocityRatio=80, accelerationRatio=80, isQueued=1)
    
    # Set coordinate parameters for smooth movement
    dType.SetPTPCoordinateParams(api,
        xyzVelocity=300,      # Higher velocity
        rVelocity=300,
        xyzAcceleration=300, # Higher acceleration
        rAcceleration=300,
        isQueued=1
    )
    
    # Set joint parameters
    dType.SetPTPJointParams(api,
        j1Velocity=300, j1Acceleration=300,
        j2Velocity=300, j2Acceleration=300,
        j3Velocity=300, j3Acceleration=300,
        j4Velocity=300, j4Acceleration=300,
        isQueued=1
    )
    
    print("✅ Performance optimization applied")
```

---

## Command Reference Summary

### Essential Commands (Must Know)
- `ConnectDobot()` / `DisconnectDobot()` - Connection
- `SetPTPCmd()` - Movement
- `SetQueuedCmdStartExec()` - Execute commands
- `GetPose()` - Read position
- `SetEndEffectorSuctionCup()` - Control suction
- `SetEndEffectorGripper()` - Control gripper

### Advanced Commands (Power Users)
- `SetPTPCommonParams()` - Movement parameters
- `SetCPCmd()` - Continuous path movement
- `SetARCCmd()` - Arc movement
- `SetIODO()` / `GetIODI()` - I/O control
- `SetWAITCmd()` - Timing control
- `SetTRIGCmd()` - Trigger conditions

### Debug Commands (Troubleshooting)
- `GetAlarmsState()` / `ClearAllAlarmsState()` - Error handling
- `GetQueuedCmdCurrentIndex()` - Queue monitoring
- `GetDeviceVersion()` - Device info
- `ResetPose()` - Position reset

---

## Quick Reference Card

### Essential Commands Cheat Sheet

```python
# === CONNECTION ===
api = dType.load()
state = dType.ConnectDobot(api, "", 115200)[0]
dType.DisconnectDobot(api)

# === MOVEMENT ===
dType.SetPTPCmd(api, dType.PTPMode.PTPMOVLXYZMode, x, y, z, r, isQueued=1)
dType.SetQueuedCmdStartExec(api)  # CRITICAL: Start execution!

# === END EFFECTOR ===
dType.SetEndEffectorSuctionCup(api, 1, 1, isQueued=1)  # Enable suction
dType.SetEndEffectorGripper(api, 1, 1, isQueued=1)     # Close gripper

# === I/O CONTROL ===
dType.SetIODO(api, address=1, level=1, isQueued=1)     # Set DO high
level = dType.GetIODI(api, addr=1)[0]                 # Read DI

# === QUEUE MANAGEMENT ===
dType.SetQueuedCmdClear(api)                          # Clear queue
dType.SetQueuedCmdStartExec(api)                      # Start execution
dType.SetQueuedCmdStopExec(api)                       # Stop execution

# === STATUS READING ===
pose = dType.GetPose(api)                             # Get position
alarms = dType.GetAlarmsState(api)                    # Check alarms
dType.ClearAllAlarmsState(api)                        # Clear alarms
```

### Common Movement Patterns

```python
# === BASIC MOVEMENT ===
def move_to(api, x, y, z, r=0):
    dType.SetPTPCmd(api, dType.PTPMode.PTPMOVLXYZMode, x, y, z, r, isQueued=1)
    dType.SetQueuedCmdStartExec(api)

# === HOME MOVEMENT ===
def home(api):
    dType.SetHOMECmd(api, temp=0, isQueued=1)
    dType.SetQueuedCmdStartExec(api)

# === PICK AND PLACE ===
def pick_and_place(api, pick_x, pick_y, pick_z, place_x, place_y, place_z):
    # Move to pick position
    dType.SetPTPCmd(api, dType.PTPMode.PTPMOVLXYZMode, pick_x, pick_y, pick_z+50, 0, isQueued=1)
    dType.SetPTPCmd(api, dType.PTPMode.PTPMOVLXYZMode, pick_x, pick_y, pick_z, 0, isQueued=1)
    
    # Pick
    dType.SetEndEffectorSuctionCup(api, 1, 1, isQueued=1)
    dType.SetPTPCmd(api, dType.PTPMode.PTPMOVLXYZMode, pick_x, pick_y, pick_z+50, 0, isQueued=1)
    
    # Move to place position
    dType.SetPTPCmd(api, dType.PTPMode.PTPMOVLXYZMode, place_x, place_y, place_z+50, 0, isQueued=1)
    dType.SetPTPCmd(api, dType.PTPMode.PTPMOVLXYZMode, place_x, place_y, place_z, 0, isQueued=1)
    
    # Place
    dType.SetEndEffectorSuctionCup(api, 1, 0, isQueued=1)
    dType.SetPTPCmd(api, dType.PTPMode.PTPMOVLXYZMode, place_x, place_y, place_z+50, 0, isQueued=1)
    
    dType.SetQueuedCmdStartExec(api)
```

### Safety Checklist

- ✅ Always call `SetQueuedCmdStartExec()` after queuing commands
- ✅ Set movement parameters with `SetPTPCommonParams()` before movement
- ✅ Clear alarms with `ClearAllAlarmsState()` if robot doesn't move
- ✅ Check for physical obstructions before movement
- ✅ Use appropriate movement modes (PTPMOVLXYZMode for straight lines)
- ✅ Set reasonable velocity/acceleration ratios (50-80%)
- ✅ Always disconnect when done: `DisconnectDobot(api)`

---

**Document Version:** 1.0  
**Last Updated:** 2025-01-27  
**Compatible with:** DOBOT Magician, Official DobotDLLType.py API
