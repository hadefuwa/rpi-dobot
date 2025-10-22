# 🚀 Deploy Python PWA to Raspberry Pi

## Quick Start Guide

### 1️⃣ Pull Latest Code on Your Pi

```bash
cd ~/rpi-dobot
git pull origin main
```

### 2️⃣ Install System Dependencies

```bash
# Install system packages
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv build-essential

# Install Snap7 library (for PLC communication)
cd ~
wget https://sourceforge.net/projects/snap7/files/1.4.2/snap7-full-1.4.2.tar.gz
tar -zxvf snap7-full-1.4.2.tar.gz
cd snap7-full-1.4.2/build/unix
make -f arm_v7_linux.mk  # For Raspberry Pi 3/4
sudo cp ../bin/arm_v7-linux/libsnap7.so /usr/lib/
sudo ldconfig
```

### 3️⃣ Set Up Python Virtual Environment

```bash
cd ~/rpi-dobot/pwa-dobot-plc/backend
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install Python dependencies
pip install -r requirements.txt
```

This installs:
- ✅ Flask (web server)
- ✅ Flask-SocketIO (real-time updates)
- ✅ python-snap7 (PLC communication)
- ✅ pydobot (Dobot control)
- ✅ pyserial (USB communication)

### 4️⃣ Set Up USB Permissions

```bash
# Add your user to dialout group
sudo usermod -a -G dialout $USER

# Log out and back in, or run:
newgrp dialout
```

### 5️⃣ Find Your Dobot USB Device

```bash
ls -la /dev/ttyACM*
ls -la /dev/ttyUSB*
```

You should see something like `/dev/ttyACM1` or `/dev/ttyACM0`.

### 6️⃣ Configure the .env File

```bash
cd ~/rpi-dobot/pwa-dobot-plc/backend
nano .env
```

Set these values:
```bash
DOBOT_USB_PATH=/dev/ttyACM1  # <-- Change this to your device
PLC_IP=192.168.1.150          # Your PLC IP
PORT=8080                      # Web server port
```

Save with `Ctrl+X`, then `Y`, then `Enter`.

### 7️⃣ Test the App

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

### 8️⃣ Stop Any Old Apps First

```bash
# Stop all PM2 processes
pm2 stop all
pm2 delete all

# Kill any processes on port 8080
sudo lsof -ti:8080 | xargs -r sudo kill -9
```

### 9️⃣ Run with PM2 (Auto-Start on Boot)

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
ping 192.168.1.150

# Check PLC IP in .env
nano ~/rpi-dobot/pwa-dobot-plc/backend/.env
```

### Flask Not Installed / Module Not Found

If you get `ModuleNotFoundError: No module named 'flask'`:

```bash
# Make sure virtual environment is activated
cd ~/rpi-dobot/pwa-dobot-plc/backend
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt
```

### Snap7 Library Issues

If you get errors about `snap7` or `libsnap7.so`:

```bash
# Verify Snap7 is installed
ls -la /usr/lib/libsnap7.so

# If not found, reinstall Snap7
cd ~
wget https://sourceforge.net/projects/snap7/files/1.4.2/snap7-full-1.4.2.tar.gz
tar -zxvf snap7-full-1.4.2.tar.gz
cd snap7-full-1.4.2/build/unix
make -f arm_v7_linux.mk
sudo cp ../bin/arm_v7-linux/libsnap7.so /usr/lib/
sudo ldconfig

# Then reinstall python-snap7
cd ~/rpi-dobot/pwa-dobot-plc/backend
source venv/bin/activate
pip install --force-reinstall python-snap7
```

### Check Logs

```bash
# If running with PM2
pm2 logs pwa-dobot-plc

# If running manually, check terminal output
```

## ✅ Verification Checklist

- [ ] Git pull completed
- [ ] System dependencies installed (Snap7 library)
- [ ] Virtual environment created
- [ ] Python packages installed (Flask, etc.)
- [ ] USB permissions configured
- [ ] Found Dobot USB device
- [ ] Updated .env with correct DOBOT_USB_PATH
- [ ] App runs without errors (`python app.py`)
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

