#!/bin/bash
# Quick install script for Raspberry Pi

echo "🤖 Installing PWA Dobot-PLC Control..."
echo ""

# Install system dependencies
echo "📦 Installing system packages..."
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv

# Create virtual environment
echo "🐍 Creating Python virtual environment..."
cd ~/rpi-dobot/pwa-dobot-plc/backend
python3 -m venv venv

# Activate and install Python packages
echo "📚 Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Set up USB permissions
echo "🔐 Setting up USB permissions..."
sudo usermod -a -G dialout $USER

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "⚙️ Creating .env file..."
    cp .env.example .env
    echo ""
    echo "📝 Please edit .env and set your DOBOT_USB_PATH"
    echo "   Run: nano .env"
    echo "   Usually it's /dev/ttyACM1 or /dev/ttyACM0"
    echo ""
fi

# Create logs directory
mkdir -p ~/logs

echo ""
echo "✅ Installation complete!"
echo ""
echo "📋 Next steps:"
echo "  1. Find your Dobot device: ls -la /dev/ttyACM*"
echo "  2. Edit .env: nano .env (set DOBOT_USB_PATH)"
echo "  3. Test the app: source venv/bin/activate && python app.py"
echo "  4. Visit http://your-pi-ip:8080 in your browser"
echo ""
echo "  5. To run with PM2: pm2 start ../deploy/ecosystem.config.js"
echo ""

