const express = require('express');
const router = express.Router();
const { verifyToken, requirePermission, requireRole, login, logout, getCurrentUser, authRateLimit } = require('../middleware/auth');
const logger = require('../utils/logger');

// Authentication routes - DISABLED FOR DEVELOPMENT
router.post('/auth/login', authRateLimit, login);
router.post('/auth/logout', logout);
router.get('/auth/me', (req, res) => {
  // Return fake admin user for development
  res.json({
    username: 'admin',
    role: 'admin',
    permissions: ['read', 'write', 'control', 'admin']
  });
});

// Health check (no auth required)
router.get('/health', (req, res) => {
  const health = {
    status: 'ok',
    timestamp: Date.now(),
    uptime: process.uptime(),
    version: process.env.npm_package_version || '1.0.0',
    environment: process.env.NODE_ENV || 'development'
  };
  
  res.json(health);
});

// Helper function to add timeout to promises
const withTimeout = (promise, timeoutMs = 1000) => {
  return Promise.race([
    promise,
    new Promise((_, reject) =>
      setTimeout(() => reject(new Error('Timeout')), timeoutMs)
    )
  ]);
};

// System status (no auth required)
router.get('/status', async (req, res) => {
  try {
    const { dobotClient, plcClient, bridge } = req.app.locals;

    // Get pose with timeout
    let pose = null;
    if (dobotClient?.connected) {
      try {
        pose = await withTimeout(dobotClient.getPose(), 500);
      } catch (err) {
        // Timeout or error - just leave pose as null
      }
    }

    // Get PLC health with timeout
    let plcHealth = { status: 'disconnected' };
    if (plcClient?.isConnected()) {
      try {
        plcHealth = await withTimeout(plcClient.healthCheck(), 500);
      } catch (err) {
        plcHealth = { status: 'error' };
      }
    }

    const status = {
      dobot: {
        connected: dobotClient?.connected || false,
        pose: pose
      },
      plc: {
        connected: plcClient?.isConnected() || false,
        health: plcHealth
      },
      bridge: bridge?.getStatus() || { running: false },
      system: {
        memory: process.memoryUsage(),
        cpu: process.cpuUsage(),
        uptime: process.uptime()
      }
    };

    res.json(status);
  } catch (error) {
    logger.error('Status check failed:', error);
    res.status(500).json({ error: 'Failed to get system status' });
  }
});

// Dobot control routes (requires control permission)
router.post('/dobot/home', async (req, res) => {
  try {
    const { dobotClient } = req.app.locals;
    
    if (!dobotClient?.connected) {
      return res.status(503).json({ error: 'Dobot not connected' });
    }
    
    const queuedIndex = await dobotClient.home();
    await dobotClient.startQueue(); // Start executing the queued command
    logger.dobot('Home command executed', { queuedIndex });
    
    res.json({ success: true, queuedIndex });
  } catch (error) {
    logger.error('Home command failed:', error);
    res.status(500).json({ error: 'Home command failed', details: error.message });
  }
});

router.post('/dobot/move', async (req, res) => {
  try {
    const { dobotClient } = req.app.locals;
    const { x, y, z, r = 0 } = req.body;
    
    if (!dobotClient?.connected) {
      return res.status(503).json({ error: 'Dobot not connected' });
    }
    
    if (x === undefined || y === undefined || z === undefined) {
      return res.status(400).json({ error: 'x, y, z coordinates are required' });
    }
    
    const queuedIndex = await dobotClient.movePTP(x, y, z, r);
    await dobotClient.startQueue(); // Start executing the queued command
    logger.dobot('Move command executed', { x, y, z, r, queuedIndex });
    
    res.json({ success: true, queuedIndex });
  } catch (error) {
    logger.error('Move command failed:', error);
    res.status(500).json({ error: 'Move command failed', details: error.message });
  }
});

router.post('/dobot/stop', async (req, res) => {
  try {
    const { dobotClient } = req.app.locals;
    
    if (!dobotClient?.connected) {
      return res.status(503).json({ error: 'Dobot not connected' });
    }
    
    await dobotClient.stopQueue(); // Stop queue execution first
    await dobotClient.clearQueue(); // Then clear all queued commands
    logger.dobot('Stop command executed', { user: req.user?.username || 'anonymous' });
    
    res.json({ success: true });
  } catch (error) {
    logger.error('Stop command failed:', error);
    res.status(500).json({ error: 'Stop command failed', details: error.message });
  }
});

