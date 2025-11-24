# Git Deployment Commands

## Push to GitHub (Windows)
```bash
cd C:\Users\HamedA\Documents\rpi-dobot
git add .
git commit -m "Your change description"
git push
```

## SSH to Pi (Windows)
```bash
ssh pi@rpi
```
Password: `1`

## Pull on Pi
```bash
cd ~/rpi-dobot
git pull
pm2 restart pwa-dobot-plc
```
