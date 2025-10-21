#!/bin/bash

# Dobot Gateway Setup Script for Raspberry Pi
# This script sets up the complete Dobot Gateway system

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
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

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   error "This script should not be run as root. Please run as a regular user with sudo privileges."
   exit 1
fi

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    warning "This script is designed for Raspberry Pi. Proceeding anyway..."
fi

log "Starting Dobot Gateway setup..."

# Update system packages
log "Updating system packages..."
sudo apt-get update && sudo apt-get upgrade -y

# Install system dependencies
log "Installing system dependencies..."
sudo apt-get install -y \
    build-essential \
    git \
    curl \
    wget \
    vim \
    htop \
    nginx \
    openssl \
    ufw \
    python3 \
    python3-pip

# Set up USB permissions for Dobot
log "Setting up USB permissions for Dobot..."
sudo usermod -a -G dialout $USER
sudo usermod -a -G tty $USER

# Install Node.js 20 LTS
log "Installing Node.js 20 LTS..."
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Verify Node.js installation
NODE_VERSION=$(node --version)
success "Node.js installed: $NODE_VERSION"

# Install PM2 globally
log "Installing PM2 process manager..."
sudo npm install -g pm2

# Create application directory
APP_DIR="/home/$USER/dobot-gateway"
log "Setting up application directory: $APP_DIR"

if [ -d "$APP_DIR" ]; then
    warning "Directory $APP_DIR already exists. Backing up..."
    mv "$APP_DIR" "${APP_DIR}.backup.$(date +%Y%m%d_%H%M%S)"
fi

mkdir -p "$APP_DIR"
cd "$APP_DIR"

# Copy application files (assuming they're in current directory)
log "Copying application files..."
cp -r . "$APP_DIR/"

# Install Node.js dependencies
log "Installing Node.js dependencies..."
npm install

# Install client dependencies and build
log "Building client application..."
cd client
npm install
npm run build
cd ..

# Create log directory
log "Setting up logging..."
sudo mkdir -p /var/log/dobot-gateway
sudo chown $USER:$USER /var/log/dobot-gateway

# Create data directory
mkdir -p "$APP_DIR/data"

# Set up environment configuration
log "Setting up environment configuration..."
if [ ! -f .env ]; then
    cp .env.example .env
    warning "Please edit .env file with your configuration:"
    echo "  nano $APP_DIR/.env"
fi

# Check for USB devices
log "Checking for USB devices..."
if ls /dev/ttyUSB* 1> /dev/null 2>&1; then
    success "Found USB devices: $(ls /dev/ttyUSB*)"
    warning "Make sure to update DOBOT_USB_PATH in .env file"
elif ls /dev/ttyACM* 1> /dev/null 2>&1; then
    success "Found USB devices: $(ls /dev/ttyACM*)"
    warning "Make sure to update DOBOT_USB_PATH in .env file"
else
    warning "No USB devices found. Connect your Dobot and check with: ls /dev/ttyUSB*"
fi

# Generate SSL certificates for HTTPS
log "Setting up SSL certificates..."
mkdir -p "$APP_DIR/certs"

if [ ! -f "$APP_DIR/certs/key.pem" ] || [ ! -f "$APP_DIR/certs/cert.pem" ]; then
    log "Generating self-signed SSL certificate..."
    openssl req -x509 -newkey rsa:4096 -keyout "$APP_DIR/certs/key.pem" -out "$APP_DIR/certs/cert.pem" -days 365 -nodes -subj "/C=US/ST=State/L=City/O=Organization/CN=raspberrypi.local"
    success "SSL certificate generated"
else
    success "SSL certificate already exists"
fi

