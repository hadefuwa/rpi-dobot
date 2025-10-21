# PWA Dobot-PLC Control

A Progressive Web App for controlling Dobot Magician robot via Siemens S7-1200 PLC communication.

## Features

- ✅ **Working S7 Communication** - Uses python-snap7 (proven to work with your PLC)
- 📱 **Progressive Web App** - Install on any device, works offline
- 🔄 **Real-time Updates** - WebSocket connection for live PLC data
- 🤖 **Dobot Control** - Move robot, home, emergency stop
- 📊 **Live Dashboard** - View PLC control bits and position data
- 🌐 **Multi-device** - Access from phone, tablet, computer

## Architecture

```
pwa-dobot-plc/
├── backend/              # Python Flask API
│   ├── app.py           # Main Flask application with WebSocket
│   ├── plc_client.py    # S7 PLC communication (python-snap7)
│   ├── dobot_client.py  # Dobot USB communication
│   └── requirements.txt # Python dependencies
├── frontend/            # PWA Frontend
│   ├── index.html       # Single-page app
│   ├── manifest.json    # PWA manifest
│   └── sw.js           # Service Worker for offline
└── deploy/             # Deployment scripts
    ├── setup.sh        # Setup script
    ├── start.sh        # Start script
    └── ecosystem.config.js  # PM2 configuration
```

## PLC Memory Map

### DB1 - Position Data (REAL values)
```
DB1.DBD0   : REAL  - Target X (PLC writes, App reads)
DB1.DBD4   : REAL  - Target Y
DB1.DBD8   : REAL  - Target Z
DB1.DBD12  : REAL  - Current X (App writes, PLC reads)
DB1.DBD16  : REAL  - Current Y
DB1.DBD20  : REAL  - Current Z
```

### M Memory - Control Bits (BOOL values)
```
M0.0 : Start Robot Command
M0.1 : Stop/Pause Command
M0.2 : Home/Reset Command
M0.3 : Emergency Stop
M0.4 : Suction Cup Enable
M0.5 : Robot Ready Status
M0.6 : Robot Busy Status
M0.7 : Robot Error Status
```

## Installation on Raspberry Pi

### Quick Setup

```bash
# Clone or copy the pwa-dobot-plc folder to your Raspberry Pi
cd ~/
git clone <your-repo-url> pwa-dobot-plc
cd pwa-dobot-plc

# Run setup script
chmod +x deploy/setup.sh
chmod +x deploy/start.sh
./deploy/setup.sh

# Edit .env file with your PLC IP
nano backend/.env
```

### Environment Configuration

Edit `backend/.env`:

```bash
# PLC Settings
PLC_IP=192.168.0.150      # Your PLC IP address
PLC_RACK=0
PLC_SLOT=1

# Dobot Settings
DOBOT_USE_USB=true
DOBOT_USB_PATH=/dev/ttyACM0  # USB device path for Dobot

# Server Settings
PORT=8080
```

### Install Dependencies

```bash
cd backend
pip3 install -r requirements.txt
```

Required packages:
- `python-snap7` - S7 PLC communication (proven working)
- `flask` - Web server
- `flask-socketio` - WebSocket support
- `flask-cors` - CORS handling
- `pydobot` - Dobot robot control (optional)

### Create PWA Icons

Simple colored icons will be created automatically if ImageMagick is installed.
Or manually create:
- `frontend/icon-192.png` (192x192 pixels)
- `frontend/icon-512.png` (512x512 pixels)

### Running the Application

#### Option 1: Direct Python
```bash
./deploy/start.sh
```

#### Option 2: Using PM2 (recommended for production)
```bash
pm2 start deploy/ecosystem.config.js
pm2 save
pm2 startup  # Enable auto-start on boot
```

### Accessing the PWA

1. **On Raspberry Pi:** http://localhost:8080
2. **On same network:** http://<pi-ip-address>:8080
3. **Install as PWA:** Open in Chrome/Edge → Menu → "Install App"