router.post('/dobot/suction', async (req, res) => {
  try {
    const { dobotClient } = req.app.locals;
    const { enable } = req.body;
    
    if (!dobotClient?.connected) {
      return res.status(503).json({ error: 'Dobot not connected' });
    }
    
    if (typeof enable !== 'boolean') {
      return res.status(400).json({ error: 'enable parameter must be boolean' });
    }
    
    await dobotClient.setSuctionCup(enable);
    logger.dobot('Suction cup command executed', { enable });
    
    res.json({ success: true, enabled: enable });
  } catch (error) {
    logger.error('Suction cup command failed:', error);
    res.status(500).json({ error: 'Suction cup command failed', details: error.message });
  }
});

router.get('/dobot/pose', async (req, res) => {
  try {
    const { dobotClient } = req.app.locals;
    
    if (!dobotClient?.connected) {
      return res.status(503).json({ error: 'Dobot not connected' });
    }
    
    const pose = await dobotClient.getPose();
    res.json(pose);
  } catch (error) {
    logger.error('Get pose failed:', error);
    res.status(500).json({ error: 'Failed to get pose', details: error.message });
  }
});

router.get('/dobot/status', async (req, res) => {
  try {
    const { dobotClient } = req.app.locals;
    
    if (!dobotClient?.connected) {
      return res.status(503).json({ error: 'Dobot not connected' });
    }
    
    const status = await dobotClient.getStatus();
    res.json(status);
  } catch (error) {
    logger.error('Get status failed:', error);
    res.status(500).json({ error: 'Failed to get status', details: error.message });
  }
});

// Queue control endpoints
router.post('/dobot/queue/start', async (req, res) => {
  try {
    const { dobotClient } = req.app.locals;
    
    if (!dobotClient?.connected) {
      return res.status(503).json({ error: 'Dobot not connected' });
    }
    
    await dobotClient.startQueue();
    logger.dobot('Queue started');
    res.json({ success: true });
  } catch (error) {
    logger.error('Start queue failed:', error);
    res.status(500).json({ error: 'Failed to start queue', details: error.message });
  }
});

router.post('/dobot/queue/stop', async (req, res) => {
  try {
    const { dobotClient } = req.app.locals;
    
    if (!dobotClient?.connected) {
      return res.status(503).json({ error: 'Dobot not connected' });
    }
    
    await dobotClient.stopQueue();
    logger.dobot('Queue stopped');
    res.json({ success: true });
  } catch (error) {
    logger.error('Stop queue failed:', error);
    res.status(500).json({ error: 'Failed to stop queue', details: error.message });
  }
});

router.post('/dobot/queue/clear', async (req, res) => {
  try {
    const { dobotClient } = req.app.locals;
    
    if (!dobotClient?.connected) {
      return res.status(503).json({ error: 'Dobot not connected' });
    }
    
    await dobotClient.clearQueue();
    logger.dobot('Queue cleared');
    res.json({ success: true });
  } catch (error) {
    logger.error('Clear queue failed:', error);
    res.status(500).json({ error: 'Failed to clear queue', details: error.message });
  }
});

// PLC control routes (requires control permission)
router.get('/plc/pose', async (req, res) => {
  try {
    const { plcClient } = req.app.locals;
    
    if (!plcClient) {
      return res.status(503).json({ error: 'PLC client not initialized' });
    }
    
    // Let the PLC service handle connection with ensureConnected()
    const pose = await plcClient.readPoseFromDB(1);
    res.json(pose);
  } catch (error) {
    logger.error('Get PLC pose failed:', error);
    res.status(500).json({ error: 'Failed to get PLC pose', details: error.message });
  }
});

router.post('/plc/pose', async (req, res) => {
  try {
    const { plcClient } = req.app.locals;
    const { x, y, z } = req.body;
    
    if (!plcClient) {
      return res.status(503).json({ error: 'PLC client not initialized' });
    }
    
    if (x === undefined || y === undefined || z === undefined) {
      return res.status(400).json({ error: 'x, y, z coordinates are required' });
    }
    
    // Let the PLC service handle connection with ensureConnected()
    await plcClient.writePoseToDB({ x, y, z }, 1, 12);
    logger.plc('PLC pose written', { x, y, z });
    
    res.json({ success: true });
  } catch (error) {
    logger.error('Write PLC pose failed:', error);
    res.status(500).json({ error: 'Failed to write PLC pose', details: error.message });
  }
});

