module.exports = {
  apps: [{
    name: 'dobot-gateway',
    script: 'server/app.js',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '1G',
    env: {
      NODE_ENV: 'production',
      PORT: 8080
    },
    env_development: {
      NODE_ENV: 'development',
      PORT: 8080
    },
    error_file: '/var/log/dobot-gateway/error.log',
    out_file: '/var/log/dobot-gateway/out.log',
    log_file: '/var/log/dobot-gateway/combined.log',
    time: true,
    log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    merge_logs: true,
    max_restarts: 10,
    min_uptime: '10s',
    restart_delay: 4000,
    kill_timeout: 5000,
    wait_ready: true,
    listen_timeout: 10000
  }]
};
