# Dobot Gateway - PWA + Raspberry Pi Gateway for Dobot ↔ S7-1200

A production-ready headless Node.js backend on Raspberry Pi facilitating real-time communication between Dobot Magician (via USB/TCP binary protocol) and Siemens S7-1200 PLC (via Snap7), with a secure PWA frontend for monitoring and control.

## 🚀 Features

- **Real-time Communication**: Binary protocol implementation for Dobot Magician
- **PLC Integration**: Snap7-based communication with Siemens S7-1200
- **Secure PWA**: React-based Progressive Web App with offline capabilities
- **Authentication**: JWT-based security with role-based access control
- **Safety Features**: Emergency stop, command validation, error handling
- **Monitoring**: Comprehensive logging and health checks
- **Production Ready**: PM2/systemd management, HTTPS, log rotation

## 🏗️ Architecture

```
[PWA Client (HTTPS/WSS)]
        ↕ JWT Auth
[Node.js Gateway on Raspberry Pi]
        ↕ Binary Protocol (USB/TCP 29999)
    [Dobot Magician]
        ↕ S7Comm (Snap7)
  [Siemens S7-1200]
```

## 📋 Requirements

- Raspberry Pi 4 (4GB+ RAM recommended)
- Raspberry Pi OS Lite (64-bit)
- Node.js 20 LTS
- 16GB+ SD card
- Dobot Magician robot
- Siemens S7-1200 PLC

## 🛠️ Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/hadefuwa/rpi-dobot.git
cd rpi-dobot
chmod +x setup.sh
./setup.sh
```

### 2. Configure Environment

Edit the configuration file:

```bash
nano .env
```

#### Required Configuration Settings

**Dobot Robot Settings:**
```bash
# Dobot Configuration
DOBOT_HOST=192.168.0.30          # IP address of your Dobot Magician
DOBOT_PORT=29999                 # TCP port (default: 29999)
DOBOT_USE_USB=false              # Set to 'true' for USB connection
DOBOT_USB_PATH=/dev/ttyUSB0      # USB device path (if using USB)
```

**PLC Settings:**
```bash
# PLC Configuration  
PLC_IP=192.168.0.10              # IP address of your S7-1200 PLC
PLC_RACK=0                       # PLC rack number (usually 0)
PLC_SLOT=1                       # PLC slot number (usually 1)
```

**Security Settings:**
```bash
# Security (REQUIRED - Change these!)
JWT_SECRET=your-super-secret-key-change-this-in-production
JWT_EXPIRES_IN=8h
SALT_ROUNDS=12
```

**Network Settings:**
```bash
# Network Configuration
NODE_ENV=production
PORT=8080                        # HTTP port for development
HTTPS_PORT=443                   # HTTPS port for production
```

**Logging & Performance:**
```bash
# Logging
LOG_LEVEL=info                   # debug, info, warn, error
LOG_DIR=/var/log/dobot-gateway

# Performance
POLL_INTERVAL=100                # PLC polling interval (ms)
MAX_OLD_SPACE_SIZE=512          # Node.js memory limit (MB)
```

#### Configuration Examples

**For USB Connection to Dobot:**
```bash
DOBOT_HOST=192.168.0.30
DOBOT_PORT=29999
DOBOT_USE_USB=true
DOBOT_USB_PATH=/dev/ttyUSB0
```

**For TCP Connection to Dobot:**
```bash
DOBOT_HOST=192.168.0.30
DOBOT_PORT=29999
DOBOT_USE_USB=false
```

**For Different PLC Configuration:**
```bash
PLC_IP=192.168.1.100            # Different PLC IP
PLC_RACK=0                      # Standard rack
PLC_SLOT=2                      # Different slot
```

#### Important Notes

- **Change JWT_SECRET**: Generate a strong secret key for production
- **Network Access**: Ensure Dobot and PLC are accessible from Raspberry Pi
- **Firewall**: Open required ports (29999 for Dobot, 102 for S7Comm)
- **USB Permissions**: If using USB, add user to dialout group: `sudo usermod -a -G dialout $USER`

### 3. Start the Application

**Option A: Using PM2 (Recommended)**
```bash
# Start the application
pm2 start ecosystem.config.js

