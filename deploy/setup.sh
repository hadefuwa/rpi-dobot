#!/bin/bash
# Setup script for PWA Dobot-PLC Control on Raspberry Pi

set -e  # Exit on error

echo "🚀 Setting up PWA Dobot-PLC Control..."

# Create .env file if it doesn't exist
if [ ! -f backend/.env ]; then
    echo "📝 Creating .env file..."
    cp backend/.env.example backend/.env
    echo "⚠️  Please edit backend/.env with your PLC IP address!"
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
cd backend
python3 -m pip install -r requirements.txt
cd ..

# Create placeholder icons
echo "🎨 Creating placeholder icons..."
mkdir -p frontend
cd frontend
if [ ! -f icon-192.png ]; then
    # Create simple colored square as icon (requires ImageMagick)
    if command -v convert &> /dev/null; then
        convert -size 192x192 xc:#2563eb -gravity center -pointsize 72 -fill white -annotate +0+0 "DP" icon-192.png
        convert -size 512x512 xc:#2563eb -gravity center -pointsize 200 -fill white -annotate +0+0 "DP" icon-512.png
    else
        echo "⚠️  ImageMagick not found, skipping icon creation"
        echo "   You can add custom icons later: frontend/icon-192.png and frontend/icon-512.png"
    fi
fi
cd ..

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit backend/.env with your PLC IP address"
echo "2. Run: ./deploy/start.sh"
