const request = require('supertest');
const jwt = require('jsonwebtoken');

// Mock the services
jest.mock('../../server/services/dobot');
jest.mock('../../server/services/plc');
jest.mock('../../server/services/bridge');

const DobotClient = require('../../server/services/dobot');
const S7Client = require('../../server/services/plc');
const Bridge = require('../../server/services/bridge');

// Create a test app
const express = require('express');
const app = express();
app.use(express.json());

// Mock services
const mockDobotClient = {
  connected: true,
  getPose: jest.fn().mockResolvedValue({ x: 200, y: 0, z: 100, r: 0 }),
  home: jest.fn().mockResolvedValue(1),
  movePTP: jest.fn().mockResolvedValue(2),
  clearQueue: jest.fn().mockResolvedValue(),
  setSuctionCup: jest.fn().mockResolvedValue(),
  getStatus: jest.fn().mockResolvedValue({ queuedCmdIndex: 0, isIdle: true })
};

const mockPlcClient = {
  isConnected: jest.fn().mockReturnValue(true),
  readPoseFromDB: jest.fn().mockResolvedValue({ x: 200, y: 0, z: 100 }),
  writePoseToDB: jest.fn().mockResolvedValue(),
  getControlBits: jest.fn().mockResolvedValue({ start: false, stop: false, home: false, estop: false }),
  setControlBits: jest.fn().mockResolvedValue(),
  healthCheck: jest.fn().mockResolvedValue({ status: 'connected' })
};

const mockBridge = {
  getStatus: jest.fn().mockReturnValue({ running: true, isExecuting: false }),
  start: jest.fn().mockResolvedValue(),
  stop: jest.fn().mockResolvedValue(),
  executeCommand: jest.fn().mockResolvedValue({ success: true })
};

// Set up app locals
app.locals.dobotClient = mockDobotClient;
app.locals.plcClient = mockPlcClient;
app.locals.bridge = mockBridge;

// Add auth middleware
const { verifyToken, requirePermission } = require('../../server/middleware/auth');
app.use('/api', verifyToken);
app.use('/api', requirePermission('read'));

// Add API routes
const apiRoutes = require('../../server/routes/api');
app.use('/api', apiRoutes);

// Helper function to generate test token
function generateTestToken(user = { id: 1, username: 'test', role: 'operator', permissions: ['read', 'control'] }) {
  return jwt.sign(user, process.env.JWT_SECRET || 'test-secret', { expiresIn: '1h' });
}