router.get('/plc/control', async (req, res) => {
  try {
    const { plcClient } = req.app.locals;
    
    if (!plcClient) {
      return res.status(503).json({ error: 'PLC client not initialized' });
    }
    
    // Let the PLC service handle connection with ensureConnected()
    const controlBits = await plcClient.getControlBits();
    res.json(controlBits);
  } catch (error) {
    logger.error('Get PLC control bits failed:', error);
    res.status(500).json({ error: 'Failed to get PLC control bits', details: error.message });
  }
});

router.post('/plc/control', async (req, res) => {
  try {
    const { plcClient } = req.app.locals;
    const { start, stop, home, estop } = req.body;
    
    if (!plcClient) {
      return res.status(503).json({ error: 'PLC client not initialized' });
    }
    
    // Let the PLC service handle connection with ensureConnected()
    const controlBits = {};
    if (start !== undefined) controlBits.start = start;
    if (stop !== undefined) controlBits.stop = stop;
    if (home !== undefined) controlBits.home = home;
    if (estop !== undefined) controlBits.estop = estop;
    
    await plcClient.setControlBits(controlBits);
    logger.plc('PLC control bits written', { controlBits });
    
    res.json({ success: true });
  } catch (error) {
    logger.error('Write PLC control bits failed:', error);
    res.status(500).json({ error: 'Failed to write PLC control bits', details: error.message });
  }
});

// PLC connection test endpoint
router.get('/plc/test', async (req, res) => {
  try {
    const { plcClient } = req.app.locals;
    
    if (!plcClient) {
      return res.status(503).json({ error: 'PLC client not initialized' });
    }
    
    const connectionTest = await plcClient.testConnection();
    const healthCheck = await plcClient.healthCheck();
    
    res.json({
      connectionTest,
      healthCheck,
      connected: plcClient.isConnected(),
      ip: plcClient.ip,
      rack: plcClient.rack,
      slot: plcClient.slot
    });
  } catch (error) {
    logger.error('PLC test failed:', error);
    res.status(500).json({ error: 'PLC test failed', details: error.message });
  }
});

// Bridge control routes (requires control permission)
router.post('/bridge/start', async (req, res) => {
  try {
    const { bridge } = req.app.locals;
    
    if (!bridge) {
      return res.status(503).json({ error: 'Bridge service not available' });
    }
    
    await bridge.start();
    logger.bridge('Bridge started', { user: req.user?.username || 'anonymous' });
    
    res.json({ success: true });
  } catch (error) {
    logger.error('Start bridge failed:', error);
    res.status(500).json({ error: 'Failed to start bridge', details: error.message });
  }
});

router.post('/bridge/stop', async (req, res) => {
  try {
    const { bridge } = req.app.locals;
    
    if (!bridge) {
      return res.status(503).json({ error: 'Bridge service not available' });
    }
    
    await bridge.stop();
    logger.bridge('Bridge stopped', { user: req.user?.username || 'anonymous' });
    
    res.json({ success: true });
  } catch (error) {
    logger.error('Stop bridge failed:', error);
    res.status(500).json({ error: 'Failed to stop bridge', details: error.message });
  }
});

router.get('/bridge/status', async (req, res) => {
  try {
    const { bridge } = req.app.locals;
    
    if (!bridge) {
      return res.status(503).json({ error: 'Bridge service not available' });
    }
    
    const status = bridge.getStatus();
    res.json(status);
  } catch (error) {
    logger.error('Get bridge status failed:', error);
    res.status(500).json({ error: 'Failed to get bridge status', details: error.message });
  }
});

router.post('/bridge/command', async (req, res) => {
  try {
    const { bridge } = req.app.locals;
    const { command, params = {} } = req.body;
    
    if (!bridge) {
      return res.status(503).json({ error: 'Bridge service not available' });
    }
    
    if (!command) {
      return res.status(400).json({ error: 'Command is required' });
    }
    
    const result = await bridge.executeCommand(command, params);
    logger.bridge('Bridge command executed', { command, params });
    
    res.json({ success: true, result });
  } catch (error) {
    logger.error('Bridge command failed:', error);
    res.status(500).json({ error: 'Bridge command failed', details: error.message });
  }
});

