#!/bin/bash

# Find Dobot USB Device Helper Script

echo "=== Finding Dobot USB Device ==="
echo ""

echo "Checking for USB serial devices..."
echo ""

# Check for ttyACM devices
if ls /dev/ttyACM* 2>/dev/null; then
    echo "✅ Found ttyACM devices"
    for device in /dev/ttyACM*; do
        echo "  - $device"
    done
else
    echo "❌ No ttyACM devices found"
fi

echo ""

# Check for ttyUSB devices
if ls /dev/ttyUSB* 2>/dev/null; then
    echo "✅ Found ttyUSB devices"
    for device in /dev/ttyUSB*; do
        echo "  - $device"
    done
else
    echo "❌ No ttyUSB devices found"
fi

echo ""
echo "=== USB Device Information ==="
lsusb

echo ""
echo "=== Dobot is likely one of these devices ==="
echo "Common Dobot USB paths:"
echo "  - /dev/ttyACM0 (most common)"
echo "  - /dev/ttyUSB0"
echo "  - /dev/ttyACM1"
echo ""
echo "To update config, edit: ~/rpi-dobot/config.js"
echo "Or use the Settings page in the web app"

