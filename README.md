# Dobot Gateway - PWA + Raspberry Pi Gateway for Dobot ↔ S7-1200

A production-ready headless Node.js backend on Raspberry Pi facilitating real-time communication between Dobot Magician (via USB/TCP binary protocol) and Siemens S7-1200 PLC (via Snap7), with a secure PWA frontend for monitoring and control.

## 🚀 Features

- **Real-time Communication**: Binary protocol implementation for Dobot Magician
- **PLC Integration**: Snap7-based communication with Siemens S7-1200
- **Secure PWA**: React-based Progressive Web App with offline capabilities
- **Authentication**: JWT-based security with role-based access control
- **Safety Features**: Emergency stop, command validation, error handling
- **Monitoring**: Comprehensive logging and health checks
- **Production Ready**: PM2/systemd management, HTTPS, log rotation

## 🏗️ Architecture

```
[PWA Client (HTTPS/WSS)]
        ↕ JWT Auth
[Node.js Gateway on Raspberry Pi]
        ↕ Binary Protocol (USB/TCP 29999)
    [Dobot Magician]
        ↕ S7Comm (Snap7)
  [Siemens S7-1200]
```

## 📋 Requirements

- Raspberry Pi 4 (4GB+ RAM recommended)
- Raspberry Pi OS Lite (64-bit)
- Node.js 20 LTS
- 16GB+ SD card
- Dobot Magician robot
- Siemens S7-1200 PLC

## 🚀 Complete Beginner's Setup Guide

This guide will walk you through setting up the Dobot Gateway from start to finish. No prior experience required!

### 📋 What You'll Need

**Hardware:**
- Raspberry Pi 4 (4GB+ RAM recommended)
- 16GB+ microSD card
- Dobot Magician robot
- Siemens S7-1200 PLC
- Ethernet cable or WiFi connection