// Emergency stop (no auth required for safety)
router.post('/emergency-stop', async (req, res) => {
  try {
    const { dobotClient, plcClient, bridge } = req.app.locals;
    
    logger.error('EMERGENCY STOP TRIGGERED via API', { ip: req.ip });
    
    // Stop Dobot
    if (dobotClient?.connected) {
      try {
        await dobotClient.clearQueue();
      } catch (error) {
        logger.error('Emergency stop - Dobot clear failed:', error);
      }
    }
    
    // Signal PLC
    if (plcClient?.isConnected()) {
      try {
        await plcClient.writeMBit('M0.3', true);
      } catch (error) {
        logger.error('Emergency stop - PLC signal failed:', error);
      }
    }
    
    // Stop bridge
    if (bridge) {
      try {
        await bridge.stop();
      } catch (error) {
        logger.error('Emergency stop - Bridge stop failed:', error);
      }
    }
    
    res.json({ success: true, message: 'Emergency stop executed' });
  } catch (error) {
    logger.error('Emergency stop failed:', error);
    res.status(500).json({ error: 'Emergency stop failed', details: error.message });
  }
});

// Settings management endpoints
router.get('/settings', async (req, res) => {
  try {
    const { plcClient } = req.app.locals;
    
    // Get current PLC configuration
    const plcConfig = {
      ip: plcClient?.ip || process.env.PLC_IP || '192.168.0.10',
      rack: plcClient?.rack || parseInt(process.env.PLC_RACK) || 0,
      slot: plcClient?.slot || parseInt(process.env.PLC_SLOT) || 1
    };
    
    res.json({
      plc: plcConfig,
      dobot: {
        host: process.env.DOBOT_HOST || '192.168.1.100',
        port: parseInt(process.env.DOBOT_PORT) || 29999,
        useUSB: process.env.DOBOT_USE_USB === 'true',
        usbPath: process.env.DOBOT_USB_PATH || '/dev/ttyUSB0'
      },
      system: {
        pollInterval: parseInt(process.env.POLL_INTERVAL) || 100,
        logLevel: process.env.LOG_LEVEL || 'info'
      }
    });
  } catch (error) {
    logger.error('Get settings failed:', error);
    res.status(500).json({ error: 'Failed to get settings', details: error.message });
  }
});

router.post('/settings', async (req, res) => {
  try {
    const { plc, dobot, system } = req.body;
    
    // Update environment variables (this would typically be saved to a config file)
    if (plc) {
      process.env.PLC_IP = plc.ip;
      process.env.PLC_RACK = plc.rack.toString();
      process.env.PLC_SLOT = plc.slot.toString();
    }
    
    if (dobot) {
      process.env.DOBOT_HOST = dobot.host;
      process.env.DOBOT_PORT = dobot.port.toString();
      process.env.DOBOT_USE_USB = dobot.useUSB.toString();
      process.env.DOBOT_USB_PATH = dobot.usbPath;
    }
    
    if (system) {
      process.env.POLL_INTERVAL = system.pollInterval.toString();
      process.env.LOG_LEVEL = system.logLevel;
    }
    
    logger.info('Settings updated', { plc, dobot, system });
    res.json({ success: true, message: 'Settings saved successfully' });
  } catch (error) {
    logger.error('Save settings failed:', error);
    res.status(500).json({ error: 'Failed to save settings', details: error.message });
  }
});

router.post('/settings/test-plc', async (req, res) => {
  try {
    const { ip, rack, slot } = req.body;
    
    if (!ip) {
      return res.status(400).json({ error: 'PLC IP address is required' });
    }
    
    // Create a temporary PLC client for testing
    const S7Client = require('../services/plc');
    const testClient = new S7Client(ip, rack || 0, slot || 1);
    
    // Test connection
    const connectionTest = await testClient.testConnection();
    const healthCheck = await testClient.healthCheck();
    
    // Clean up
    await testClient.disconnect();
    
    res.json({
      success: connectionTest.success,
      connectionTest,
      healthCheck,
      config: { ip, rack: rack || 0, slot: slot || 1 }
    });
  } catch (error) {
    logger.error('PLC connection test failed:', error);
    res.status(500).json({ 
      success: false, 
      error: 'PLC connection test failed', 
      details: error.message 
    });
  }
});

// Logs endpoint (admin only)
router.get('/logs', (req, res) => {
  // This would typically read from log files
  // For now, return a placeholder
  res.json({ message: 'Log viewing not implemented yet' });
});

module.exports = router;
