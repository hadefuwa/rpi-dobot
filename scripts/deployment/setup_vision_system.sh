#!/bin/bash

# Vision System Setup Script for Raspberry Pi
# This script installs and configures the vision system app with auto-boot

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log "Starting Vision System setup..."

# Update system packages
log "Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install system dependencies
log "Installing system dependencies..."
sudo apt-get install -y \
    build-essential \
    git \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    libatlas-base-dev \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libv4l-dev \
    libxvidcore-dev \
    libx264-dev \
    libgtk-3-dev \
    libcanberra-gtk-module \
    libcanberra-gtk3-module \
    v4l-utils \
    nodejs \
    npm

# Install PM2 globally
log "Installing PM2 process manager..."
sudo npm install -g pm2

# Set up USB permissions for camera
log "Setting up USB permissions..."
sudo usermod -a -G dialout $USER
sudo usermod -a -G video $USER

# Clone repository if not already present
if [ ! -d ~/rpi-dobot ]; then
    log "Cloning repository..."
    cd ~
    git clone https://github.com/hadefuwa/rpi-dobot.git
else
    log "Repository already exists, updating..."
    cd ~/rpi-dobot
    git pull
fi

cd ~/rpi-dobot/pwa-dobot-plc/backend

# Create virtual environment if it doesn't exist
if [ ! -d venv ]; then
    log "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment and install dependencies
log "Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# Install ultralytics (YOLO) if not already installed
log "Installing YOLO (Ultralytics)..."
pip install ultralytics

# Create logs directory
log "Setting up logging..."
mkdir -p ~/logs

# Create counter images directory
log "Setting up counter images directory..."
mkdir -p ~/counter_images

# Check for YOLO model file
log "Checking for YOLO model..."
if [ ! -f ~/counter_detector.pt ]; then
    warning "YOLO model file not found at ~/counter_detector.pt"
    warning "Please place your trained YOLO model at ~/counter_detector.pt"
    warning "The vision service will start but YOLO detection will be disabled until the model is added."
fi

# Check for camera
log "Checking for camera..."
if [ -e /dev/video0 ]; then
    success "Camera found at /dev/video0"
else
    warning "No camera found at /dev/video0"
    warning "Please connect a USB camera"
fi

# Set up PM2 for auto-start
log "Setting up PM2 for auto-start..."
cd ~/rpi-dobot/pwa-dobot-plc/deploy

# Stop any existing PM2 processes
pm2 delete all 2>/dev/null || true

# Start the applications
log "Starting applications with PM2..."
pm2 start ecosystem.config.js

# Save PM2 configuration
pm2 save

# Set up PM2 to start on boot
log "Configuring PM2 to start on boot..."
pm2 startup systemd -u $USER --hp /home/$USER | grep "sudo" | bash || warning "PM2 startup command may need to be run manually"

# Wait a moment for services to start
sleep 3

# Check status
log "Checking application status..."
pm2 status

# Display access information
echo ""
success "Vision System setup completed!"
echo ""
echo "=== Access Information ==="
PI_IP=$(hostname -I | awk '{print $1}')
echo "Web Interface: http://$PI_IP:8080/vision-system.html"
echo "Web Interface: http://localhost:8080/vision-system.html"
echo ""
echo "=== Management Commands ==="
echo "Status:  pm2 status"
echo "Logs:    pm2 logs"
echo "Restart: pm2 restart all"
echo "Stop:    pm2 stop all"
echo ""
echo "=== Application Logs ==="
echo "Main app:    pm2 logs pwa-dobot-plc"
echo "Vision service: pm2 logs vision-service"
echo ""
success "Setup complete! The application should be running and will auto-start on boot."