**Software:**
- Raspberry Pi OS (we'll install this)
- Node.js (we'll install this)
- Git (we'll install this)

### 🎯 Step-by-Step Setup

#### Step 1: Prepare Your Raspberry Pi

**1.1 Flash Raspberry Pi OS**
1. Download [Raspberry Pi Imager](https://www.raspberrypi.org/downloads/)
2. Insert your microSD card
3. Open Raspberry Pi Imager
4. Choose "Raspberry Pi OS Lite (64-bit)"
5. Click "Write" and wait for it to complete

**1.2 Enable SSH (for remote access)**
1. Before ejecting the SD card, create an empty file called `ssh` in the boot partition
2. Create a file called `wpa_supplicant.conf` in the boot partition with your WiFi details:
```
country=US
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1

network={
    ssid="YOUR_WIFI_NAME"
    psk="YOUR_WIFI_PASSWORD"
}
```

**1.3 Boot Your Raspberry Pi**
1. Insert the SD card into your Raspberry Pi
2. Connect power and wait for it to boot
3. Find your Pi's IP address (check your router admin panel or use `nmap`)

#### Step 2: Connect to Your Raspberry Pi

**2.1 SSH Connection (Windows)**
1. Download [PuTTY](https://www.putty.org/)
2. Open PuTTY
3. Enter your Pi's IP address
4. Click "Open"
5. Login with username: `pi`, password: `raspberry`

**2.2 SSH Connection (Mac/Linux)**
```bash
ssh pi@YOUR_PI_IP_ADDRESS
# Default password: raspberry
```

**2.3 Update Your System**
```bash
sudo apt update && sudo apt upgrade -y
```

#### Step 3: Install the Dobot Gateway

**3.1 Clone the Repository**
```bash
git clone https://github.com/hadefuwa/rpi-dobot.git
cd rpi-dobot
```

**3.2 Make Setup Script Executable**
```bash
chmod +x setup.sh
```

**3.3 Run the Automated Setup**
```bash
./setup.sh
```

This script will automatically:
- Install Node.js 20 LTS
- Install PM2 process manager
- Install all required dependencies
- Build the frontend application
- Set up the systemd service
- Configure log directories

**3.4 Wait for Installation**
The setup process takes about 10-15 minutes. You'll see progress messages like:
```
Installing Node.js...
Installing dependencies...
Building frontend...
Setting up services...
```

#### Step 4: Configure Your System

**4.1 Create Environment File**
```bash
nano .env
```

**4.2 Add Your Configuration**
Copy and paste this template, then modify the values:

```bash
# ===========================================
# DOBOT GATEWAY CONFIGURATION
# ===========================================

# Dobot Robot Settings (USB Connection)
DOBOT_HOST=192.168.0.30          # Not used for USB connection
DOBOT_PORT=29999                 # Not used for USB connection  
DOBOT_USE_USB=true               # Set to 'true' for USB connection
DOBOT_USB_PATH=/dev/ttyUSB0      # USB device path (check with: ls /dev/ttyUSB*)

# PLC Settings  
PLC_IP=192.168.0.10              # CHANGE THIS: Your PLC's IP address
PLC_RACK=0                       # Keep this (standard for S7-1200)
PLC_SLOT=1                       # Keep this (standard for S7-1200)

# Security Settings (IMPORTANT!)
JWT_SECRET=your-super-secret-key-change-this-in-production
JWT_EXPIRES_IN=8h
SALT_ROUNDS=12

# Network Settings
NODE_ENV=production
PORT=8080
HTTPS_PORT=443

# Logging
LOG_LEVEL=info
LOG_DIR=/var/log/dobot-gateway
```

**4.3 How to Configure Your Devices**

**Dobot Magician (USB Connection):**
The Dobot Magician connects via USB cable, just like the official Dobot app. You don't need to find an IP address.

**Finding Your Dobot's USB Device Path:**
1. Connect your Dobot to your Raspberry Pi via USB cable
2. Power on your Dobot
3. Check which USB device it appears as:
   ```bash
   ls /dev/ttyUSB*
   # or
   ls /dev/ttyACM*
   ```
4. You should see something like `/dev/ttyUSB0` or `/dev/ttyACM0`
5. Update the `DOBOT_USB_PATH` in your `.env` file with this path

**Finding Your PLC's IP Address:**
1. Connect your S7-1200 to the same network as your Raspberry Pi
2. Use TIA Portal to check the PLC's IP settings
3. Or check your router's admin panel for the PLC device
4. Note the IP address (e.g., 192.168.0.10)

**4.4 Generate a Secure JWT Secret**
```bash
# Generate a secure secret key
node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"
```

Copy the output and replace `your-super-secret-key-change-this-in-production` with it.

**4.5 Save and Exit**
- Press `Ctrl + X` to exit
- Press `Y` to save
- Press `Enter` to confirm

### 🔐 Security Checklist

**Critical Security Requirements:**
- [ ] **Change JWT_SECRET** to a random 32+ character string
- [ ] **Set appropriate expiration** (8h is good for industrial use)
- [ ] **Keep SALT_ROUNDS at 12** (good balance of security/performance)
- [ ] **Never commit secrets** to Git (use .env files)
- [ ] **Use environment variables** for all secrets
- [ ] **Rotate JWT_SECRET** periodically in production

**Generate Secure JWT_SECRET:**
```bash
# Option 1: Online generator
# Visit: https://generate-secret.vercel.app/32

# Option 2: Command line
openssl rand -hex 32

# Option 3: Node.js
node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"
```

**Production Security Configuration:**
```bash
# Example secure configuration
JWT_SECRET=a8f5f167f44f4964e6c998dee827110c  # 32-character random
JWT_EXPIRES_IN=8h                              # 8 hours for industrial
SALT_ROUNDS=12                                 # Secure password hashing
NODE_ENV=production                            # Production mode
```

**Network Settings:**
```bash
# Network Configuration
NODE_ENV=production
PORT=8080                        # HTTP port for development
HTTPS_PORT=443                   # HTTPS port for production
```

**Logging & Performance:**
```bash
# Logging
LOG_LEVEL=info                   # debug, info, warn, error
LOG_DIR=/var/log/dobot-gateway

# Performance
POLL_INTERVAL=100                # PLC polling interval (ms)
MAX_OLD_SPACE_SIZE=512          # Node.js memory limit (MB)
```

#### Configuration Examples

**For USB Connection to Dobot:**
```bash
DOBOT_HOST=192.168.0.30
DOBOT_PORT=29999
DOBOT_USE_USB=true
DOBOT_USB_PATH=/dev/ttyUSB0
```

**For TCP Connection to Dobot:**
```bash
DOBOT_HOST=192.168.0.30
DOBOT_PORT=29999
DOBOT_USE_USB=false
```

**For Different PLC Configuration:**
```bash
PLC_IP=192.168.1.100            # Different PLC IP
PLC_RACK=0                      # Standard rack
PLC_SLOT=2                      # Different slot
```

#### Important Notes

- **Change JWT_SECRET**: Generate a strong secret key for production
- **Network Access**: Ensure Dobot and PLC are accessible from Raspberry Pi
- **Firewall**: Open required ports (29999 for Dobot, 102 for S7Comm)
- **USB Permissions**: If using USB, add user to dialout group: `sudo usermod -a -G dialout pi`
- **USB Device Path**: Check the correct USB path with `ls /dev/ttyACM*` or `ls /dev/ttyUSB*`. Common paths:
  - `/dev/ttyACM0` for Dobot Magician (ACM devices)
  - `/dev/ttyUSB0` for USB-to-Serial adapters
- **Dependencies**: Make sure to install all dependencies:
  - Server: `npm install` in project root
  - Client: `cd client && npm install && npm run build`
- **PM2 Startup**: Enable PM2 to start on boot: `pm2 save && pm2 startup`

#### Step 5: Start the Application

**5.1 Start with PM2 (Recommended)**
```bash
# Start the application
pm2 start ecosystem.config.js

# Check if it's running
pm2 status
```

You should see output like:
```
┌─────┬────────────────┬─────────────┬─────────┬─────────┬──────────┬────────┬──────┬───────────┬──────────┬──────────┬──────────┬──────────┐
│ id  │ name            │ namespace  │ version │ mode    │ pid      │ uptime │ ↺    │ status    │ cpu      │ mem      │ user     │ watching │
├─────┼────────────────┼─────────────┼─────────┼─────────┼──────────┼────────┼──────┼───────────┼──────────┼──────────┼──────────┼──────────┤
│ 0   │ dobot-gateway   │ default     │ 1.0.0   │ fork    │ 1234     │ 0s     │ 0    │ online    │ 0%       │ 45.2mb   │ pi       │ disabled │
└─────┴────────────────┴─────────────┴─────────┴─────────┴──────────┴────────┴──────┴───────────┴──────────┴──────────┴──────────┴──────────┘
```

**5.2 View Application Logs**
```bash
# View real-time logs
pm2 logs dobot-gateway

# View logs without following
pm2 logs dobot-gateway --lines 50
```

**5.3 Check Application Status**
```bash
# Check if the application is running
pm2 status

# Restart if needed
pm2 restart dobot-gateway

# Stop the application
pm2 stop dobot-gateway
```

#### Step 6: Access Your Application

**6.1 Find Your Raspberry Pi's IP Address**
```bash
# Get your Pi's IP address
hostname -I
```

**6.2 Open the Web Interface**
1. Open your web browser
2. Go to: `https://YOUR_PI_IP_ADDRESS` (e.g., `https://192.168.0.100`)
3. You might see a security warning - click "Advanced" and "Proceed to site"

**6.3 Login to the Application**
Use these default credentials:
- **Username**: `admin`
- **Password**: `admin123`

**6.4 Test the Connection**
1. Click on "Connection Status" to see if Dobot and PLC are connected
2. If they show as "Disconnected", check your IP addresses in the `.env` file
3. Make sure your Dobot and PLC are powered on and connected to the network

### 4. Access the Application

Open your browser and navigate to:
- **Production**: `https://raspberrypi.local` or `https://[PI_IP_ADDRESS]`
- **Development**: `http://localhost:8080`

### 5. Default Login Credentials

| Role | Username | Password | Permissions |
|------|----------|----------|------------|
| **Admin** | `admin` | `admin123` | Full control, user management |
| **Operator** | `operator` | `operator123` | Robot control, monitoring |
| **Viewer** | `viewer` | `viewer123` | Read-only access |

⚠️ **Change default passwords in production!**

### 6. Verify Installation

This section shows you exactly how to test that everything is working correctly.

**6.1 Check Service Status:**
```bash
# PM2 status - Should show 'online'
pm2 status

# Expected output:
# ┌────┬──────────────────┬────────┬──────┬───────────┬──────────┬
# │ id │ name             │ status │ ↺    │ cpu      │ mem      │
# ├────┼──────────────────┼────────┼──────┼──────────┼──────────┤
# │ 0  │ dobot-gateway    │ online │ 0    │ 0%       │ 58.9mb   │
# └────┴──────────────────┴────────┴──────┴──────────┴──────────┘

# Check if port 8080 is listening
sudo netstat -tlnp | grep :8080
# OR
lsof -i :8080

# Expected: tcp6 :::8080 :::* LISTEN
```

**6.2 Test HTTP Endpoints (Local on Pi):**
```bash
# Test health endpoint - Should return {"status":"ok"}
curl http://localhost:8080/health

# Example successful response:
# {"status":"ok","timestamp":1761024468620,"uptime":640.106}

# Test Socket.IO endpoint - Should return {"code":0}
curl http://localhost:8080/socket.io/

# Example successful response:
# {"code":0,"message":"Transport unknown"}
```

**6.3 Test Remote Access (From your computer):**
```bash
# Replace 'rpi' with your Pi's IP address if needed
curl http://rpi:8080/health

# Or from Windows PowerShell:
# Invoke-WebRequest -Uri "http://rpi:8080/health"

# Open web browser and navigate to:
# http://rpi:8080
# You should see the Dobot Gateway web interface
```

**6.4 Verify Hardware Connections (Check PM2 Logs):**
```bash
# View application startup logs
pm2 logs dobot-gateway --lines 50

# Look for these SUCCESS messages:
# ✅ "Connected to Dobot via USB at /dev/ttyACM0"
# ✅ "Dobot connected successfully"
# ✅ "Connected to S7-1200 PLC at 192.168.0.99"
# ✅ "Bridge started"
# ✅ "HTTP server running on port 8080"

# Example successful startup:
# info: Connected to Dobot via USB at /dev/ttyACM0
# info: Dobot connected successfully
# info: Connected to S7-1200 PLC at 192.168.0.99
# info: Bridge started
# info: HTTP server running on port 8080
```

**6.5 Complete Test Checklist:**

Run through this checklist to confirm everything works:

- [ ] **App Running**: `pm2 status` shows "online" status
- [ ] **Port Open**: Port 8080 is listening
- [ ] **Health Endpoint**: `curl http://localhost:8080/health` returns OK
- [ ] **Remote Access**: Can access `http://rpi:8080` from another computer
- [ ] **Dobot Connected**: Logs show "Connected to Dobot via USB"
- [ ] **PLC Connected**: Logs show "Connected to S7-1200 PLC"
- [ ] **Bridge Running**: Logs show "Bridge started"
- [ ] **Web Interface**: Browser shows the control panel at `http://rpi:8080`

**6.6 Test from Windows/Mac/Linux Computer:**
```bash
# From your development machine, test connectivity:

# 1. Ping the Raspberry Pi
ping rpi

# 2. Test HTTP access
curl http://rpi:8080/health

# 3. Open web browser
# Navigate to: http://rpi:8080
# You should see the Dobot Gateway login page
```

**6.7 Monitor Real-Time Logs:**
```bash
# View live logs (Press Ctrl+C to stop)
pm2 logs dobot-gateway

# Monitor system resources
pm2 monit

# View specific error logs only
pm2 logs dobot-gateway --err
```

#### Step 7: Troubleshooting Common Issues

**7.1 Application Won't Start**

**Problem**: PM2 shows "errored" status
**Solution**:
```bash
# Check what went wrong
pm2 logs dobot-gateway

# Common fixes:
# 1. Check if .env file exists
ls -la .env

# 2. Check if all dependencies are installed
npm install

# 3. Rebuild the frontend
cd client && npm run build && cd ..

# 4. Restart the application
pm2 restart dobot-gateway
```

**7.2 Can't Access the Web Interface**

**Problem**: Browser shows "This site can't be reached"
**Solution**:
```bash
# 1. Check if the application is running
pm2 status

# 2. Check if the port is open
sudo netstat -tlnp | grep :8080

# 3. Check your Pi's IP address
hostname -I

# 4. Try accessing via IP address instead of hostname
# Go to: https://YOUR_PI_IP_ADDRESS
```

**7.3 Dobot Shows as "Disconnected"**

**Problem**: Dobot connection status is red
**Solution**:
```bash
# 1. Check if your Dobot is powered on and connected via USB
# 2. Check if the USB device is detected
ls /dev/ttyUSB*
ls /dev/ttyACM*

# 3. Verify the USB path in .env file
nano .env
# Make sure DOBOT_USB_PATH matches the device found above

# 4. Check USB permissions
ls -la /dev/ttyUSB*
sudo usermod -a -G dialout $USER
sudo reboot

# 5. Test USB connection (after reboot)
sudo chmod 666 /dev/ttyUSB0  # Replace with your device path
```

**7.4 PLC Shows as "Disconnected"**

**Problem**: PLC connection status is red
**Solution**:
```bash
# 1. Check if your PLC is powered on
# 2. Verify the IP address in .env file
nano .env

# 3. Test network connectivity
ping YOUR_PLC_IP_ADDRESS

# 4. Test the S7Comm port
telnet YOUR_PLC_IP_ADDRESS 102

# 5. Check firewall settings
sudo ufw allow 102
```

**7.5 Login Issues**

**Problem**: Can't login with default credentials
**Solution**:
```bash
# 1. Make sure you're using the correct credentials:
# Username: admin
# Password: admin123

# 2. Check if the application is running
pm2 status

# 3. Check application logs
pm2 logs dobot-gateway

# 4. Try clearing browser cache and cookies
```

**7.6 Performance Issues**

**Problem**: Application is slow or unresponsive
**Solution**:
```bash
# 1. Check memory usage
free -h

# 2. Check CPU usage
top

# 3. Restart the application
pm2 restart dobot-gateway

# 4. Check for memory leaks
pm2 monit
```

**7.7 Log Files and Debugging**

**View Application Logs**:
```bash
# Real-time logs
pm2 logs dobot-gateway

# Last 100 lines
pm2 logs dobot-gateway --lines 100

# Error logs only
pm2 logs dobot-gateway --err
```

**Check System Logs**:
```bash
# System logs
sudo journalctl -u dobot-gateway -f

# Application-specific logs
tail -f /var/log/dobot-gateway/combined.log
```

**7.8 Complete Reset (If Nothing Works)**

**Nuclear Option**:
```bash
# 1. Stop the application
pm2 stop dobot-gateway
pm2 delete dobot-gateway

# 2. Remove all files
cd ..
rm -rf rpi-dobot

# 3. Start over
git clone https://github.com/hadefuwa/rpi-dobot.git
cd rpi-dobot
chmod +x setup.sh
./setup.sh

# 4. Reconfigure
nano .env
# (Add your configuration)

# 5. Restart
pm2 start ecosystem.config.js
```

## 📚 Quick Reference for Beginners

### 🎯 What You Should See When Everything Works

**1. PM2 Status (should show "online"):**
```
┌─────┬────────────────┬─────────────┬─────────┬─────────┬──────────┬────────┬──────┬───────────┬──────────┬──────────┬──────────┬──────────┐
│ id  │ name            │ namespace  │ version │ mode    │ pid      │ uptime │ ↺    │ status    │ cpu      │ mem      │ user     │ watching │
├─────┼────────────────┼─────────────┼─────────┼─────────┼──────────┼────────┼──────┼───────────┼──────────┼──────────┼──────────┼──────────┤
│ 0   │ dobot-gateway   │ default     │ 1.0.0   │ fork    │ 1234     │ 0s     │ 0    │ online    │ 0%       │ 45.2mb   │ pi       │ disabled │
└─────┴────────────────┴─────────────┴─────────┴─────────┴──────────┴────────┴──────┴───────────┴──────────┴──────────┴──────────┴──────────┘
```

**2. Web Interface (should show login page):**
- Go to: `https://YOUR_PI_IP_ADDRESS`
- Login with: `admin` / `admin123`
- You should see the dashboard with connection status

**3. Connection Status (should show green):**
- Dobot: Connected (green)
- PLC: Connected (green)

### 🔧 Essential Commands You'll Need

```bash
# Check if everything is running
pm2 status

# View what's happening (logs)
pm2 logs dobot-gateway

# Restart if something breaks
pm2 restart dobot-gateway

# Stop everything
pm2 stop dobot-gateway

# Start everything
pm2 start ecosystem.config.js

# Check your Pi's IP address
hostname -I

# Edit configuration
nano .env
```

### 🆘 When Things Go Wrong

**Most Common Issues:**
1. **Wrong IP addresses** - Check your `.env` file
2. **Devices not powered on** - Make sure Dobot and PLC are on
3. **Network issues** - Check if devices are on the same network
4. **Application not running** - Check `pm2 status`

**Quick Fixes:**
```bash
# If the application won't start
pm2 restart dobot-gateway

# If you can't access the web interface
hostname -I  # Get your Pi's IP address

# If connections fail
ls /dev/ttyUSB*             # Check if Dobot USB device is detected
ping YOUR_PLC_IP_ADDRESS    # Test PLC connection
```

### 📞 Getting Help

**If you're stuck:**
1. Check the troubleshooting section above
2. Look at the logs: `pm2 logs dobot-gateway`
3. Try the complete reset procedure
4. Check the GitHub issues page

**Useful Information to Include When Asking for Help:**
- Your Raspberry Pi's IP address
- Your Dobot's USB device path (from `ls /dev/ttyUSB*`)
- Your PLC's IP address
- The output of `pm2 status`
- The last few lines of `pm2 logs dobot-gateway`

---

## 🔧 Dobot Magician Protocol Implementation

### Protocol Specification (V1.1.5)

**Packet Structure:**
```
Header (2 bytes): 0xAA 0xAA
Length (1 byte): Payload length + 2
ID (1 byte): Command identifier
Ctrl (1 byte): Bit 0: R/W, Bit 1: IsQueued
Params (N bytes): Command-specific data (little-endian)
Checksum (1 byte): 2's complement of sum(bytes[2:])
```

**Key Commands:**

| Command | ID | Description | Queued |
|---------|----|-----------|----|
| **GetPose** | 0x0A | Read X,Y,Z,R position | No |
| **SetPTPCmd** | 0x54 | Point-to-point movement | Yes |
| **SetHOMECmd** | 0x1F | Home the robot | Yes |
| **SetQueuedCmdClear** | 0xF5 | Clear command queue | No |
| **SetEndEffectorSuctionCup** | 0x3E | Control suction cup | No |

### Node.js Implementation Example

**Packet Building:**
```javascript
function buildPacket(cmdId, ctrl = 0x00, params = Buffer.alloc(0)) {
  const length = params.length + 2;
  const buffer = Buffer.allocUnsafe(5 + params.length);
  
  buffer.writeUInt8(0xAA, 0);  // Header byte 1
  buffer.writeUInt8(0xAA, 1);  // Header byte 2
  buffer.writeUInt8(length, 2); // Length
  buffer.writeUInt8(cmdId, 3);  // Command ID
  buffer.writeUInt8(ctrl, 4);   // Control byte
  
  if (params.length > 0) {
    params.copy(buffer, 5);
  }
  
  // Calculate checksum (2's complement)
  let sum = 0;
  for (let i = 2; i < buffer.length; i++) {
    sum += buffer[i];
  }
  const checksum = (~sum + 1) & 0xFF;
  buffer.writeUInt8(checksum, buffer.length - 1);
  
  return buffer;
}
```

**Command Execution:**
```javascript
// Get robot pose
async function getPose() {
  const packet = buildPacket(0x0A, 0x00);
  const response = await sendCommand(packet);
  return {
    x: response.readFloatLE(0),
    y: response.readFloatLE(4),
    z: response.readFloatLE(8),
    r: response.readFloatLE(12)
  };
}

// Move to position
async function movePTP(x, y, z, r) {
  const params = Buffer.allocUnsafe(17);
  params.writeUInt8(0x01, 0);  // Mode: MOVJ_XYZ
  params.writeFloatLE(x, 1);
  params.writeFloatLE(y, 5);
  params.writeFloatLE(z, 9);
  params.writeFloatLE(r, 13);
  
  const packet = buildPacket(0x54, 0x02, params);
  return await sendCommand(packet);
}
```

### Connection Methods

**TCP Connection (Recommended):**
```bash
DOBOT_HOST=192.168.0.30
DOBOT_PORT=29999
DOBOT_USE_USB=false
```

**USB Serial Connection:**
```bash
DOBOT_USE_USB=true
DOBOT_USB_PATH=/dev/ttyUSB0
# Baud Rate: 115200, Data Bits: 8, Stop Bits: 1, Parity: None
```

## 📊 PLC Memory Mapping

The system uses specific memory addresses in the S7-1200 PLC for communication:

| Address | Type | Description | Access |
|---------|------|-------------|--------|
| **M0.0** | BOOL | Start Dobot Command | Write |
| **M0.1** | BOOL | Stop/Pause Command | Write |
| **M0.2** | BOOL | Reset/Home Command | Write |
| **M0.3** | BOOL | Emergency Stop | Write |
| **DB1.DBD0** | REAL | Target X Position | Write |
| **DB1.DBD4** | REAL | Target Y Position | Write |
| **DB1.DBD8** | REAL | Target Z Position | Write |
| **DB1.DBD12** | REAL | Current X Position | Read |
| **DB1.DBD16** | REAL | Current Y Position | Read |
| **DB1.DBD20** | REAL | Current Z Position | Read |
| **DB1.DBW24** | INT | Status Code | Read |

### S7Comm Protocol Details

- **Port**: 102 (standard S7Comm)
- **Rack/Slot**: Usually 0/1 for S7-1200
- **Data Types**: REAL (32-bit float), BOOL (1-bit), INT (16-bit)
- **Endianness**: Big-endian for S7 data

### Node.js Snap7 Implementation

**PLC Client Setup:**
```javascript
const snap7 = require('node-snap7');

class S7Client {
  constructor(ip = '192.168.0.10', rack = 0, slot = 1) {
    this.ip = ip;
    this.rack = rack;
    this.slot = slot;
    this.client = new snap7.S7Client();
    this.connected = false;
  }

  async connect() {
    return new Promise((resolve, reject) => {
      this.client.ConnectTo(this.ip, this.rack, this.slot, (err) => {
        if (err) {
          reject(new Error(`PLC connection failed: ${err}`));
        } else {
          this.connected = this.client.Connected();
          resolve();
        }
      });
    });
  }

  async readDB(dbNumber, start, size) {
    return new Promise((resolve, reject) => {
      const buffer = Buffer.alloc(size);
      this.client.DBRead(dbNumber, start, size, buffer, (err) => {
        if (err) reject(err);
        else resolve(buffer);
      });
    });
  }

  async writeDB(dbNumber, start, buffer) {
    return new Promise((resolve, reject) => {
      this.client.DBWrite(dbNumber, start, buffer.length, buffer, (err) => {
        if (err) reject(err);
        else resolve();
      });
    });
  }

  // Read Merker bit (e.g., M0.0)
  async readMBit(address) {
    const [byte, bit] = address.split('.');
    const byteNum = parseInt(byte.substring(1));
    
    return new Promise((resolve, reject) => {
      const buffer = Buffer.alloc(1);
      this.client.MBRead(byteNum, 1, buffer, (err) => {
        if (err) reject(err);
        else resolve((buffer[0] >> parseInt(bit)) & 1);
      });
    });
  }

  // Write Merker bit
  async writeMBit(address, value) {
    const [byte, bit] = address.split('.');
    const byteNum = parseInt(byte.substring(1));
    
    // Read-modify-write
    const buffer = Buffer.alloc(1);
    await new Promise((resolve, reject) => {
      this.client.MBRead(byteNum, 1, buffer, (err) => {
        if (err) reject(err);
        else resolve();
      });
    });
    
    if (value) {
      buffer[0] |= (1 << parseInt(bit));
    } else {
      buffer[0] &= ~(1 << parseInt(bit));
    }
    
    return new Promise((resolve, reject) => {
      this.client.MBWrite(byteNum, 1, buffer, (err) => {
        if (err) reject(err);
        else resolve();
      });
    });
  }

  // Parse REAL values (S7 uses big-endian)
  parseReal(buffer, offset) {
    return buffer.readFloatBE(offset);
  }

  encodeReal(value) {
    const buffer = Buffer.allocUnsafe(4);
    buffer.writeFloatBE(value, 0);
    return buffer;
  }
}
```

## 🌉 Bridge Logic Implementation

### PLC ↔ Dobot Coordination

**Bridge Service:**
```javascript
class Bridge {
  constructor(dobot, plc) {
    this.dobot = dobot;
    this.plc = plc;
    this.state = {
      running: false,
      lastStartBit: false,
      lastStopBit: false,
      lastHomeBit: false
    };
    this.pollInterval = 100; // ms
  }

  async start() {
    this.running = true;
    this.poll();
  }

  async poll() {
    if (!this.running) return;

    try {
      // Read PLC commands
      const startBit = await this.plc.readMBit('M0.0');
      const stopBit = await this.plc.readMBit('M0.1');
      const homeBit = await this.plc.readMBit('M0.2');
      const eStopBit = await this.plc.readMBit('M0.3');

      // Emergency stop handling
      if (eStopBit) {
        await this.emergencyStop();
        return;
      }

      // Edge detection for start command
      if (startBit && !this.state.lastStartBit && !this.state.running) {
        const targetBuffer = await this.plc.readDB(1, 0, 12);
        const x = this.plc.parseReal(targetBuffer, 0);
        const y = this.plc.parseReal(targetBuffer, 4);
        const z = this.plc.parseReal(targetBuffer, 8);
        
        await this.dobot.movePTP(x, y, z, 0);
        this.state.running = true;
        await this.plc.writeMBit('M0.0', false); // Reset trigger
      }

      // Stop command
      if (stopBit && !this.state.lastStopBit && this.state.running) {
        await this.dobot.stop();
        this.state.running = false;
        await this.plc.writeMBit('M0.1', false);
      }

      // Home command
      if (homeBit && !this.state.lastHomeBit) {
        await this.dobot.home();
        await this.plc.writeMBit('M0.2', false);
      }

      // Update state tracking
      this.state.lastStartBit = startBit;
      this.state.lastStopBit = stopBit;
      this.state.lastHomeBit = homeBit;

      // Read Dobot pose and write to PLC
      const pose = await this.dobot.getPose();
      const poseBuffer = Buffer.concat([
        this.plc.encodeReal(pose.x),
        this.plc.encodeReal(pose.y),
        this.plc.encodeReal(pose.z)
      ]);
      await this.plc.writeDB(1, 12, poseBuffer);

      // Write status code
      const statusBuffer = Buffer.allocUnsafe(2);
      statusBuffer.writeInt16BE(this.state.running ? 1 : 0, 0);
      await this.plc.writeDB(1, 24, statusBuffer);

    } catch (error) {
      console.error('Bridge error:', error);
    }

    setTimeout(() => this.poll(), this.pollInterval);
  }

  async emergencyStop() {
    console.log('EMERGENCY STOP TRIGGERED');
    await this.dobot.clearQueue();
    this.state.running = false;
    // E-stop bit is already set by PLC
  }
}
```

### Command Flow

1. **PLC → Dobot**: Read M0.0-M0.3 for commands, DB1.DBD0-8 for target position
2. **Dobot → PLC**: Write current pose to DB1.DBD12-20, status to DB1.DBW24
3. **Edge Detection**: Only trigger on rising edge of command bits
4. **State Management**: Track running state and prevent duplicate commands

## 🔌 API Endpoints

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `GET /api/auth/me` - Get current user

### Dobot Control
- `GET /api/dobot/status` - Get Dobot connection status
- `GET /api/dobot/pose` - Get current robot pose
- `POST /api/dobot/home` - Home the robot
- `POST /api/dobot/move` - Move to position
- `POST /api/dobot/stop` - Stop robot movement
- `POST /api/dobot/emergency-stop` - Emergency stop

### PLC Communication
- `GET /api/plc/status` - Get PLC connection status
- `GET /api/plc/read/:address` - Read PLC memory
- `POST /api/plc/write/:address` - Write to PLC memory
- `GET /api/plc/io` - Get all I/O status

### System
- `GET /api/health` - System health check
- `GET /api/status` - Overall system status
- `GET /api/logs` - View system logs

## 🛡️ Security & Authentication

### JWT Implementation

**Token Structure:**
```javascript
{
  "id": "user_id",
  "username": "username", 
  "role": "admin|operator|viewer",
  "iat": 1234567890,
  "exp": 1234597890
}
```

**Role-Based Access Control:**

| Role | Permissions |
|------|------------|
| **Admin** | Full control, user management, system settings |
| **Operator** | Robot control, monitoring, emergency stop |
| **Viewer** | Read-only access, monitoring only |

### HTTPS Configuration

**Self-Signed Certificate (Development):**
```bash
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
```

**Local Trusted Certificate (Recommended):**
```bash
# Install mkcert
npm install -g mkcert
mkcert -install
mkcert raspberrypi.local localhost 127.0.0.1
```

## 🧪 Testing Strategy

### Test Structure

```
tests/
├── unit/
│   ├── dobot.test.js      # Protocol unit tests
│   ├── plc.test.js        # PLC communication tests
│   └── bridge.test.js     # Bridge logic tests
├── integration/
│   ├── api.test.js        # API endpoint tests
│   └── websocket.test.js  # Real-time communication tests
└── e2e/
    └── user-flow.test.js  # End-to-end user scenarios
```

### Running Tests

```bash
# Unit tests
npm run test:unit

# Integration tests  
npm run test:integration

# E2E tests
npm run test:e2e

# All tests
npm test
```

### Test Coverage

- **Unit Tests**: Protocol parsing, command building, data validation
- **Integration Tests**: API endpoints, database operations, external services
- **E2E Tests**: Complete user workflows, browser automation

## 📊 Monitoring & Logging

### Winston Logging Configuration

**Log Levels:**
- `error`: System errors, connection failures
- `warn`: Warnings, retry attempts
- `info`: General information, user actions
- `debug`: Detailed debugging information

**Log Files:**
- `/var/log/dobot-gateway/error.log` - Error logs only
- `/var/log/dobot-gateway/combined.log` - All logs
- Console output for development

### Health Monitoring

**Health Check Endpoint:**
```bash
curl -k https://localhost/api/health
```

**Response Example:**
```json
{
  "uptime": 3600,
  "timestamp": 1234567890,
  "dobot": "connected",
  "plc": "connected", 
  "memory": {
    "rss": 45678912,
    "heapTotal": 12345678,
    "heapUsed": 8765432
  },
  "cpu": {
    "user": 1234567,
    "system": 987654
  }
}
```

### Performance Metrics

**Key Metrics:**
- Connection status (Dobot, PLC)
- Command execution time
- Memory usage
- CPU utilization
- Error rates
- Response times

## 🚨 Safety & Error Handling

### Emergency Stop Implementation

**Hardware E-Stop Integration:**
```javascript
// GPIO pin monitoring for physical E-stop
const eStopPin = new Gpio(17, 'in', 'falling');
eStopPin.watch((err, value) => {
  if (value === 0) {
    emergencyStop();
  }
});
```

**Software E-Stop:**
- Web interface emergency stop button
- API endpoint: `POST /api/dobot/emergency-stop`
- Automatic command queue clearing
- PLC notification via M0.3

### Command Validation

**Position Limits:**
```javascript
const limits = {
  x: { min: -300, max: 300 },
  y: { min: -300, max: 300 }, 
  z: { min: -100, max: 400 },
  r: { min: -180, max: 180 }
};
```

**Safety Features:**
- Position boundary checking
- Speed limit validation
- Command timeout handling
- Connection loss detection
- Automatic reconnection

### Error Recovery

**Automatic Retry Logic:**
- Connection failures: 5 retries with exponential backoff
- Command timeouts: 3 retries with increasing timeout
- Graceful degradation on service failures
- State recovery after reconnection

## ⚡ Performance Optimization

### Node.js Tuning

**Memory Management:**
```bash
# Start with optimized settings
node --max-old-space-size=512 --optimize-for-size server/app.js
```

**Polling Optimization:**
- Configurable poll interval (default: 100ms)
- Adaptive polling based on activity
- Batch operations where possible

### WebSocket Optimization

**Message Compression:**
- Automatic compression for messages > 1KB
- Per-message deflate compression
- Reduced bandwidth usage

**Connection Management:**
- Connection pooling
- Automatic reconnection
- Heartbeat monitoring

## 📱 PWA Implementation

### Progressive Web App Features

**Core PWA Capabilities:**
- **Offline Support**: Service worker caching for offline operation
- **Installable**: Add to home screen on mobile/desktop
- **Responsive**: Works on all device sizes
- **Secure**: HTTPS/WSS required for PWA features

### Frontend Architecture

**React Component Structure:**
```
src/
├── components/
│   ├── Dashboard.jsx          # Main dashboard
│   ├── ConnectionStatus.jsx   # Connection indicators
│   ├── PoseDisplay.jsx        # Robot position display
│   ├── ControlPanel.jsx       # Manual controls
│   ├── PLCMonitor.jsx         # PLC I/O status
│   ├── EmergencyStop.jsx      # E-stop button
│   └── Login.jsx              # Authentication
├── hooks/
│   ├── useAuth.js             # Authentication hook
│   └── useSocket.js           # WebSocket connection
└── services/
    └── api.js                 # API client
```

### Real-Time Communication

**WebSocket Events:**
```javascript
// Server to Client
'dobot-pose-update'     // Robot position changes
'plc-status-update'     // PLC I/O changes
'connection-status'     // Connection state changes
'emergency-stop'        // E-stop triggered

// Client to Server  
'dobot-move'           // Move robot command
'dobot-home'           // Home robot command
'emergency-stop'       // Trigger E-stop
```

### Service Worker Configuration

**Caching Strategy:**
- **Cache First**: Static assets (JS, CSS, images)
- **Network First**: API calls and real-time data
- **Stale While Revalidate**: App shell and components

**Offline Fallback:**
- Cached dashboard for offline viewing
- Connection status indicators
- Emergency stop functionality (if connected)

## 🔧 Manual Installation

### Prerequisites

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install dependencies
sudo apt-get install -y build-essential git curl wget nginx openssl

# Install Node.js 20 LTS
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install PM2
sudo npm install -g pm2
```

### Backend Setup

```bash
# Install dependencies
npm install

# Set up environment
cp .env.example .env
# Edit .env with your configuration

# Create log directory
sudo mkdir -p /var/log/dobot-gateway
sudo chown $USER:$USER /var/log/dobot-gateway
```

### Frontend Setup

```bash
cd client
npm install
npm run build
cd ..
```

### Start the Application

```bash
# Using PM2 (recommended)
pm2 start ecosystem.config.js
pm2 save
pm2 startup

# Or using systemd
sudo systemctl enable dobot-gateway
sudo systemctl start dobot-gateway
```

## 📡 API Documentation

### Authentication

All API endpoints require authentication via JWT token.

```bash
# Login
POST /api/auth/login
{
  "username": "operator",
  "password": "operator123"
}

# Get current user
GET /api/auth/me
```

### Dobot Control

```bash
# Get current pose
GET /api/dobot/pose

# Home robot
POST /api/dobot/home

# Move to position
POST /api/dobot/move
{
  "x": 200,
  "y": 0,
  "z": 100,
  "r": 0
}

# Stop robot
POST /api/dobot/stop

# Control suction cup
POST /api/dobot/suction
{
  "enable": true
}
```

### PLC Control

```bash
# Get PLC pose
GET /api/plc/pose

# Set PLC pose
POST /api/plc/pose
{
  "x": 200,
  "y": 0,
  "z": 100
}

# Get control bits
GET /api/plc/control

# Set control bits
POST /api/plc/control
{
  "start": true,
  "home": false
}
```

### System Status

```bash
# Get system status
GET /api/status

# Health check
GET /api/health

# Emergency stop (no auth required)
POST /api/emergency-stop
```

## 🔒 Security

- JWT-based authentication with HTTP-only cookies
- Role-based access control (admin, operator, viewer)
- HTTPS with self-signed certificates (configurable)
- Input validation and sanitization
- Rate limiting on API endpoints
- CORS protection

## 🧪 Testing

```bash
# Run all tests
npm test

# Run specific test suites
npm run test:unit
npm run test:integration
npm run test:e2e

# Run tests in watch mode
npm run test:watch
```

## 📊 Monitoring

### Logs

```bash
# View application logs
pm2 logs dobot-gateway

# View system logs
sudo journalctl -u dobot-gateway

# View Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Health Checks

- Application health: `GET /api/health`
- System status: `GET /api/status`
- PM2 status: `pm2 status`

### Monitoring Script

```bash
./monitor.sh
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NODE_ENV` | Environment mode | `production` |
| `PORT` | HTTP port | `8080` |
| `DOBOT_HOST` | Dobot IP address | `192.168.0.30` |
| `DOBOT_PORT` | Dobot TCP port | `29999` |
| `DOBOT_USE_USB` | Use USB connection | `false` |
| `PLC_IP` | PLC IP address | `192.168.0.10` |
| `PLC_RACK` | PLC rack number | `0` |
| `PLC_SLOT` | PLC slot number | `1` |
| `JWT_SECRET` | JWT secret key | **Required** |
| `LOG_LEVEL` | Logging level | `info` |

### PLC Memory Map

| Address | Type | Description |
|---------|------|-------------|
| M0.0 | BOOL | Start Dobot Command |
| M0.1 | BOOL | Stop/Pause |
| M0.2 | BOOL | Reset/Home |
| M0.3 | BOOL | Emergency Stop |
| DB1.DBD0 | REAL | Target X Position |
| DB1.DBD4 | REAL | Target Y Position |
| DB1.DBD8 | REAL | Target Z Position |
| DB1.DBD12 | REAL | Current X (feedback) |
| DB1.DBD16 | REAL | Current Y (feedback) |
| DB1.DBD20 | REAL | Current Z (feedback) |
| DB1.DBW24 | INT | Status Code |

## 🚨 Safety Features

- **Emergency Stop**: Hardware and software emergency stop
- **Command Validation**: Range checking for all movements
- **Error Handling**: Comprehensive error recovery
- **Connection Monitoring**: Automatic reconnection
- **Safe Shutdown**: Graceful shutdown procedures

## 🔄 Management Commands

```bash
# Start application
./start.sh

# Stop application
./stop.sh

# Restart application
./restart.sh

# Monitor status
./monitor.sh

# View logs
pm2 logs dobot-gateway

# Restart PM2
pm2 restart dobot-gateway

# Stop PM2
pm2 stop dobot-gateway
```

## 🐛 Troubleshooting

### Common Issues

1. **Connection Refused**
   - Check if the application is running: `pm2 status`
   - Check logs: `pm2 logs dobot-gateway`
   - Verify port availability: `netstat -tlnp | grep :8080`

2. **Dobot Not Connecting**
   - Verify IP address and port in `.env`
   - Check network connectivity: `ping 192.168.0.30`
   - Ensure Dobot is powered on and in TCP mode

3. **PLC Not Connecting**
   - Verify PLC IP address and rack/slot settings
   - Check network connectivity: `ping 192.168.0.10`
   - Ensure PLC is running and accessible

4. **SSL Certificate Issues**
   - Regenerate certificates: `rm certs/* && ./setup.sh`
   - Accept self-signed certificate in browser
   - Check certificate validity: `openssl x509 -in certs/cert.pem -text -noout`

### Log Analysis

```bash
# Application errors
grep "ERROR" /var/log/dobot-gateway/error.log

# Connection issues
grep "connection" /var/log/dobot-gateway/combined.log

# Performance issues
grep "slow" /var/log/dobot-gateway/combined.log
```

## 📈 Performance Tuning

### Node.js Optimization

```bash
# Increase memory limit
node --max-old-space-size=512 server/app.js

# Enable clustering
pm2 start ecosystem.config.js -i max
```

### System Optimization

```bash
# Increase file descriptor limit
echo "* soft nofile 65536" | sudo tee -a /etc/security/limits.conf
echo "* hard nofile 65536" | sudo tee -a /etc/security/limits.conf

# Optimize network settings
echo "net.core.rmem_max = 16777216" | sudo tee -a /etc/sysctl.conf
echo "net.core.wmem_max = 16777216" | sudo tee -a /etc/sysctl.conf
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Add tests for new functionality
5. Run tests: `npm test`
6. Commit changes: `git commit -am 'Add feature'`
7. Push to branch: `git push origin feature-name`
8. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [Wiki](https://github.com/hadefuwa/rpi-dobot/wiki)
- **Issues**: [GitHub Issues](https://github.com/hadefuwa/rpi-dobot/issues)
- **Discussions**: [GitHub Discussions](https://github.com/hadefuwa/rpi-dobot/discussions)

## 🚀 Extensibility & Future Features

### MQTT Integration

**Industrial IoT Connectivity:**
```javascript
const mqtt = require('mqtt');
const client = mqtt.connect('mqtt://broker.local');

// Publish robot status
client.publish('factory/dobot/pose', JSON.stringify(pose));
client.publish('factory/dobot/status', JSON.stringify(status));
```

### Multiple Robot Support

**Multi-Robot Architecture:**
- Support for multiple Dobot robots
- Load balancing across robots
- Coordinated movements
- Individual robot monitoring

### Advanced Monitoring

**Grafana Dashboard Integration:**
- Real-time metrics visualization
- Historical data analysis
- Custom dashboards
- Alerting and notifications

### Machine Learning Integration

**Predictive Maintenance:**
- Robot performance analysis
- Predictive failure detection
- Optimization recommendations
- Usage pattern analysis

## 📈 Production Readiness Checklist

### ✅ Core Features
- [x] Dobot binary protocol implementation
- [x] S7-1200 PLC communication via Snap7
- [x] Real-time WebSocket communication
- [x] JWT authentication with role-based access
- [x] React PWA with offline support
- [x] Emergency stop functionality
- [x] Comprehensive error handling

### ✅ Security
- [x] HTTPS/WSS encryption
- [x] JWT token authentication
- [x] Role-based access control
- [x] Input validation and sanitization
- [x] Secure configuration management

### ✅ Testing
- [x] Unit tests for core functionality
- [x] Integration tests for API endpoints
- [x] E2E tests for user workflows
- [x] Mock services for testing

### ✅ Monitoring
- [x] Winston structured logging
- [x] Health check endpoints
- [x] Performance metrics
- [x] Error tracking and reporting

### ✅ Deployment
- [x] PM2/systemd service management
- [x] Automated setup script
- [x] Environment configuration
- [x] Log rotation and management

## 🙏 Acknowledgments

- **Dobot Technology** for the Magician robot and protocol documentation
- **Siemens** for the S7-1200 PLC and S7Comm protocol
- **Node.js community** for excellent tooling and libraries
- **React team** for the amazing frontend framework
- **Snap7 project** for PLC communication library
- **Socket.io** for real-time communication capabilities
- **The open-source community** for the amazing tools and libraries

---

**⚠️ Safety Notice**: This software controls industrial equipment. Always follow proper safety procedures and ensure adequate training before operation.
