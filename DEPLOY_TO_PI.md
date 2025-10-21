# 🚀 Deploy Python PWA to Raspberry Pi

## Quick Start Guide

### 1️⃣ Pull Latest Code on Your Pi

```bash
cd ~/rpi-dobot
git pull origin main
```

### 2️⃣ Run the Installation Script

```bash
cd ~/rpi-dobot/pwa-dobot-plc/deploy
chmod +x install.sh start.sh
./install.sh
```

This will:
- ✅ Install Python dependencies
- ✅ Create virtual environment
- ✅ Set up USB permissions
- ✅ Create .env file

### 3️⃣ Find Your Dobot USB Device

```bash
ls -la /dev/ttyACM*
ls -la /dev/ttyUSB*
```

You should see something like `/dev/ttyACM1` or `/dev/ttyACM0`.

### 4️⃣ Configure the .env File

```bash
cd ~/rpi-dobot/pwa-dobot-plc/backend
nano .env
```

Set these values:
```bash
DOBOT_USB_PATH=/dev/ttyACM1  # <-- Change this to your device
PLC_IP=192.168.0.150          # Your PLC IP
PORT=8080                      # Web server port
```

Save with `Ctrl+X`, then `Y`, then `Enter`.

### 5️⃣ Test the App

```bash
cd ~/rpi-dobot/pwa-dobot-plc/backend
source venv/bin/activate
python app.py
```

Visit `http://your-pi-ip:8080` in your browser!

You should see:
- 🤖 Beautiful gradient UI with emojis
- 📊 PLC Data (DB1)
- 🦾 Dobot Position
- 🎛️ Control Bits
- 🕹️ Manual Control buttons

### 6️⃣ Stop Any Old Apps First

```bash
# Stop all PM2 processes
pm2 stop all
pm2 delete all

# Kill any processes on port 8080
sudo lsof -ti:8080 | xargs -r sudo kill -9
```

### 7️⃣ Run with PM2 (Auto-Start on Boot)

```bash
cd ~/rpi-dobot/pwa-dobot-plc
pm2 start deploy/ecosystem.config.js

# Save PM2 config
pm2 save

# Set to start on boot (if not already done)
pm2 startup
# Run the command it gives you (with sudo)

# Check status
pm2 status
pm2 logs pwa-dobot-plc
```

## 🎯 What You'll See

The app will show:
- **Green dots** when PLC and Dobot are connected
- **Red dots** when disconnected
- **Real-time data** updating every 2 seconds
- **Control bits** with ON/OFF status
- **Manual control buttons**:
  - 🏠 **Home** - Send robot home
  - ▶️ **Move to Target** - Move to PLC coordinates
  - 🛑 **Emergency Stop** - Stop everything

## 📱 Install as PWA

On your phone:
1. Open `http://your-pi-ip:8080`
2. Tap "Share" → "Add to Home Screen"
3. Launch like a native app!

## 🔧 Troubleshooting

### USB Permission Denied

```bash
sudo usermod -a -G dialout $USER
newgrp dialout
```

Log out and back in, then try again.

### Port Already in Use

```bash
# Find what's using port 8080
sudo lsof -i :8080

# Kill it
sudo lsof -ti:8080 | xargs -r sudo kill -9
```

### PLC Not Connecting

```bash
# Test network connection
ping 192.168.0.150

# Check PLC IP in .env
nano ~/rpi-dobot/pwa-dobot-plc/backend/.env
```

### Check Logs

```bash
# If running with PM2
pm2 logs pwa-dobot-plc

# If running manually, check terminal output
```

## ✅ Verification Checklist

- [ ] Git pull completed
- [ ] Install script ran successfully
- [ ] Found Dobot USB device
- [ ] Updated .env with correct DOBOT_USB_PATH
- [ ] Stopped old PM2 processes
- [ ] Started new PM2 process
- [ ] Can access web UI at http://pi-ip:8080
- [ ] PLC shows green dot (connected)
- [ ] Dobot shows green dot (connected)
- [ ] Manual controls work

## 🎉 Done!

Your Python PWA app with emojis is now running!

Visit: **http://your-pi-ip:8080**

Enjoy! 🚀

