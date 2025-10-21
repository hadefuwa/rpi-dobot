/**
 * Dobot Gateway Configuration
 * 
 * Edit these values directly to configure your system.
 * No need for .env files - just change the values here!
 */

module.exports = {
  // Server Configuration
  server: {
    port: 8080,
    httpsPort: 443,
    nodeEnv: 'development'
  },

  // Dobot Robot Configuration
  dobot: {
    // For TCP/IP connection (when Dobot has network module)
    host: '192.168.0.30',
    port: 29999,
    
    // For USB connection (recommended for Raspberry Pi)
    useUSB: true,  // Set to true for USB, false for TCP/IP
    usbPath: '/dev/ttyACM0',  // Common: /dev/ttyACM0 or /dev/ttyUSB0
    
    // Movement limits (safety boundaries)
    limits: {
      x: { min: -300, max: 300 },
      y: { min: -300, max: 300 },
      z: { min: -100, max: 400 },
      r: { min: -180, max: 180 }
    }
  },

  // PLC (Siemens S7-1200) Configuration
  plc: {
    ip: '192.168.0.150',  // Change this to your PLC's IP address
    rack: 0,              // Usually 0 for S7-1200
    slot: 1,              // Usually 1 for S7-1200
    
    // Memory mapping (matches your PLC program)
    memoryMap: {
      controlBits: {
        start: 'M0.0',
        stop: 'M0.1',
        home: 'M0.2',
        estop: 'M0.3'
      },
      dataBlock: 1,  // DB1
      targetPoseOffset: 0,    // DBD0-DBD8 (X,Y,Z target)
      currentPoseOffset: 12,  // DBD12-DBD20 (X,Y,Z current)
      statusOffset: 24        // DBW24 (status code)
    }
  },

  // Bridge Service Configuration
  bridge: {
    pollInterval: 100,  // How often to check PLC (milliseconds)
    maxRetries: 3,
    retryDelay: 1000
  },

  // Security Configuration
  security: {
    jwtSecret: 'dbc668505d1de51cdeb6e1461f28de316b385670df1d',
    jwtExpiresIn: '8h',
    saltRounds: 12
  },

  // Logging Configuration
  logging: {
    level: 'info',  // Options: 'error', 'warn', 'info', 'debug'
    dir: '/var/log/dobot-gateway'
  }
};

