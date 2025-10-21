// PM2 Ecosystem configuration for PWA Dobot-PLC Control
const path = require('path');

module.exports = {
  apps: [{
    name: 'pwa-dobot-plc',
    script: 'app.py',
    cwd: path.join(__dirname, '../backend'),
    interpreter: 'python3',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '500M',
    env: {
      PLC_IP: '192.168.0.150',
      PLC_RACK: '0',
      PLC_SLOT: '1',
      DOBOT_USE_USB: 'true',
      DOBOT_USB_PATH: '/dev/ttyACM0',
      PORT: '8080'
    }
  }]
};
