// Test setup file
const path = require('path');

// Set test environment
process.env.NODE_ENV = 'test';
process.env.JWT_SECRET = 'test-secret-key';
process.env.LOG_LEVEL = 'error';

// Mock console methods to reduce noise in tests
global.console = {
  ...console,
  log: jest.fn(),
  debug: jest.fn(),
  info: jest.fn(),
  warn: jest.fn(),
  error: jest.fn()
};

// Increase timeout for integration tests
jest.setTimeout(10000);

// Global test utilities
global.testUtils = {
  generateTestToken: (user = { id: 1, username: 'test', role: 'operator', permissions: ['read', 'control'] }) => {
    const jwt = require('jsonwebtoken');
    return jwt.sign(user, process.env.JWT_SECRET, { expiresIn: '1h' });
  },
  
  mockDobotClient: {
    connected: true,
    getPose: jest.fn().mockResolvedValue({ x: 200, y: 0, z: 100, r: 0 }),
    home: jest.fn().mockResolvedValue(1),
    movePTP: jest.fn().mockResolvedValue(2),
    clearQueue: jest.fn().mockResolvedValue(),
    setSuctionCup: jest.fn().mockResolvedValue(),
    getStatus: jest.fn().mockResolvedValue({ queuedCmdIndex: 0, isIdle: true })
  },
  
  mockPlcClient: {
    isConnected: jest.fn().mockReturnValue(true),
    readPoseFromDB: jest.fn().mockResolvedValue({ x: 200, y: 0, z: 100 }),
    writePoseToDB: jest.fn().mockResolvedValue(),
    getControlBits: jest.fn().mockResolvedValue({ start: false, stop: false, home: false, estop: false }),
    setControlBits: jest.fn().mockResolvedValue(),
    healthCheck: jest.fn().mockResolvedValue({ status: 'connected' })
  },
  
  mockBridge: {
    getStatus: jest.fn().mockReturnValue({ running: true, isExecuting: false }),
    start: jest.fn().mockResolvedValue(),
    stop: jest.fn().mockResolvedValue(),
    executeCommand: jest.fn().mockResolvedValue({ success: true })
  }
};

// Clean up after each test
afterEach(() => {
  jest.clearAllMocks();
});
