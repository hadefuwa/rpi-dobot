module.exports = {
  apps: [{
    name: 'pwa-dobot-plc',
    cwd: '/home/pi/rpi-dobot/pwa-dobot-plc/backend',
    script: 'venv/bin/python',
    args: 'app.py',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '200M',
    env: {
      NODE_ENV: 'production'
    },
    error_file: '/home/pi/logs/pwa-dobot-plc-error.log',
    out_file: '/home/pi/logs/pwa-dobot-plc-out.log',
    log_date_format: 'YYYY-MM-DD HH:mm:ss Z'
  }]
};
