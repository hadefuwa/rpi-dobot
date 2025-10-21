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
git clone https://github.com/yourusername/dobot-gateway.git
cd dobot-gateway
chmod +x setup.sh
./setup.sh
```

### 2. Configure Environment

Edit the configuration file:

```bash
nano .env
```

Key settings:
```bash
# Dobot Configuration
DOBOT_HOST=192.168.0.30
DOBOT_PORT=29999
DOBOT_USE_USB=false

# PLC Configuration
PLC_IP=192.168.0.10
PLC_RACK=0
PLC_SLOT=1

# Security
JWT_SECRET=your-super-secret-key-change-this
```

### 3. Access the Application

Open your browser and navigate to:
- `https://raspberrypi.local`
- `https://localhost`
- `https://[PI_IP_ADDRESS]`

### 4. Login

Use the default credentials:
- **Admin**: `admin` / `admin123`
- **Operator**: `operator` / `operator123`
- **Viewer**: `viewer` / `viewer123`

⚠️ **Change default passwords in production!**

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

- **Documentation**: [Wiki](https://github.com/yourusername/dobot-gateway/wiki)
- **Issues**: [GitHub Issues](https://github.com/yourusername/dobot-gateway/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/dobot-gateway/discussions)

## 🙏 Acknowledgments

- Dobot Technology for the Magician robot
- Siemens for the S7-1200 PLC
- The open-source community for the amazing tools and libraries

---

**⚠️ Safety Notice**: This software controls industrial equipment. Always follow proper safety procedures and ensure adequate training before operation.