# Check status
pm2 status

# View logs
pm2 logs dobot-gateway

# Restart if needed
pm2 restart dobot-gateway
```

**Option B: Using systemd**
```bash
# Enable and start the service
sudo systemctl enable dobot-gateway
sudo systemctl start dobot-gateway

# Check status
sudo systemctl status dobot-gateway

# View logs
sudo journalctl -u dobot-gateway -f
```

**Option C: Manual Start (Development)**
```bash
# Install dependencies
npm install
cd client && npm install && npm run build && cd ..

# Start the server
node server/app.js
```

### 4. Access the Application

Open your browser and navigate to:
- **Production**: `https://raspberrypi.local` or `https://[PI_IP_ADDRESS]`
- **Development**: `http://localhost:8080`

### 5. Default Login Credentials

| Role | Username | Password | Permissions |
|------|----------|----------|------------|
| **Admin** | `admin` | `admin123` | Full control, user management |
| **Operator** | `operator` | `operator123` | Robot control, monitoring |
| **Viewer** | `viewer` | `viewer123` | Read-only access |

⚠️ **Change default passwords in production!**

### 6. Verify Installation

**Check Service Status:**
```bash
# PM2 status
pm2 status

# Systemd status  
sudo systemctl status dobot-gateway

# Check if ports are listening
sudo netstat -tlnp | grep :8080
sudo netstat -tlnp | grep :443
```

**Test Connections:**
```bash
# Test Dobot connection
curl -k https://localhost/api/status

# Test PLC connection
curl -k https://localhost/api/plc/status

# Check health endpoint
curl -k https://localhost/api/health
```

### 7. Troubleshooting

**Common Issues:**

**Connection Refused:**
```bash
# Check if service is running
pm2 status
sudo systemctl status dobot-gateway

# Check logs for errors
pm2 logs dobot-gateway
sudo journalctl -u dobot-gateway -f
```

**Dobot Connection Failed:**
```bash
# Verify Dobot is accessible
ping 192.168.0.30
telnet 192.168.0.30 29999

# Check USB connection
ls -la /dev/ttyUSB*
sudo usermod -a -G dialout $USER
```

**PLC Connection Failed:**
```bash
# Verify PLC is accessible
ping 192.168.0.10
telnet 192.168.0.10 102

# Check S7Comm port (102) is open
sudo ufw allow 102
```

**Permission Issues:**
```bash
# Fix log directory permissions
sudo mkdir -p /var/log/dobot-gateway
sudo chown $USER:$USER /var/log/dobot-gateway

# Fix USB permissions
sudo usermod -a -G dialout $USER
sudo reboot
```

**Memory Issues:**
```bash
# Check memory usage
free -h
pm2 monit

# Restart if needed
pm2 restart dobot-gateway
```

## 📊 PLC Memory Mapping

The system uses specific memory addresses in the S7-1200 PLC for communication:

| Address | Type | Description | Access |
|---------|------|-------------|--------|
| **M0.0** | BOOL | Start Dobot Command | Write |
| **M0.1** | BOOL | Stop/Pause Command | Write |
| **M0.2** | BOOL | Reset/Home Command | Write |
| **M0.3** | BOOL | Emergency Stop | Write |
| **DB1.DBD0** | REAL | Target X Position | Write |
| **DB1.DBD4** | REAL | Target Y Position | Write |
| **DB1.DBD8** | REAL | Target Z Position | Write |
| **DB1.DBD12** | REAL | Current X Position | Read |
| **DB1.DBD16** | REAL | Current Y Position | Read |
| **DB1.DBD20** | REAL | Current Z Position | Read |
| **DB1.DBW24** | INT | Status Code | Read |

## 🔌 API Endpoints

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `GET /api/auth/me` - Get current user

