const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '.env') });

module.exports = {
  apps: [{
    name: 'dobot-gateway',
    script: './server/app.js',
    cwd: __dirname,
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '1G',
    env: {
      NODE_ENV: process.env.NODE_ENV || 'development',
      PORT: process.env.PORT || '8080',
      DOBOT_HOST: process.env.DOBOT_HOST || '192.168.0.30',
      DOBOT_PORT: process.env.DOBOT_PORT || '29999',
      DOBOT_USE_USB: process.env.DOBOT_USE_USB || 'true',
      DOBOT_USB_PATH: process.env.DOBOT_USB_PATH || '/dev/ttyACM0',
      PLC_IP: process.env.PLC_IP || '192.168.0.150',
      PLC_RACK: process.env.PLC_RACK || '0',
      PLC_SLOT: process.env.PLC_SLOT || '1',
      POLL_INTERVAL: process.env.POLL_INTERVAL || '100',
      LOG_LEVEL: process.env.LOG_LEVEL || 'info'
    }
  }]
};
