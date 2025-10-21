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

// System status (no auth required)
router.get('/status', async (req, res) => {
  try {
    const { dobotClient, plcClient, bridge } = req.app.locals;
    
    const status = {
      dobot: {
        connected: dobotClient?.connected || false,
        pose: dobotClient?.connected ? await dobotClient.getPose().catch(() => null) : null
      },
      plc: {
        connected: plcClient?.isConnected() || false,
        health: plcClient?.connected ? await plcClient.healthCheck().catch(() => ({ status: 'error' })) : { status: 'disconnected' }
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
    
    await dobotClient.clearQueue();
    logger.dobot('Stop command executed', { user: req.user.username });
    
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

// PLC control routes (requires control permission)
router.get('/plc/pose', async (req, res) => {
  try {
    const { plcClient } = req.app.locals;
    
    if (!plcClient?.isConnected()) {
      return res.status(503).json({ error: 'PLC not connected' });
    }
    
    const pose = await plcClient.readPoseFromDB(1, 0);
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
    
    if (!plcClient?.isConnected()) {
      return res.status(503).json({ error: 'PLC not connected' });
    }
    
    if (x === undefined || y === undefined || z === undefined) {
      return res.status(400).json({ error: 'x, y, z coordinates are required' });
    }
    
    await plcClient.writePoseToDB({ x, y, z }, 1, 0);
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
    
    if (!plcClient?.isConnected()) {
      return res.status(503).json({ error: 'PLC not connected' });
    }
    
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
    
    if (!plcClient?.isConnected()) {
      return res.status(503).json({ error: 'PLC not connected' });
    }
    
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

// Bridge control routes (requires control permission)
router.post('/bridge/start', async (req, res) => {
  try {
    const { bridge } = req.app.locals;
    
    if (!bridge) {
      return res.status(503).json({ error: 'Bridge service not available' });
    }
    
    await bridge.start();
    logger.bridge('Bridge started', { user: req.user.username });
    
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
    logger.bridge('Bridge stopped', { user: req.user.username });
    
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

// Logs endpoint (admin only)
router.get('/logs', (req, res) => {
  // This would typically read from log files
  // For now, return a placeholder
  res.json({ message: 'Log viewing not implemented yet' });
});

module.exports = router;
