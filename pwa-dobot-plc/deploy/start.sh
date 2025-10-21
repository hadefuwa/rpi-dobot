#!/bin/bash
# Quick start script for development testing

cd ~/rpi-dobot/pwa-dobot-plc/backend

# Activate virtual environment
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "   Run: ./deploy/install.sh first"
    exit 1
fi

source venv/bin/activate

# Check for .env file
if [ ! -f .env ]; then
    echo "⚠️ .env file not found! Creating from example..."
    cp .env.example .env
    echo "📝 Please edit .env and set your DOBOT_USB_PATH"
    exit 1
fi

# Start the server
echo "🚀 Starting PWA Dobot-PLC Control..."
echo "📡 Server will be available at http://$(hostname -I | awk '{print $1}'):8080"
echo "   Press Ctrl+C to stop"
echo ""

python app.py

