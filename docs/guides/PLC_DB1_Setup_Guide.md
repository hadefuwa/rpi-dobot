# PLC DB1 Setup Guide

## Problem
Your PLC is connected but the application can't read from **DB1** (Database Block 1), which is where the robot pose data is stored.

## Error Message
```
DB Read timeout after 5000ms - Check if DB1 exists and is accessible (non-optimized)
```

## Solution: Create DB1 on Your S7-1200 PLC

### Step 1: Open TIA Portal
1. Open your Siemens TIA Portal project
2. Navigate to your S7-1200 PLC device

### Step 2: Create DB1
1. In the project tree, right-click on your PLC device
2. Select **"Add new block"** → **"Data block"**
3. Set the following properties:
   - **Name**: `DB1`
   - **Number**: `1`
   - **Type**: `Global DB`
   - **Language**: `DB`

### Step 3: Configure DB1 Structure
Add the following variables to DB1:

```
DB1 (Data Block 1)
├── Target_Position (Struct)
│   ├── X (Real) - Address: 0.0
│   ├── Y (Real) - Address: 4.0  
│   └── Z (Real) - Address: 8.0
├── Current_Position (Struct)
│   ├── X (Real) - Address: 12.0
│   ├── Y (Real) - Address: 16.0
│   └── Z (Real) - Address: 20.0
└── Status (Int) - Address: 24.0
```

**Note**: This setup allows both web app control AND PLC control via Merker bits for maximum flexibility.

### Step 4: Make DB1 Non-Optimized
1. Right-click on **DB1** in the project tree
2. Select **"Properties"**
3. Go to **"Attributes"** tab
4. **Uncheck** "Optimized block access"
5. Click **"OK"**

### Step 5: Download to PLC
1. Compile your project (Ctrl+F7)
2. Download to PLC (Ctrl+F8)
3. Start the PLC

### Step 6: Initialize Values
Add this initialization code to your main program:

```scl
// Initialize DB1 with default values
DB1.Target_Position.X := 0.0;
DB1.Target_Position.Y := 0.0;
DB1.Target_Position.Z := 100.0;

DB1.Current_Position.X := 0.0;
DB1.Current_Position.Y := 0.0;
DB1.Current_Position.Z := 100.0;

DB1.Status := 0; // 0 = Idle

// Initialize Merker bits
M0.0 := FALSE; // Start
M0.1 := FALSE; // Stop  
M0.2 := FALSE; // Home
M0.3 := FALSE; // Emergency Stop
```

## Memory Map Reference

| Address | Variable | Type | Description |
|---------|----------|------|-------------|
| DB1.DBD0 | Target_Position.X | Real | Target X coordinate (mm) |
| DB1.DBD4 | Target_Position.Y | Real | Target Y coordinate (mm) |
| DB1.DBD8 | Target_Position.Z | Real | Target Z coordinate (mm) |
| DB1.DBD12 | Current_Position.X | Real | Current X coordinate (mm) |
| DB1.DBD16 | Current_Position.Y | Real | Current Y coordinate (mm) |
| DB1.DBD20 | Current_Position.Z | Real | Current Z coordinate (mm) |
| DB1.DBW24 | Status | Int | Robot status (0=Idle, 1=Moving, etc.) |

## Control Bits (Merker Memory)

| Address | Variable | Description |
|---------|----------|-------------|
| M0.0 | Start | Start robot movement |
| M0.1 | Stop | Stop robot movement |
| M0.2 | Home | Send robot to home position |
| M0.3 | EStop | Emergency stop |

## Testing
After setting up DB1:
1. Restart your Dobot Gateway application
2. Check the dashboard - PLC should show "Online" with DB1 accessible
3. The PLC Monitor should display pose data instead of errors

## Troubleshooting
- **Still getting timeouts?** Check that DB1 is non-optimized
- **Connection issues?** Verify PLC IP address in .env file
- **Permission errors?** Ensure PLC is in RUN mode and not in STOP mode