## API Endpoints

### PLC Control
- `GET  /api/plc/status` - Get PLC connection status
- `POST /api/plc/connect` - Connect to PLC
- `GET  /api/plc/pose` - Read target pose from PLC
- `POST /api/plc/pose` - Write current pose to PLC
- `GET  /api/plc/control` - Read all control bits
- `POST /api/plc/control/<bit>` - Set control bit

### Dobot Control
- `GET  /api/dobot/status` - Get Dobot status
- `POST /api/dobot/connect` - Connect to Dobot
- `POST /api/dobot/home` - Home robot
- `POST /api/dobot/move` - Move to position
- `GET  /api/dobot/pose` - Get current position

### Emergency
- `POST /api/emergency-stop` - Emergency stop all systems

### WebSocket Events

**Client → Server:**
- `start_polling` - Start real-time data polling
- `stop_polling` - Stop polling

**Server → Client:**
- `plc_data` - PLC control bits and target pose (100ms interval)
- `dobot_data` - Current robot position (100ms interval)

## TIA Portal PLC Configuration

### IMPORTANT: Enable S7 Communication

1. Open TIA Portal
2. Select your PLC (CPU 1214C DC/DC/DC)
3. Go to **Properties** → **Protection & Security** → **Connection mechanisms**
4. **CHECK:** ☑ **Permit access with PUT/GET communication from remote partner**
5. Download configuration to PLC

### DB1 Configuration

DB1 must be **non-optimized** for external access:

1. Right-click DB1 → **Properties**
2. **Attributes** tab
3. **UNCHECK:** ☐ **Optimized block access**
4. Download DB1 to PLC

## Why Python-Snap7 Instead of Node-Snap7?

Your existing Node.js implementation was failing because:
1. node-snap7 has compatibility issues with S7-1200
2. Connection timeouts even when PUT/GET was enabled
3. M-memory reads were unreliable

**python-snap7 works because:**
- ✅ Direct bindings to official snap7 library
- ✅ Proven compatibility with S7-1200/1500
- ✅ Your working example already uses it successfully
- ✅ More stable and actively maintained

## Troubleshooting

### PLC Not Connecting

1. **Check network:** `ping 192.168.0.150`
2. **Verify PUT/GET enabled** in TIA Portal
3. **Check DB1 is non-optimized**
4. **Check firewall** on Pi and PLC network

### Dobot Not Connecting

1. **Check USB connection:** `ls /dev/ttyACM*`
2. **Verify permissions:** `sudo chmod 666 /dev/ttyACM0`
3. **Check pydobot installed:** `pip3 list | grep pydobot`

### PWA Not Installing

1. **Use HTTPS** or localhost (PWA requirement)
2. **Check manifest.json** is accessible
3. **Ensure icons exist**

## Development

### Testing Backend Only

```bash
cd backend
python3 app.py
```

Then open http://localhost:8080/api/health

### Testing PLC Connection

```bash
cd backend
python3 -c "from plc_client import PLCClient; plc = PLCClient('192.168.0.150'); print('Connected' if plc.connect() else 'Failed')"
```

### Monitoring Logs

```bash
# PM2 logs
pm2 logs pwa-dobot-plc --lines 100

# Direct run with verbose logging
cd backend
python3 app.py
```

## Deployment to Multiple Pis

1. **Setup Git repository:**
```bash
cd ~/pwa-dobot-plc
git init
git add .
git commit -m "Initial PWA setup"
git push origin main
```

2. **On each new Pi:**
```bash
git clone <repo-url> pwa-dobot-plc
cd pwa-dobot-plc
./deploy/setup.sh
# Edit backend/.env for specific Pi settings
pm2 start deploy/ecosystem.config.js
pm2 save
```

## License

MIT

## Credits

- Uses proven python-snap7 library from your working example
- Flask backend for reliability and simplicity
- Progressive Web App for cross-device compatibility