describe('API Integration Tests', () => {
  let token;

  beforeEach(() => {
    token = generateTestToken();
    jest.clearAllMocks();
  });

  describe('Authentication', () => {
    test('GET /api/status requires authentication', async () => {
      const response = await request(app)
        .get('/api/status');
      
      expect(response.status).toBe(401);
      expect(response.body.error).toBe('No token provided');
    });

    test('GET /api/status with valid token succeeds', async () => {
      const response = await request(app)
        .get('/api/status')
        .set('Authorization', `Bearer ${token}`);
      
      expect(response.status).toBe(200);
      expect(response.body).toHaveProperty('dobot');
      expect(response.body).toHaveProperty('plc');
      expect(response.body).toHaveProperty('bridge');
    });
  });

  describe('Dobot API', () => {
    test('POST /api/dobot/home executes home command', async () => {
      const response = await request(app)
        .post('/api/dobot/home')
        .set('Authorization', `Bearer ${token}`);
      
      expect(response.status).toBe(200);
      expect(response.body.success).toBe(true);
      expect(response.body.queuedIndex).toBe(1);
      expect(mockDobotClient.home).toHaveBeenCalled();
    });

    test('POST /api/dobot/move executes move command', async () => {
      const moveData = { x: 100, y: 200, z: 150, r: 45 };
      
      const response = await request(app)
        .post('/api/dobot/move')
        .set('Authorization', `Bearer ${token}`)
        .send(moveData);
      
      expect(response.status).toBe(200);
      expect(response.body.success).toBe(true);
      expect(mockDobotClient.movePTP).toHaveBeenCalledWith(100, 200, 150, 45);
    });

    test('POST /api/dobot/move validates coordinates', async () => {
      const invalidMoveData = { x: 500, y: 200, z: 150 }; // X out of range
      
      const response = await request(app)
        .post('/api/dobot/move')
        .set('Authorization', `Bearer ${token}`)
        .send(invalidMoveData);
      
      expect(response.status).toBe(500);
      expect(response.body.error).toContain('Move command failed');
    });

    test('POST /api/dobot/stop executes stop command', async () => {
      const response = await request(app)
        .post('/api/dobot/stop')
        .set('Authorization', `Bearer ${token}`);
      
      expect(response.status).toBe(200);
      expect(response.body.success).toBe(true);
      expect(mockDobotClient.clearQueue).toHaveBeenCalled();
    });

    test('POST /api/dobot/suction controls suction cup', async () => {
      const response = await request(app)
        .post('/api/dobot/suction')
        .set('Authorization', `Bearer ${token}`)
        .send({ enable: true });
      
      expect(response.status).toBe(200);
      expect(response.body.success).toBe(true);
      expect(response.body.enabled).toBe(true);
      expect(mockDobotClient.setSuctionCup).toHaveBeenCalledWith(true);
    });

    test('GET /api/dobot/pose returns current pose', async () => {
      const response = await request(app)
        .get('/api/dobot/pose')
        .set('Authorization', `Bearer ${token}`);
      
      expect(response.status).toBe(200);
      expect(response.body).toEqual({ x: 200, y: 0, z: 100, r: 0 });
      expect(mockDobotClient.getPose).toHaveBeenCalled();
    });

    test('handles dobot not connected', async () => {
      mockDobotClient.connected = false;
      
      const response = await request(app)
        .post('/api/dobot/home')
        .set('Authorization', `Bearer ${token}`);
      
      expect(response.status).toBe(503);
      expect(response.body.error).toBe('Dobot not connected');
    });
  });

  describe('PLC API', () => {
    test('GET /api/plc/pose returns PLC pose', async () => {
      const response = await request(app)
        .get('/api/plc/pose')
        .set('Authorization', `Bearer ${token}`);
      
      expect(response.status).toBe(200);
      expect(response.body).toEqual({ x: 200, y: 0, z: 100 });
      expect(mockPlcClient.readPoseFromDB).toHaveBeenCalledWith(1, 0);
    });

    test('POST /api/plc/pose writes pose to PLC', async () => {
      const poseData = { x: 100, y: 200, z: 150 };
      
      const response = await request(app)
        .post('/api/plc/pose')
        .set('Authorization', `Bearer ${token}`)
        .send(poseData);
      
      expect(response.status).toBe(200);
      expect(response.body.success).toBe(true);
      expect(mockPlcClient.writePoseToDB).toHaveBeenCalledWith(poseData, 1, 0);
    });

    test('GET /api/plc/control returns control bits', async () => {
      const response = await request(app)
        .get('/api/plc/control')
        .set('Authorization', `Bearer ${token}`);
      
      expect(response.status).toBe(200);
      expect(response.body).toEqual({ start: false, stop: false, home: false, estop: false });
      expect(mockPlcClient.getControlBits).toHaveBeenCalled();
    });

    test('POST /api/plc/control sets control bits', async () => {
      const controlData = { start: true, home: true };
      
      const response = await request(app)
        .post('/api/plc/control')
        .set('Authorization', `Bearer ${token}`)
        .send(controlData);
      
      expect(response.status).toBe(200);
      expect(response.body.success).toBe(true);
      expect(mockPlcClient.setControlBits).toHaveBeenCalledWith(controlData);
    });

    test('handles PLC not connected', async () => {
      mockPlcClient.isConnected.mockReturnValue(false);
      
      const response = await request(app)
        .get('/api/plc/pose')
        .set('Authorization', `Bearer ${token}`);
      
      expect(response.status).toBe(503);
      expect(response.body.error).toBe('PLC not connected');
    });
  });

  describe('Bridge API', () => {
    test('GET /api/bridge/status returns bridge status', async () => {
      const response = await request(app)
        .get('/api/bridge/status')
        .set('Authorization', `Bearer ${token}`);
      
      expect(response.status).toBe(200);
      expect(response.body).toEqual({ running: true, isExecuting: false });
      expect(mockBridge.getStatus).toHaveBeenCalled();
    });

    test('POST /api/bridge/start starts bridge', async () => {
      const response = await request(app)
        .post('/api/bridge/start')
        .set('Authorization', `Bearer ${token}`);
      
      expect(response.status).toBe(200);
      expect(response.body.success).toBe(true);
      expect(mockBridge.start).toHaveBeenCalled();
    });

    test('POST /api/bridge/stop stops bridge', async () => {
      const response = await request(app)
        .post('/api/bridge/stop')
        .set('Authorization', `Bearer ${token}`);
      
      expect(response.status).toBe(200);
      expect(response.body.success).toBe(true);
      expect(mockBridge.stop).toHaveBeenCalled();
    });

    test('POST /api/bridge/command executes command', async () => {
      const commandData = { command: 'home', params: {} };
      
      const response = await request(app)
        .post('/api/bridge/command')
        .set('Authorization', `Bearer ${token}`)
        .send(commandData);
      
      expect(response.status).toBe(200);
      expect(response.body.success).toBe(true);
      expect(mockBridge.executeCommand).toHaveBeenCalledWith('home', {});
    });
  });

  describe('Emergency Stop', () => {
    test('POST /api/emergency-stop works without authentication', async () => {
      const response = await request(app)
        .post('/api/emergency-stop');
      
      expect(response.status).toBe(200);
      expect(response.body.success).toBe(true);
      expect(response.body.message).toBe('Emergency stop executed');
    });

    test('POST /api/emergency-stop calls all stop methods', async () => {
      await request(app)
        .post('/api/emergency-stop');
      
      expect(mockDobotClient.clearQueue).toHaveBeenCalled();
      expect(mockPlcClient.writeMBit).toHaveBeenCalledWith('M0.3', true);
      expect(mockBridge.stop).toHaveBeenCalled();
    });
  });

  describe('Error Handling', () => {
    test('handles service errors gracefully', async () => {
      mockDobotClient.home.mockRejectedValue(new Error('Dobot error'));
      
      const response = await request(app)
        .post('/api/dobot/home')
        .set('Authorization', `Bearer ${token}`);
      
      expect(response.status).toBe(500);
      expect(response.body.error).toBe('Home command failed');
      expect(response.body.details).toBe('Dobot error');
    });

    test('handles missing parameters', async () => {
      const response = await request(app)
        .post('/api/dobot/move')
        .set('Authorization', `Bearer ${token}`)
        .send({ x: 100 }); // Missing y, z
      
      expect(response.status).toBe(400);
      expect(response.body.error).toBe('x, y, z coordinates are required');
    });
  });
});