### Dobot Control
- `GET /api/dobot/status` - Get Dobot connection status
- `GET /api/dobot/pose` - Get current robot pose
- `POST /api/dobot/home` - Home the robot
- `POST /api/dobot/move` - Move to position
- `POST /api/dobot/stop` - Stop robot movement
- `POST /api/dobot/emergency-stop` - Emergency stop

### PLC Communication
- `GET /api/plc/status` - Get PLC connection status
- `GET /api/plc/read/:address` - Read PLC memory
- `POST /api/plc/write/:address` - Write to PLC memory
- `GET /api/plc/io` - Get all I/O status

### System
- `GET /api/health` - System health check
- `GET /api/status` - Overall system status
- `GET /api/logs` - View system logs

## 🔧 Manual Installation

### Prerequisites

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install dependencies
sudo apt-get install -y build-essential git curl wget nginx openssl

# Install Node.js 20 LTS
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install PM2
sudo npm install -g pm2
```

### Backend Setup

```bash
# Install dependencies
npm install

# Set up environment
cp .env.example .env
# Edit .env with your configuration

# Create log directory
sudo mkdir -p /var/log/dobot-gateway
sudo chown $USER:$USER /var/log/dobot-gateway
```

### Frontend Setup

```bash
cd client
npm install
npm run build
cd ..
```

### Start the Application

```bash
# Using PM2 (recommended)
pm2 start ecosystem.config.js
pm2 save
pm2 startup

# Or using systemd
sudo systemctl enable dobot-gateway
sudo systemctl start dobot-gateway
```

## 📡 API Documentation

### Authentication

All API endpoints require authentication via JWT token.

```bash
# Login
POST /api/auth/login
{
  "username": "operator",
  "password": "operator123"
}

# Get current user
GET /api/auth/me
```

### Dobot Control

```bash
# Get current pose
GET /api/dobot/pose

# Home robot
POST /api/dobot/home

# Move to position
POST /api/dobot/move
{
  "x": 200,
  "y": 0,
  "z": 100,
  "r": 0
}

# Stop robot
POST /api/dobot/stop

# Control suction cup
POST /api/dobot/suction
{
  "enable": true
}
```

### PLC Control

```bash
# Get PLC pose
GET /api/plc/pose

# Set PLC pose
POST /api/plc/pose
{
  "x": 200,
  "y": 0,
  "z": 100
}

# Get control bits
GET /api/plc/control

# Set control bits
POST /api/plc/control
{
  "start": true,
  "home": false
}
```

### System Status

```bash
# Get system status
GET /api/status

# Health check
GET /api/health

# Emergency stop (no auth required)
POST /api/emergency-stop
```

## 🔒 Security

- JWT-based authentication with HTTP-only cookies
- Role-based access control (admin, operator, viewer)
- HTTPS with self-signed certificates (configurable)
- Input validation and sanitization
- Rate limiting on API endpoints
- CORS protection

## 🧪 Testing

```bash
# Run all tests
npm test

# Run specific test suites
npm run test:unit
npm run test:integration
npm run test:e2e

# Run tests in watch mode
npm run test:watch
```

## 📊 Monitoring

### Logs

```bash
# View application logs
pm2 logs dobot-gateway

# View system logs
sudo journalctl -u dobot-gateway

# View Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Health Checks

- Application health: `GET /api/health`
- System status: `GET /api/status`
- PM2 status: `pm2 status`

### Monitoring Script

```bash
./monitor.sh
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NODE_ENV` | Environment mode | `production` |
| `PORT` | HTTP port | `8080` |
| `DOBOT_HOST` | Dobot IP address | `192.168.0.30` |
| `DOBOT_PORT` | Dobot TCP port | `29999` |
| `DOBOT_USE_USB` | Use USB connection | `false` |
| `PLC_IP` | PLC IP address | `192.168.0.10` |
| `PLC_RACK` | PLC rack number | `0` |
| `PLC_SLOT` | PLC slot number | `1` |
| `JWT_SECRET` | JWT secret key | **Required** |
| `LOG_LEVEL` | Logging level | `info` |

