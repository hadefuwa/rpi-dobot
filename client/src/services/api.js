import axios from 'axios';

// Create axios instance
const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
  withCredentials: true
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add timestamp to prevent caching
    if (config.method === 'get') {
      config.params = {
        ...config.params,
        _t: Date.now()
      };
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // Handle common errors
    if (error.response?.status === 401) {
      // Unauthorized - redirect to login
      window.location.href = '/login';
    } else if (error.response?.status === 403) {
      // Forbidden
      console.error('Access forbidden:', error.response.data);
    } else if (error.response?.status >= 500) {
      // Server error
      console.error('Server error:', error.response.data);
    }
    
    return Promise.reject(error);
  }
);

// API methods
export const dobotAPI = {
  // Get current pose
  getPose: () => api.get('/dobot/pose'),
  
  // Get status
  getStatus: () => api.get('/dobot/status'),
  
  // Home command
  home: () => api.post('/dobot/home'),
  
  // Move command
  move: (x, y, z, r = 0) => api.post('/dobot/move', { x, y, z, r }),
  
  // Stop command
  stop: () => api.post('/dobot/stop'),
  
  // Suction cup control
  setSuctionCup: (enable) => api.post('/dobot/suction', { enable })
};

export const plcAPI = {
  // Get pose from PLC
  getPose: () => api.get('/plc/pose'),
  
  // Set pose in PLC
  setPose: (x, y, z) => api.post('/plc/pose', { x, y, z }),
  
  // Get control bits
  getControl: () => api.get('/plc/control'),
  
  // Set control bits
  setControl: (bits) => api.post('/plc/control', bits)
};

export const bridgeAPI = {
  // Get bridge status
  getStatus: () => api.get('/bridge/status'),
  
  // Start bridge
  start: () => api.post('/bridge/start'),
  
  // Stop bridge
  stop: () => api.post('/bridge/stop'),
  
  // Execute command
  executeCommand: (command, params = {}) => 
    api.post('/bridge/command', { command, params })
};

export const systemAPI = {
  // Get system status
  getStatus: () => api.get('/status'),
  
  // Health check
  health: () => api.get('/health'),
  
  // Emergency stop
  emergencyStop: () => api.post('/emergency-stop')
};

export { api };
