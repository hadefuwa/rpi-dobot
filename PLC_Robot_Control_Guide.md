# How to Control the Robot via PLC - Complete Programming Guide

## Table of Contents
1. [System Overview](#system-overview)
2. [PLC Programming (Siemens S7-1200)](#plc-programming-siemens-s7-1200)
3. [Robot Arm Programming (Dobot Magician)](#robot-arm-programming-dobot-magician)
4. [Communication Protocol](#communication-protocol)
5. [Memory Mapping](#memory-mapping)
6. [Programming Examples](#programming-examples)
7. [Safety Implementation](#safety-implementation)
8. [Troubleshooting](#troubleshooting)
9. [Best Practices](#best-practices)

---

## System Overview

The Dobot Gateway system creates a bridge between a Siemens S7-1200 PLC and a Dobot Magician robot arm through a Raspberry Pi running Node.js. This architecture allows the PLC to control the robot through standardized memory addresses while maintaining real-time communication.

### Architecture Diagram
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SYSTEM ARCHITECTURE                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐    S7Comm     ┌─────────────────┐    Binary Protocol  │
│  │ Siemens S7-1200 │◄─────────────►│ Raspberry Pi    │◄──────────────────►│
│  │      PLC        │   (Port 102)   │    Gateway      │   (USB/TCP 29999)  │
│  │                 │                │                 │                    │
│  │ Memory Addresses│                │ Node.js Bridge  │                    │
│  │ • M0.0-M0.7     │                │ • Protocol      │                    │
│  │ • DB1.DBD0-26   │                │   Translation   │                    │
│  │ • Control Logic │                │ • Real-time     │                    │
│  │ • Safety Systems│                │   Communication │                    │
│  └─────────────────┘                └─────────────────┘                    │
│           │                                    │                           │
│           │                                    │                           │
│           ▼                                    ▼                           │
│  ┌─────────────────┐                ┌─────────────────┐                    │
│  │   HMI/Operator  │                │   PWA Web       │                    │
│  │   Interface     │                │   Interface     │                    │
│  │                 │                │                 │                    │
│  │ • TIA Portal    │                │ • Real-time     │                    │
│  │ • WinCC         │                │   Monitoring    │                    │
│  │ • Custom HMI    │                │ • Manual Control│                    │
│  └─────────────────┘                └─────────────────┘                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

Communication Flow:
PLC Control Logic → Memory Addresses → Gateway Bridge → Robot Commands
Robot Status ← Memory Addresses ← Gateway Bridge ← Robot Feedback
```

### Key Components
- **PLC**: Central control logic and safety systems
- **Gateway**: Communication bridge and protocol translation
- **Robot**: Physical execution of movements and operations
- **PWA Interface**: Human-machine interface for monitoring and control

---

## PLC Programming (Siemens S7-1200)

### 1. TIA Portal Setup

#### Creating Data Blocks
In TIA Portal, create the following data blocks for robot communication:

**DB1 - Robot Communication Data Block:**
```
DB1:
├── DBD0  : REAL    Target X Position
├── DBD4  : REAL    Target Y Position  
├── DBD8  : REAL    Target Z Position
├── DBD12 : REAL    Current X Position (Read-only)
├── DBD16 : REAL    Current Y Position (Read-only)
├── DBD20 : REAL    Current Z Position (Read-only)
├── DBW24 : INT     Robot Status Code
└── DBW26 : INT     Error Code
```

**Merker Bits (M Memory):**
```
M0.0 : BOOL    Start Robot Command
M0.1 : BOOL    Stop/Pause Command
M0.2 : BOOL    Home/Reset Command
M0.3 : BOOL    Emergency Stop
M0.4 : BOOL    Suction Cup Enable
M0.5 : BOOL    Robot Ready Status (Read-only)
M0.6 : BOOL    Robot Busy Status (Read-only)
M0.7 : BOOL    Robot Error Status (Read-only)
```

### 2. Ladder Logic Programming

#### Main Control Program (OB1)

**Step 1: Emergency Stop Logic**
```ladder
// Emergency Stop - Highest Priority
M0.3 (E-Stop) → [Emergency Stop Handler]
                ↓
            [Stop All Operations]
            [Set Error Status]
            [Disable Robot Commands]
```

**Step 2: Robot Status Monitoring**
```ladder
// Read robot status from gateway
// This is handled automatically by the Node.js bridge
// The PLC only needs to monitor the status bits
```

**Step 3: Command Execution Logic**
```ladder
// Start Command (Edge Detection)
M0.0 AND NOT M0.0_PREV → [Set Target Position]
                         [Trigger Movement]
                         [Reset Start Bit]

// Home Command (Edge Detection)  
M0.2 AND NOT M0.2_PREV → [Execute Home Sequence]
                         [Reset Home Bit]

// Stop Command (Edge Detection)
M0.1 AND NOT M0.1_PREV → [Stop Robot Movement]
                         [Reset Stop Bit]
```

### 3. Structured Text (ST) Programming

#### Robot Control Function Block
```pascal
FUNCTION_BLOCK FB_RobotControl
VAR_INPUT
    Enable : BOOL;
    StartCmd : BOOL;
    StopCmd : BOOL;
    HomeCmd : BOOL;
    EStop : BOOL;
    TargetX : REAL;
    TargetY : REAL;
    TargetZ : REAL;
END_VAR

VAR_OUTPUT
    RobotReady : BOOL;
    RobotBusy : BOOL;
    RobotError : BOOL;
    StatusCode : INT;
END_VAR

VAR
    StartCmd_Prev : BOOL;
    StopCmd_Prev : BOOL;
    HomeCmd_Prev : BOOL;
    EStop_Prev : BOOL;
END_VAR

// Main control logic
IF Enable THEN
    // Emergency stop handling
    IF EStop AND NOT EStop_Prev THEN
        // Emergency stop triggered
        RobotError := TRUE;
        RobotBusy := FALSE;
        // Clear all command bits
        StartCmd := FALSE;
        StopCmd := FALSE;
        HomeCmd := FALSE;
    END_IF;
    
    // Start command edge detection
    IF StartCmd AND NOT StartCmd_Prev AND NOT RobotBusy AND NOT RobotError THEN
        // Set target position in DB1
        "DB1".TargetX := TargetX;
        "DB1".TargetY := TargetY;
        "DB1".TargetZ := TargetZ;
        
        // Trigger movement (handled by gateway)
        RobotBusy := TRUE;
    END_IF;
    
    // Home command edge detection
    IF HomeCmd AND NOT HomeCmd_Prev AND NOT RobotBusy AND NOT RobotError THEN
        // Execute home sequence
        RobotBusy := TRUE;
    END_IF;
    
    // Stop command edge detection
    IF StopCmd AND NOT StopCmd_Prev AND RobotBusy THEN
        // Stop robot movement
        RobotBusy := FALSE;
    END_IF;
    
    // Update previous states
    StartCmd_Prev := StartCmd;
    StopCmd_Prev := StopCmd;
    HomeCmd_Prev := HomeCmd;
    EStop_Prev := EStop;
    
    // Read robot status from DB1
    StatusCode := "DB1".StatusCode;
    RobotReady := (StatusCode = 0);
    RobotError := (StatusCode > 1);
    
END_IF;
```

### 4. Pick and Place Example Program

```pascal
FUNCTION_BLOCK FB_PickAndPlace
VAR_INPUT
    Enable : BOOL;
    PartDetected : BOOL;
    PlacePosition : BOOL;
    EStop : BOOL;
END_VAR

VAR_OUTPUT
    CycleComplete : BOOL;
    ErrorStatus : BOOL;
END_VAR

VAR
    State : INT;
    PickX, PickY, PickZ : REAL;
    PlaceX, PlaceY, PlaceZ : REAL;
    RobotCtrl : FB_RobotControl;
END_VAR

// State machine for pick and place
CASE State OF
    0: // Idle state
        IF Enable AND PartDetected AND NOT EStop THEN
            State := 1; // Move to pick position
        END_IF;
        
    1: // Move to pick position
        PickX := 200.0;
        PickY := 0.0;
        PickZ := 50.0;
        
        RobotCtrl(
            Enable := TRUE,
            StartCmd := TRUE,
            TargetX := PickX,
            TargetY := PickY,
            TargetZ := PickZ
        );
        
        IF RobotCtrl.RobotReady THEN
            State := 2; // Pick the part
        END_IF;
        
    2: // Pick the part
        // Enable suction cup
        M0.4 := TRUE;
        
        // Wait for pickup confirmation
        IF PartDetected = FALSE THEN
            State := 3; // Move to place position
        END_IF;
        
    3: // Move to place position
        PlaceX := 100.0;
        PlaceY := 100.0;
        PlaceZ := 50.0;
        
        RobotCtrl(
            Enable := TRUE,
            StartCmd := TRUE,
            TargetX := PlaceX,
            TargetY := PlaceY,
            TargetZ := PlaceZ
        );
        
        IF RobotCtrl.RobotReady THEN
            State := 4; // Place the part
        END_IF;
        
    4: // Place the part
        // Disable suction cup
        M0.4 := FALSE;
        
        // Wait for placement confirmation
        IF PlacePosition THEN
            State := 5; // Return to home
        END_IF;
        
    5: // Return to home
        RobotCtrl(
            Enable := TRUE,
            HomeCmd := TRUE
        );
        
        IF RobotCtrl.RobotReady THEN
            State := 0; // Cycle complete
            CycleComplete := TRUE;
        END_IF;
        
END_CASE;

// Error handling
IF EStop OR RobotCtrl.RobotError THEN
    State := 0;
    ErrorStatus := TRUE;
    CycleComplete := FALSE;
END_IF;
```

---

## Robot Arm Programming (Dobot Magician)

### 1. Binary Protocol Implementation

The Dobot Magician uses a binary protocol for communication. Here's how the gateway handles robot programming:

#### Packet Structure
```javascript
// Packet format: [Header][Length][ID][Ctrl][Params][Checksum]
// Header: 0xAA 0xAA
// Length: Payload length + 2
// ID: Command identifier
// Ctrl: Control byte (bit 0: R/W, bit 1: IsQueued)
// Params: Command-specific data (little-endian)
// Checksum: 2's complement of sum(bytes[2:])
```

#### Key Commands
```javascript
const COMMANDS = {
    GET_POSE: 0x0A,           // Read current position
    SET_PTP_CMD: 0x54,        // Point-to-point movement
    SET_HOME_CMD: 0x1F,       // Home the robot
    SET_QUEUED_CMD_CLEAR: 0xF5, // Clear command queue
    SET_END_EFFECTOR_SUCTION_CUP: 0x3E, // Control suction cup
    GET_STATUS: 0x10          // Get robot status
};
```

### 2. Movement Programming

#### Basic Movement Function
```javascript
async function moveToPosition(x, y, z, r = 0) {
    // Validate coordinates
    validateCoordinates(x, y, z, r);
    
    // Build movement parameters
    const params = Buffer.allocUnsafe(17);
    params.writeUInt8(0x01, 0);  // Mode: MOVJ_XYZ
    params.writeFloatLE(x, 1);
    params.writeFloatLE(y, 5);
    params.writeFloatLE(z, 9);
    params.writeFloatLE(r, 13);
    
    // Send command
    const response = await sendCommand(0x54, 0x02, params);
    return response.queuedIndex;
}
```

#### Pick and Place Sequence
```javascript
async function pickAndPlace(pickPos, placePos) {
    try {
        // 1. Move to pick position
        await moveToPosition(pickPos.x, pickPos.y, pickPos.z + 50);
        await moveToPosition(pickPos.x, pickPos.y, pickPos.z);
        
        // 2. Enable suction cup
        await setSuctionCup(true);
        
        // 3. Move up
        await moveToPosition(pickPos.x, pickPos.y, pickPos.z + 50);
        
        // 4. Move to place position
        await moveToPosition(placePos.x, placePos.y, placePos.z + 50);
        await moveToPosition(placePos.x, placePos.y, placePos.z);
        
        // 5. Disable suction cup
        await setSuctionCup(false);
        
        // 6. Move up
        await moveToPosition(placePos.x, placePos.y, placePos.z + 50);
        
        // 7. Return to home
        await home();
        
    } catch (error) {
        console.error('Pick and place failed:', error);
        await emergencyStop();
        throw error;
    }
}
```

### 3. Safety and Error Handling

#### Emergency Stop Implementation
```javascript
async function emergencyStop() {
    try {
        // Clear command queue immediately
        await clearQueue();
        
        // Update status
        await updateStatus(5); // Emergency stop status
        
        // Emit emergency stop event
        this.emit('emergency_stop');
        
    } catch (error) {
        console.error('Emergency stop failed:', error);
    }
}
```

#### Coordinate Validation
```javascript
function validateCoordinates(x, y, z, r) {
    const limits = {
        x: { min: -300, max: 300 },
        y: { min: -300, max: 300 },
        z: { min: -100, max: 400 },
        r: { min: -180, max: 180 }
    };

    if (x < limits.x.min || x > limits.x.max) {
        throw new Error(`X position ${x} out of range [${limits.x.min}, ${limits.x.max}]`);
    }
    // Similar validation for y, z, r...
}
```

---

## Communication Protocol

### 1. S7Comm Protocol (PLC ↔ Gateway)

The gateway uses the S7Comm protocol to communicate with the Siemens S7-1200 PLC:

#### Reading Data from PLC
```javascript
// Read control bits
const controlBits = await plc.getControlBits();
// Returns: { start: boolean, stop: boolean, home: boolean, estop: boolean }

// Read target position
const targetPose = await plc.readPoseFromDB(1, 0);
// Returns: { x: number, y: number, z: number }
```

#### Writing Data to PLC
```javascript
// Write current position
await plc.writePoseToDB(currentPose, 1, 12);

// Write status code
await plc.writeStatusToDB(statusCode, 1, 24);

// Write control bits
await plc.setControlBits({ start: false, home: false });
```

### 2. Binary Protocol (Gateway ↔ Robot)

The gateway communicates with the Dobot using a binary protocol:

#### Command Execution
```javascript
async function sendCommand(cmdId, ctrl, params, timeout = 2000) {
    const packet = buildPacket(cmdId, ctrl, params);
    const commandId = ++this.commandId;
    
    return new Promise((resolve, reject) => {
        const timer = setTimeout(() => {
            reject(new Error(`Command ${cmdId} timeout`));
        }, timeout);
        
        this.responseHandlers.set(commandId, { resolve, reject, timer, cmdId });
        
        if (this.useUSB) {
            this.port.write(packet);
        } else {
            this.socket.write(packet);
        }
    });
}
```

---

## Memory Mapping

### PLC Memory Layout

| Address | Type | Description | Access | Example |
|---------|------|-------------|--------|---------|
| **M0.0** | BOOL | Start Robot Command | Write | `TRUE` to start movement |
| **M0.1** | BOOL | Stop/Pause Command | Write | `TRUE` to stop robot |
| **M0.2** | BOOL | Home/Reset Command | Write | `TRUE` to home robot |
| **M0.3** | BOOL | Emergency Stop | Write | `TRUE` for emergency stop |
| **M0.4** | BOOL | Suction Cup Enable | Write | `TRUE` to enable suction |
| **M0.5** | BOOL | Robot Ready Status | Read | `TRUE` when robot ready |
| **M0.6** | BOOL | Robot Busy Status | Read | `TRUE` when robot moving |
| **M0.7** | BOOL | Robot Error Status | Read | `TRUE` when error occurs |
| **DB1.DBD0** | REAL | Target X Position | Write | `200.5` (mm) |
| **DB1.DBD4** | REAL | Target Y Position | Write | `0.0` (mm) |
| **DB1.DBD8** | REAL | Target Z Position | Write | `100.0` (mm) |
| **DB1.DBD12** | REAL | Current X Position | Read | `200.3` (mm) |
| **DB1.DBD16** | REAL | Current Y Position | Read | `0.1` (mm) |
| **DB1.DBD20** | REAL | Current Z Position | Read | `99.8` (mm) |
| **DB1.DBW24** | INT | Status Code | Read | `0` = Ready, `1` = Busy, `2` = Error |
| **DB1.DBW26** | INT | Error Code | Read | `0` = No Error, `1` = Position Error |

### Status Codes

| Code | Description | Meaning |
|------|-------------|---------|
| **0** | Ready | Robot is ready for commands |
| **1** | Busy | Robot is executing a command |
| **2** | Error | Robot has encountered an error |
| **3** | Homing | Robot is performing home sequence |
| **4** | Stopped | Robot movement has been stopped |
| **5** | Emergency Stop | Emergency stop is active |

---

## Programming Examples

### 1. Simple Pick and Place Program

#### PLC Side (Ladder Logic)
```ladder
// Network 1: Part Detection and Start Command
I0.0 (Part Sensor) AND NOT M0.6 (Robot Busy) → M0.0 (Start Command)

// Network 2: Set Pick Position
M0.0 → [MOV] 200.0 → DB1.DBD0 (Target X)
M0.0 → [MOV] 0.0 → DB1.DBD4 (Target Y)  
M0.0 → [MOV] 50.0 → DB1.DBD8 (Target Z)

// Network 3: Set Place Position (after pick)
M0.5 (Robot Ready) AND M0.0 → [MOV] 100.0 → DB1.DBD0 (Target X)
M0.5 (Robot Ready) AND M0.0 → [MOV] 100.0 → DB1.DBD4 (Target Y)
M0.5 (Robot Ready) AND M0.0 → [MOV] 50.0 → DB1.DBD8 (Target Z)

// Network 4: Suction Cup Control
M0.5 (Robot Ready) → M0.4 (Suction Cup Enable)

// Network 5: Emergency Stop
I0.1 (E-Stop Button) → M0.3 (Emergency Stop)
```

#### Gateway Side (Node.js)
```javascript
// Bridge service handles the communication automatically
// The PLC writes to memory addresses, and the gateway:
// 1. Reads the control bits
// 2. Executes the corresponding robot commands
// 3. Updates the status and position feedback
```

### 2. Complex Assembly Sequence

#### PLC Side (Structured Text)
```pascal
PROGRAM Main
VAR
    AssemblyState : INT;
    Part1Detected : BOOL;
    Part2Detected : BOOL;
    AssemblyComplete : BOOL;
    RobotCtrl : FB_RobotControl;
END_VAR

// State machine for assembly process
CASE AssemblyState OF
    0: // Wait for parts
        IF Part1Detected AND Part2Detected THEN
            AssemblyState := 1;
        END_IF;
        
    1: // Pick first part
        RobotCtrl(
            Enable := TRUE,
            StartCmd := TRUE,
            TargetX := 150.0,
            TargetY := 0.0,
            TargetZ := 30.0
        );
        
        IF RobotCtrl.RobotReady THEN
            AssemblyState := 2;
        END_IF;
        
    2: // Place first part on assembly fixture
        RobotCtrl(
            Enable := TRUE,
            StartCmd := TRUE,
            TargetX := 100.0,
            TargetY := 100.0,
            TargetZ := 20.0
        );
        
        IF RobotCtrl.RobotReady THEN
            AssemblyState := 3;
        END_IF;
        
    3: // Pick second part
        RobotCtrl(
            Enable := TRUE,
            StartCmd := TRUE,
            TargetX := 200.0,
            TargetY := 0.0,
            TargetZ := 30.0
        );
        
        IF RobotCtrl.RobotReady THEN
            AssemblyState := 4;
        END_IF;
        
    4: // Assemble parts
        RobotCtrl(
            Enable := TRUE,
            StartCmd := TRUE,
            TargetX := 100.0,
            TargetY := 100.0,
            TargetZ := 25.0
        );
        
        IF RobotCtrl.RobotReady THEN
            AssemblyState := 5;
        END_IF;
        
    5: // Assembly complete
        AssemblyComplete := TRUE;
        AssemblyState := 0;
        
END_CASE;
```

### 3. Quality Control with Vision

#### PLC Side
```pascal
// Vision system integration
IF VisionSystem.PartDetected THEN
    // Check part quality
    IF VisionSystem.QualityOK THEN
        // Good part - proceed with normal handling
        RobotCtrl.StartCmd := TRUE;
        RobotCtrl.TargetX := VisionSystem.PartX;
        RobotCtrl.TargetY := VisionSystem.PartY;
        RobotCtrl.TargetZ := VisionSystem.PartZ;
    ELSE
        // Defective part - move to reject area
        RobotCtrl.StartCmd := TRUE;
        RobotCtrl.TargetX := RejectArea.X;
        RobotCtrl.TargetY := RejectArea.Y;
        RobotCtrl.TargetZ := RejectArea.Z;
    END_IF;
END_IF;
```

---

## Safety Implementation

### 1. Emergency Stop System

#### Hardware E-Stop
```ladder
// Emergency stop circuit
I0.1 (E-Stop Button) → M0.3 (Emergency Stop)
M0.3 → [NOT] → All Robot Commands
M0.3 → [NOT] → All Conveyor Motors
M0.3 → [NOT] → All Pneumatic Valves
```

#### Software E-Stop
```javascript
// Gateway emergency stop handling
async function handleEmergencyStop() {
    try {
        // Stop robot immediately
        await dobot.clearQueue();
        
        // Update PLC status
        await plc.writeStatusToDB(5, 1); // Emergency stop status
        
        // Disable all robot commands
        await plc.setControlBits({
            start: false,
            stop: false,
            home: false
        });
        
        // Emit emergency stop event
        this.emit('emergency_stop');
        
    } catch (error) {
        logger.error('Emergency stop failed:', error);
    }
}
```

### 2. Safety Monitoring

#### Position Limits
```javascript
function validateCoordinates(x, y, z, r) {
    const limits = {
        x: { min: -300, max: 300 },
        y: { min: -300, max: 300 },
        z: { min: -100, max: 400 },
        r: { min: -180, max: 180 }
    };

    // Check each coordinate
    if (x < limits.x.min || x > limits.x.max) {
        throw new Error(`X position ${x} out of safe range`);
    }
    // Similar checks for y, z, r...
}
```

#### Collision Detection
```javascript
// Monitor robot position for potential collisions
function checkCollisionZone(currentPose) {
    const collisionZones = [
        { x: { min: 0, max: 50 }, y: { min: 0, max: 50 }, z: { min: 0, max: 100 } },
        // Define other collision zones...
    ];
    
    for (const zone of collisionZones) {
        if (isInZone(currentPose, zone)) {
            throw new Error('Collision zone detected');
        }
    }
}
```

---

## Troubleshooting

### Common Issues and Solutions

#### 1. Robot Not Responding to PLC Commands

**Symptoms:**
- PLC sets start bit but robot doesn't move
- Status shows robot as not ready

**Solutions:**
```javascript
// Check gateway connection status
console.log('Dobot connected:', dobot.connected);
console.log('PLC connected:', plc.isConnected());

// Check memory mapping
const controlBits = await plc.getControlBits();
console.log('Control bits:', controlBits);

// Verify robot status
const robotStatus = await dobot.getStatus();
console.log('Robot status:', robotStatus);
```

#### 2. Communication Timeouts

**Symptoms:**
- Commands timeout after 2 seconds
- Intermittent connection issues

**Solutions:**
```javascript
// Increase timeout for complex operations
const response = await dobot.sendCommand(0x54, 0x02, params, 5000);

// Implement retry logic
async function sendCommandWithRetry(cmdId, params, maxRetries = 3) {
    for (let i = 0; i < maxRetries; i++) {
        try {
            return await dobot.sendCommand(cmdId, 0x02, params);
        } catch (error) {
            if (i === maxRetries - 1) throw error;
            await delay(1000);
        }
    }
}
```

#### 3. Position Feedback Issues

**Symptoms:**
- PLC shows incorrect robot position
- Position updates are delayed

**Solutions:**
```javascript
// Check pose update frequency
const pose = await dobot.getPose();
console.log('Current pose:', pose);

// Verify data conversion
const poseBuffer = Buffer.concat([
    plc.encodeReal(pose.x),
    plc.encodeReal(pose.y),
    plc.encodeReal(pose.z)
]);
console.log('Encoded pose:', poseBuffer);

// Check PLC write operation
await plc.writePoseToDB(pose, 1, 12);
const readBack = await plc.readPoseFromDB(1, 12);
console.log('Read back pose:', readBack);
```

### Debugging Tools

#### 1. PLC Debugging
```pascal
// Add debug outputs in TIA Portal
// Monitor memory addresses in real-time
// Use force values for testing
```

#### 2. Gateway Debugging
```javascript
// Enable debug logging
logger.level = 'debug';

// Monitor bridge status
setInterval(() => {
    const status = bridge.getStatus();
    console.log('Bridge status:', status);
}, 1000);

// Check communication timing
const startTime = Date.now();
await dobot.getPose();
const endTime = Date.now();
console.log(`Pose read took ${endTime - startTime}ms`);
```

#### 3. Robot Debugging
```javascript
// Check robot connection
if (!dobot.connected) {
    console.log('Attempting to reconnect...');
    await dobot.connect();
}

// Verify command queue
const status = await dobot.getStatus();
console.log('Command queue index:', status.queuedCmdIndex);
console.log('Robot idle:', status.isIdle);
```

---

## Best Practices

### 1. Programming Guidelines

#### PLC Programming
- **Use edge detection** for command bits to prevent repeated execution
- **Implement proper error handling** with status codes
- **Use structured programming** with function blocks for complex logic
- **Test thoroughly** in simulation before deployment

#### Robot Programming
- **Validate all coordinates** before sending movement commands
- **Implement proper error handling** with try-catch blocks
- **Use queued commands** for smooth motion sequences
- **Monitor robot status** continuously

### 2. Safety Guidelines

#### Hardware Safety
- **Install emergency stops** at multiple locations
- **Use safety-rated components** for critical functions
- **Implement proper grounding** and shielding
- **Regular safety inspections** and maintenance

#### Software Safety
- **Validate all inputs** before processing
- **Implement timeout mechanisms** for all operations
- **Use proper error codes** for different failure modes
- **Log all safety events** for analysis

### 3. Performance Optimization

#### Communication Optimization
```javascript
// Batch multiple operations
const operations = [
    () => plc.readMBit('M0.0'),
    () => plc.readMBit('M0.1'),
    () => plc.readMBit('M0.2'),
    () => plc.readMBit('M0.3')
];
const results = await Promise.all(operations);
```

#### Memory Management
```javascript
// Clear old command handlers
setInterval(() => {
    const now = Date.now();
    for (const [id, handler] of responseHandlers) {
        if (now - handler.timestamp > 30000) {
            handler.reject(new Error('Handler timeout'));
            responseHandlers.delete(id);
        }
    }
}, 5000);
```

### 4. Maintenance and Monitoring

#### Regular Maintenance
- **Check connections** weekly
- **Update software** as needed
- **Monitor logs** for errors
- **Test emergency stops** monthly

#### Performance Monitoring
```javascript
// Monitor system performance
const performance = {
    commandLatency: [],
    errorRate: 0,
    uptime: process.uptime()
};

// Track command execution times
const startTime = Date.now();
await executeCommand();
const executionTime = Date.now() - startTime;
performance.commandLatency.push(executionTime);
```

---

## Step-by-Step Implementation Guide

### Phase 1: Hardware Setup

#### 1.1 Connect the Hardware
```
1. Power on the Siemens S7-1200 PLC
2. Connect the Dobot Magician robot arm
3. Connect the Raspberry Pi to the network
4. Verify all connections using the web interface
```

#### 1.2 Configure Network Settings
```bash
# On Raspberry Pi, edit the configuration
nano .env

# Set your specific IP addresses
PLC_IP=192.168.0.10          # Your PLC's IP address
DOBOT_HOST=192.168.0.30      # Your robot's IP (if using TCP)
DOBOT_USB_PATH=/dev/ttyUSB0  # USB device path (if using USB)
```

### Phase 2: PLC Programming

#### 2.1 Create Data Blocks in TIA Portal
```
1. Open TIA Portal
2. Create new project or open existing
3. Add new Data Block (DB1)
4. Configure memory addresses as shown in Memory Mapping section
5. Compile and download to PLC
```

#### 2.2 Write Control Logic
```
1. Create new Function Block (FB_RobotControl)
2. Implement the control logic using Ladder Logic or ST
3. Add safety functions (emergency stop, limits)
4. Test in simulation mode first
5. Download to PLC
```

### Phase 3: Gateway Configuration

#### 3.1 Start the Gateway Service
```bash
# Start the gateway service
pm2 start ecosystem.config.js

# Check status
pm2 status

# View logs
pm2 logs dobot-gateway
```

#### 3.2 Verify Connections
```bash
# Check PLC connection
curl http://localhost:8080/api/plc/status

# Check robot connection  
curl http://localhost:8080/api/dobot/status

# Check overall system status
curl http://localhost:8080/api/status
```

### Phase 4: Testing and Validation

#### 4.1 Basic Functionality Test
```
1. Open web interface: http://YOUR_PI_IP:8080
2. Login with admin credentials
3. Check connection status (should show green)
4. Test manual robot movement
5. Test emergency stop functionality
```

#### 4.2 PLC Integration Test
```
1. Set M0.0 (Start bit) in PLC
2. Verify robot moves to target position
3. Check status feedback in PLC
4. Test stop and home commands
5. Verify emergency stop works
```

### Phase 5: Production Deployment

#### 5.1 Safety Verification
```
1. Test all emergency stops
2. Verify position limits work
3. Check error handling
4. Validate safety interlocks
5. Document safety procedures
```

#### 5.2 Performance Optimization
```
1. Adjust polling intervals
2. Optimize communication timing
3. Monitor system performance
4. Set up logging and monitoring
5. Create maintenance procedures
```

---

## Quick Reference Cards

### PLC Memory Quick Reference
```
Control Bits (M Memory):
M0.0 = Start Robot    M0.4 = Suction Cup
M0.1 = Stop Robot     M0.5 = Robot Ready
M0.2 = Home Robot     M0.6 = Robot Busy  
M0.3 = Emergency Stop M0.7 = Robot Error

Position Data (DB1):
DB1.DBD0-8   = Target Position (X,Y,Z)
DB1.DBD12-20 = Current Position (X,Y,Z)
DB1.DBW24    = Status Code
DB1.DBW26    = Error Code
```

### Robot Commands Quick Reference
```
Basic Commands:
- Home: Set M0.2 = TRUE
- Move: Set target position + M0.0 = TRUE
- Stop: Set M0.1 = TRUE
- Emergency: Set M0.3 = TRUE

Status Codes:
0 = Ready, 1 = Busy, 2 = Error, 3 = Homing, 4 = Stopped, 5 = E-Stop
```

### Troubleshooting Quick Reference
```
Problem: Robot not responding
Solution: Check M0.5 (Robot Ready) and M0.7 (Robot Error)

Problem: Position not updating
Solution: Check DB1.DBD12-20 values and gateway logs

Problem: Communication timeout
Solution: Check network connectivity and restart gateway service
```

---

## Conclusion

This guide provides a comprehensive overview of how to control the Dobot Magician robot arm via a Siemens S7-1200 PLC through the Raspberry Pi gateway. The system uses standardized memory addresses for communication, making it easy to integrate into existing PLC programs.

Key points to remember:
1. **PLC programming** uses standard IEC 61131-3 languages with memory-mapped communication
2. **Robot programming** uses binary protocol commands for precise control
3. **Safety systems** are critical and must be implemented at both hardware and software levels
4. **Proper testing** and debugging are essential for reliable operation
5. **Regular maintenance** ensures long-term system reliability

For additional support or questions, refer to the main README.md file or check the troubleshooting section above.
