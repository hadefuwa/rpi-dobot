require('dotenv').config();

module.exports = {
  apps: [{
    name: 'dobot-gateway',
    script: 'server/app.js',
    cwd: '/home/pi/rpi-dobot',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '1G',
    env: {
      NODE_ENV: process.env.NODE_ENV || 'development',
      PORT: process.env.PORT || 8080,
      DOBOT_HOST: process.env.DOBOT_HOST,
      DOBOT_PORT: process.env.DOBOT_PORT,
      DOBOT_USE_USB: process.env.DOBOT_USE_USB,
      DOBOT_USB_PATH: process.env.DOBOT_USB_PATH,
      PLC_IP: process.env.PLC_IP,
      PLC_RACK: process.env.PLC_RACK,
      PLC_SLOT: process.env.PLC_SLOT,
      POLL_INTERVAL: process.env.POLL_INTERVAL,
      LOG_LEVEL: process.env.LOG_LEVEL
    }
  }]
};
