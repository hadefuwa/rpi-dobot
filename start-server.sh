#!/bin/bash

echo "=== Dobot Gateway Startup Script ==="
echo ""

# Kill any existing processes on port 8080
echo "1. Killing existing processes on port 8080..."
sudo lsof -ti:8080 | xargs -r sudo kill -9
pkill -9 node 2>/dev/null
sleep 2

# Check for Dobot USB device
echo ""
echo "2. Checking for Dobot USB device..."
if [ -e "/dev/ttyACM0" ]; then
    echo "✅ Found Dobot at /dev/ttyACM0"
elif [ -e "/dev/ttyUSB0" ]; then
    echo "✅ Found USB device at /dev/ttyUSB0"
    echo "⚠️  Update config.js to use /dev/ttyUSB0"
else
    echo "❌ No USB device found at /dev/ttyACM0 or /dev/ttyUSB0"
    echo ""
    echo "Running USB device finder..."
    ./find-dobot-usb.sh
    echo ""
    read -p "Press Enter to continue anyway or Ctrl+C to cancel..."
fi

# Start the server
echo ""
echo "3. Starting server..."
npm start