# Set up Nginx reverse proxy
log "Setting up Nginx reverse proxy..."
sudo tee /etc/nginx/sites-available/dobot-gateway > /dev/null <<EOF
server {
    listen 80;
    server_name raspberrypi.local localhost;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name raspberrypi.local localhost;

    ssl_certificate $APP_DIR/certs/cert.pem;
    ssl_certificate_key $APP_DIR/certs/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Client max body size
    client_max_body_size 10M;

    # Proxy to Node.js application
    location / {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }

    # WebSocket support
    location /socket.io/ {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Enable the site
sudo ln -sf /etc/nginx/sites-available/dobot-gateway /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx

# Set up firewall
log "Configuring firewall..."
sudo ufw --force enable
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 29999/tcp  # Dobot TCP port
sudo ufw allow 102/tcp    # S7Comm port

# Set up PM2 configuration
log "Setting up PM2 configuration..."
tee ecosystem.config.js > /dev/null <<EOF
module.exports = {
  apps: [{
    name: 'dobot-gateway',
    script: 'server/app.js',
    cwd: '$APP_DIR',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '1G',
    env: {
      NODE_ENV: 'production',
      PORT: 8080
    },
    error_file: '/var/log/dobot-gateway/error.log',
    out_file: '/var/log/dobot-gateway/out.log',
    log_file: '/var/log/dobot-gateway/combined.log',
    time: true
  }]
};
EOF

# Start the application with PM2
log "Starting Dobot Gateway application..."
pm2 start ecosystem.config.js
pm2 save
pm2 startup

# Set up log rotation
log "Setting up log rotation..."
sudo tee /etc/logrotate.d/dobot-gateway > /dev/null <<EOF
/var/log/dobot-gateway/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 $USER $USER
    postrotate
        pm2 reloadLogs
    endscript
}
EOF

# Set up systemd service (alternative to PM2)
log "Setting up systemd service..."
sudo tee /etc/systemd/system/dobot-gateway.service > /dev/null <<EOF
[Unit]
Description=Dobot Gateway Service
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$APP_DIR
ExecStart=/usr/bin/node server/app.js
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
Environment=NODE_ENV=production
Environment=PORT=8080

[Install]
WantedBy=multi-user.target
EOF

# Enable systemd service (but don't start it since PM2 is running)
sudo systemctl enable dobot-gateway

# Set up mDNS (for raspberrypi.local)
log "Setting up mDNS..."
sudo apt-get install -y avahi-daemon
sudo systemctl enable avahi-daemon
sudo systemctl start avahi-daemon

# Create startup script
log "Creating startup script..."
tee start.sh > /dev/null <<EOF
#!/bin/bash
cd $APP_DIR
pm2 start ecosystem.config.js
EOF

chmod +x start.sh

# Create stop script
tee stop.sh > /dev/null <<EOF
#!/bin/bash
cd $APP_DIR
pm2 stop dobot-gateway
EOF

chmod +x stop.sh

# Create restart script
tee restart.sh > /dev/null <<EOF
#!/bin/bash
cd $APP_DIR
pm2 restart dobot-gateway
EOF

chmod +x restart.sh

# Set up monitoring script
log "Setting up monitoring script..."
tee monitor.sh > /dev/null <<EOF
#!/bin/bash
echo "=== Dobot Gateway Status ==="
echo "PM2 Status:"
pm2 status
echo ""
echo "Application Logs (last 20 lines):"
pm2 logs dobot-gateway --lines 20
echo ""
echo "System Resources:"
echo "Memory: \$(free -h | grep Mem | awk '{print \$3\"/\"\$2}')"
echo "Disk: \$(df -h / | tail -1 | awk '{print \$3\"/\"\$2\" (\"\$5\" used)\"}')"
echo "CPU Load: \$(uptime | awk -F'load average:' '{print \$2}')"
EOF

chmod +x monitor.sh

# Run tests
log "Running tests..."
npm test || warning "Some tests failed, but continuing with setup..."

# Final status check
log "Checking application status..."
sleep 5
pm2 status

# Display access information
echo ""
success "Dobot Gateway setup completed!"
echo ""
echo "=== Access Information ==="
echo "Web Interface: https://raspberrypi.local"
echo "Web Interface: https://localhost"
echo "Web Interface: https://$(hostname -I | awk '{print $1}')"
echo ""
echo "=== Management Commands ==="
echo "Start:   cd $APP_DIR && ./start.sh"
echo "Stop:    cd $APP_DIR && ./stop.sh"
echo "Restart: cd $APP_DIR && ./restart.sh"
echo "Monitor: cd $APP_DIR && ./monitor.sh"
echo "Logs:    pm2 logs dobot-gateway"
echo ""
echo "=== Configuration ==="
echo "Edit settings: nano $APP_DIR/.env"
echo "Nginx config:  sudo nano /etc/nginx/sites-available/dobot-gateway"
echo ""
echo "=== Default Credentials ==="
echo "Admin:    admin / admin123"
echo "Operator: operator / operator123"
echo "Viewer:   viewer / viewer123"
echo ""
warning "Please change default passwords in production!"
echo ""
success "Setup complete! The application should be running at https://raspberrypi.local"
