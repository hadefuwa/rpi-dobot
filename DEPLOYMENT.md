# Quick Deployment Guide

## Copy to Raspberry Pi

### Method 1: Using Git (Recommended)

```bash
# On your Windows machine, push to GitHub
cd pwa-dobot-plc
git remote add origin https://github.com/YOUR_USERNAME/pwa-dobot-plc.git
git push -u origin master

# On Raspberry Pi
ssh pi@rpi
cd ~
git clone https://github.com/YOUR_USERNAME/pwa-dobot-plc.git
cd pwa-dobot-plc
```

### Method 2: Direct Copy via SCP

```bash
# On Windows (from rpi-dobot directory)
scp -r pwa-dobot-plc pi@rpi:~/
```

## Installation Steps on Pi

```bash
# 1. Navigate to project
cd ~/pwa-dobot-plc

# 2. Make scripts executable
chmod +x deploy/setup.sh
chmod +x deploy/start.sh

# 3. Run setup
./deploy/setup.sh

# 4. Configure your PLC IP
nano backend/.env
# Change PLC_IP=192.168.0.150 to your PLC IP
# Save: Ctrl+O, Enter, Ctrl+X

# 5. Copy .env.example to .env
cp backend/.env.example backend/.env

# 6. Start with PM2
pm2 start deploy/ecosystem.config.js
pm2 save
pm2 startup

# 7. Check status
pm2 status
pm2 logs pwa-dobot-plc
```

## Access the App

- **On Pi:** http://localhost:8080
- **On your phone/computer:** http://192.168.0.XXX:8080 (use Pi's IP)

## Install as PWA on Phone

1. Open Chrome on Android or Safari on iPhone
2. Go to http://PI_IP:8080
3. Tap menu (⋮ or share icon)
4. Select "Add to Home Screen" or "Install App"
5. App will work offline!

## Updating

```bash
ssh pi@rpi
cd ~/pwa-dobot-plc
git pull
pm2 restart pwa-dobot-plc
```

## Troubleshooting

### Check if running
```bash
pm2 status
curl http://localhost:8080/api/health
```

### View logs
```bash
pm2 logs pwa-dobot-plc --lines 50
```

### Restart
```bash
pm2 restart pwa-dobot-plc
```

### Full reinstall
```bash
cd ~/pwa-dobot-plc
pm2 delete pwa-dobot-plc
./deploy/setup.sh
pm2 start deploy/ecosystem.config.js
pm2 save
```