### PLC Memory Map

| Address | Type | Description |
|---------|------|-------------|
| M0.0 | BOOL | Start Dobot Command |
| M0.1 | BOOL | Stop/Pause |
| M0.2 | BOOL | Reset/Home |
| M0.3 | BOOL | Emergency Stop |
| DB1.DBD0 | REAL | Target X Position |
| DB1.DBD4 | REAL | Target Y Position |
| DB1.DBD8 | REAL | Target Z Position |
| DB1.DBD12 | REAL | Current X (feedback) |
| DB1.DBD16 | REAL | Current Y (feedback) |
| DB1.DBD20 | REAL | Current Z (feedback) |
| DB1.DBW24 | INT | Status Code |

## 🚨 Safety Features

- **Emergency Stop**: Hardware and software emergency stop
- **Command Validation**: Range checking for all movements
- **Error Handling**: Comprehensive error recovery
- **Connection Monitoring**: Automatic reconnection
- **Safe Shutdown**: Graceful shutdown procedures

## 🔄 Management Commands

```bash
# Start application
./start.sh

# Stop application
./stop.sh

# Restart application
./restart.sh

# Monitor status
./monitor.sh

# View logs
pm2 logs dobot-gateway

# Restart PM2
pm2 restart dobot-gateway

# Stop PM2
pm2 stop dobot-gateway
```

## 🐛 Troubleshooting

### Common Issues

1. **Connection Refused**
   - Check if the application is running: `pm2 status`
   - Check logs: `pm2 logs dobot-gateway`
   - Verify port availability: `netstat -tlnp | grep :8080`

2. **Dobot Not Connecting**
   - Verify IP address and port in `.env`
   - Check network connectivity: `ping 192.168.0.30`
   - Ensure Dobot is powered on and in TCP mode

3. **PLC Not Connecting**
   - Verify PLC IP address and rack/slot settings
   - Check network connectivity: `ping 192.168.0.10`
   - Ensure PLC is running and accessible

4. **SSL Certificate Issues**
   - Regenerate certificates: `rm certs/* && ./setup.sh`
   - Accept self-signed certificate in browser
   - Check certificate validity: `openssl x509 -in certs/cert.pem -text -noout`

### Log Analysis

```bash
# Application errors
grep "ERROR" /var/log/dobot-gateway/error.log

# Connection issues
grep "connection" /var/log/dobot-gateway/combined.log

# Performance issues
grep "slow" /var/log/dobot-gateway/combined.log
```

## 📈 Performance Tuning

### Node.js Optimization

```bash
# Increase memory limit
node --max-old-space-size=512 server/app.js

# Enable clustering
pm2 start ecosystem.config.js -i max
```

### System Optimization

```bash
# Increase file descriptor limit
echo "* soft nofile 65536" | sudo tee -a /etc/security/limits.conf
echo "* hard nofile 65536" | sudo tee -a /etc/security/limits.conf

# Optimize network settings
echo "net.core.rmem_max = 16777216" | sudo tee -a /etc/sysctl.conf
echo "net.core.wmem_max = 16777216" | sudo tee -a /etc/sysctl.conf
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Add tests for new functionality
5. Run tests: `npm test`
6. Commit changes: `git commit -am 'Add feature'`
7. Push to branch: `git push origin feature-name`
8. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [Wiki](https://github.com/hadefuwa/rpi-dobot/wiki)
- **Issues**: [GitHub Issues](https://github.com/hadefuwa/rpi-dobot/issues)
- **Discussions**: [GitHub Discussions](https://github.com/hadefuwa/rpi-dobot/discussions)

## 🙏 Acknowledgments

- Dobot Technology for the Magician robot
- Siemens for the S7-1200 PLC
- The open-source community for the amazing tools and libraries

---

**⚠️ Safety Notice**: This software controls industrial equipment. Always follow proper safety procedures and ensure adequate training before operation.
