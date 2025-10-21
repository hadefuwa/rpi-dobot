# 🤖 PWA Dobot-PLC Control

Beautiful Progressive Web App for controlling Dobot Magician robot via Siemens S7-1200 PLC.

## ✨ Features

- 📱 **Progressive Web App** - Install on any device, works offline
- 🎯 **Real-time Monitoring** - Live PLC data and Dobot position
- 🕹️ **Manual Control** - Direct robot control from web interface
- 🛑 **Emergency Stop** - Quick safety shutdown
- 📊 **Control Bits Display** - Monitor PLC control signals
- 🎨 **Beautiful UI** - Modern, gradient design with emoji indicators

## 🚀 Installation on Raspberry Pi

### 1. Clone the repository
```bash
cd ~
git clone https://github.com/hadefuwa/rpi-dobot.git
cd rpi-dobot/pwa-dobot-plc/backend
```

### 2. Install Python dependencies
```bash
# Install system packages
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python packages
pip install -r requirements.txt
```

### 3. Configure Dobot USB permissions
```bash
# Add your user to dialout group
sudo usermod -a -G dialout $USER

# Log out and back in, or run:
newgrp dialout

# Find your Dobot device
ls -la /dev/ttyACM*
```

### 4. Configure settings
```bash
# Copy and edit .env file
cp .env.example .env
nano .env
```

Update these values:
- `DOBOT_USB_PATH` - Your Dobot device (usually `/dev/ttyACM1`)
- `PLC_IP` - Your PLC IP address (usually `192.168.0.150`)

### 5. Test the application
```bash
# Make sure you're in the virtual environment
source venv/bin/activate

# Run the server
python app.py
```

Visit `http://your-pi-ip:8080` in your browser!

### 6. Set up PM2 for auto-start
```bash
# Install PM2 globally
npm install -g pm2

# Create PM2 ecosystem file
cd ~/rpi-dobot/pwa-dobot-plc
```

Create `ecosystem.config.js`:
```javascript
module.exports = {
  apps: [{
    name: 'pwa-dobot-plc',
    cwd: '/home/pi/rpi-dobot/pwa-dobot-plc/backend',
    script: 'venv/bin/python',
    args: 'app.py',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '200M',
    env: {
      NODE_ENV: 'production'
    }
  }]
};
```

```bash
# Start with PM2
pm2 start ecosystem.config.js

# Save PM2 config
pm2 save

# Set PM2 to start on boot
pm2 startup
# Run the command it gives you (with sudo)

# Check status
pm2 status
pm2 logs pwa-dobot-plc
```

## 🎮 Usage

1. **Open the app** - Navigate to `http://your-pi-ip:8080`
2. **Check connections** - Green dots indicate PLC and Dobot are connected
3. **Monitor data** - See real-time PLC targets and Dobot position
4. **Manual control**:
   - 🏠 **Home** - Send robot to home position
   - ▶️ **Move to Target** - Move robot to PLC target coordinates
   - 🛑 **Emergency Stop** - Immediately stop all movement

## 📱 Install as PWA

On **mobile devices**:
1. Open in Safari (iOS) or Chrome (Android)
2. Tap "Share" → "Add to Home Screen"
3. Launch like a native app!

On **desktop**:
1. Open in Chrome
2. Click the install icon in address bar
3. Use as standalone app!

## 🔧 Troubleshooting

### Dobot not connecting
```bash
# Check USB device
ls -la /dev/ttyACM*
ls -la /dev/ttyUSB*

# Check permissions
groups  # Should include 'dialout'

# Try different device path in .env
DOBOT_USB_PATH=/dev/ttyACM0  # or /dev/ttyACM1
```

### PLC not connecting
```bash
# Test network connection
ping 192.168.0.150

# Check PLC IP in .env
PLC_IP=192.168.0.150
```

### Port already in use
```bash
# Find and kill process on port 8080
sudo lsof -ti:8080 | xargs -r sudo kill -9

# Or change port in .env
PORT=8081
```

## 📋 PLC Memory Map

### DB1 (Data Block)
- **DBD0-11**: Target Position (X, Y, Z) - REAL values

### Merkers (M Memory)
- **M0.0**: Start movement
- **M0.1**: Stop
- **M0.2**: Home
- **M0.3**: Emergency stop
- **M0.4**: Suction cup
- **M0.5**: Ready status
- **M0.6**: Busy status
- **M0.7**: Error status

## 🎨 Features

- ✅ Real-time data updates (2s polling)
- ✅ Offline support (PWA)
- ✅ Mobile-friendly responsive design
- ✅ Auto-reconnect on disconnect
- ✅ Beautiful gradient UI
- ✅ Emoji indicators for status
- ✅ Emergency stop with confirmation

## 📝 License

MIT - Feel free to use and modify!

## 🙏 Credits

- Flask & Flask-SocketIO - Web framework
- python-snap7 - PLC communication
- pydobot - Dobot robot control

