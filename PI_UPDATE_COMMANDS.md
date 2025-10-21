# Raspberry Pi Update Commands

## Quick Update & Restart

```bash
# Navigate to project directory
cd ~/rpi-dobot

# Pull latest changes from GitHub
git pull origin main

# Check if server is running
pm2 status

# If server is NOT running, start it:
pm2 start ecosystem.config.js

# If server IS running, restart it:
pm2 restart dobot-gateway

# Watch logs in real-time
pm2 logs dobot-gateway
```

## First Time Setup (if PM2 process doesn't exist)

```bash
cd ~/rpi-dobot

# Install dependencies (if needed)
npm install

# Start the server with PM2
pm2 start ecosystem.config.js

# Save PM2 process list
pm2 save

# Set PM2 to start on system boot
pm2 startup

# Check status
pm2 status
```

## Troubleshooting

### Server Not Found
```bash
# Check what PM2 processes are running
pm2 list

# If nothing is running, start the server
pm2 start ecosystem.config.js

# If wrong process name, delete all and restart
pm2 delete all
pm2 start ecosystem.config.js
```

### View Logs
```bash
# Live logs (press Ctrl+C to exit)
pm2 logs dobot-gateway

# Last 100 lines
pm2 logs dobot-gateway --lines 100

# Only errors
pm2 logs dobot-gateway --err
```

### Check Server Status
```bash
# PM2 status
pm2 status

# Detailed monitoring
pm2 monit

# Check if port 8080 is listening
sudo netstat -tlnp | grep :8080

# Test health endpoint
curl http://localhost:8080/health
```

## Manual Start (without PM2)

If PM2 isn't working, you can start the server manually:

```bash
cd ~/rpi-dobot
npm start
```

Press Ctrl+C to stop when running manually.
