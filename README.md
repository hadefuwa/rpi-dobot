# RPI-Dobot Project

A comprehensive Dobot Magician control system with PLC integration, featuring a web-based interface and alarm clearing functionality.

## 🚀 Quick Start

### On Raspberry Pi:
```bash
cd ~/rpi-dobot
git pull origin main
cd pwa-dobot-plc/backend
python3 app.py
```

Visit `http://your-pi-ip:8080` to access the web interface.

## 📁 Project Structure

```
rpi-dobot/
├── app/                          # Main application
│   └── pwa-dobot-plc/           # Working web application
├── docs/                        # Documentation
│   ├── guides/                  # Setup and usage guides
│   ├── solutions/               # Problem resolution docs
│   └── api/                     # API documentation
├── scripts/                     # Executable scripts
│   ├── deployment/              # Deployment scripts
│   └── testing/                 # Test scripts
├── lib/                         # External libraries
│   └── DobotAPI/               # Official Dobot API files
├── tests/                       # All test files
│   ├── pydobot/                # pydobot tests
│   └── official_api/           # Official API tests
├── README.md                    # This file
└── pwa-dobot-plc/              # Core application (untouched)
```

## 🔧 Key Features

- ✅ **Dobot Movement Control** - Full robot arm control via web interface
- ✅ **Alarm Clearing** - Automatic alarm state management
- ✅ **PLC Integration** - Siemens S7-1200 communication
- ✅ **Real-time Monitoring** - Live position and status updates
- ✅ **Settings Management** - Web-based configuration
- ✅ **Emergency Stop** - Safety controls

## 📚 Documentation

### Setup & Usage Guides
- [Quick Start Guide](docs/guides/QUICK_START_ON_PI.md)
- [Deployment Guide](docs/guides/DEPLOY_TO_PI.md)
- [PLC Setup Guide](docs/guides/PLC_DB1_Setup_Guide.md)
- [PLC Robot Control](docs/guides/PLC_Robot_Control_Guide.md)
- [PLC Settings Guide](docs/guides/PLC_Settings_Guide.md)

### Problem Solutions
- [Solution Summary](docs/solutions/SOLUTION_SUMMARY.md) - **Main fix documentation**
- [Bugfix Summary](docs/solutions/BUGFIX_SUMMARY.md)
- [Implementation Summary](docs/solutions/IMPLEMENTATION_SUMMARY.md)
- [Complete Documentation](docs/solutions/DOBOT_FIX_COMPLETE_DOCUMENTATION.md)

### API Documentation
- [API Migration Plan](docs/api/DOBOT_API_MIGRATION_PLAN.md)
- [Official API Migration Guide](docs/api/OFFICIAL_API_MIGRATION_GUIDE.md)
- [API Quick Reference](docs/api/OFFICIAL_API_QUICK_REFERENCE.md)
- [Example Documentation](docs/api/example_README.md)

## 🧪 Testing

### Main Test (Alarm Clearing Fix)
```bash
python3 scripts/testing/test_improved_client.py
```

### pydobot Tests
```bash
python3 tests/pydobot/test_dobot_simple.py
python3 tests/pydobot/test_dobot_speed.py
python3 tests/pydobot/test_dobot_home.py
```

### Official API Tests
```bash
python3 tests/official_api/test_official_api_connection.py
python3 tests/official_api/test_official_api_movement.py
python3 tests/official_api/test_official_api_peripherals.py
```

## 🚀 Deployment

### Quick Deployment
```bash
./scripts/deployment/setup.sh
```

### Full Deployment with PM2
```bash
./scripts/deployment/FINAL_DEPLOYMENT.sh
```

### Official API Setup
```bash
./scripts/deployment/setup_official_dobot_api.sh
```

## 🔧 Core Application

The main application is in `pwa-dobot-plc/`:
- **Backend**: Flask API with Dobot and PLC integration
- **Frontend**: Web interface with real-time controls
- **Configuration**: JSON-based settings management

## 📋 Status

✅ **WORKING** - Dobot movement issue resolved with alarm clearing  
✅ **TESTED** - All core functionality verified  
✅ **DEPLOYED** - Production-ready on Raspberry Pi  
✅ **ORGANIZED** - Clean project structure for maintainability

## 🎯 Key Solution

The main issue (Dobot not moving) was solved by adding **alarm clearing** to the initialization sequence. See [Solution Summary](docs/solutions/SOLUTION_SUMMARY.md) for details.

## 📞 Support

- Check [Documentation Index](DOCUMENTATION_INDEX.md) for all available guides
- Review [Solution Summary](docs/solutions/SOLUTION_SUMMARY.md) for the main fix
- See [Quick Start Guide](docs/guides/QUICK_START_ON_PI.md) for setup

---

**Last Updated:** 2025-10-21  
**Version:** v4.1  
**Status:** Production Ready ✅