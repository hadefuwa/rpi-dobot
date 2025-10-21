const jwt = require('jsonwebtoken');
const bcrypt = require('bcrypt');
const logger = require('../utils/logger');

const JWT_SECRET = process.env.JWT_SECRET || 'change-me-in-production';
const JWT_EXPIRES_IN = process.env.JWT_EXPIRES_IN || '8h';
const SALT_ROUNDS = parseInt(process.env.SALT_ROUNDS) || 12;

// Default users (in production, use a database)
const users = [
  {
    id: 1,
    username: 'admin',
    password: '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/8QzQK2a', // 'admin123'
    role: 'admin',
    permissions: ['read', 'write', 'control', 'admin']
  },
  {
    id: 2,
    username: 'operator',
    password: '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/8QzQK2a', // 'operator123'
    role: 'operator',
    permissions: ['read', 'control']
  },
  {
    id: 3,
    username: 'viewer',
    password: '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/8QzQK2a', // 'viewer123'
    role: 'viewer',
    permissions: ['read']
  }
];

// Generate JWT token
function generateToken(user) {
  const payload = {
    id: user.id,
    username: user.username,
    role: user.role,
    permissions: user.permissions
  };
  
  return jwt.sign(payload, JWT_SECRET, { 
    expiresIn: JWT_EXPIRES_IN,
    issuer: 'dobot-gateway',
    audience: 'dobot-gateway-client'
  });
}

// Verify JWT token
function verifyToken(req, res, next) {
  const token = req.cookies.token || 
                req.headers.authorization?.split(' ')[1] ||
                req.query.token;

  if (!token) {
    logger.security('No token provided', { ip: req.ip, url: req.url });
    return res.status(401).json({ 
      error: 'No token provided',
      code: 'NO_TOKEN'
    });
  }

  try {
    const decoded = jwt.verify(token, JWT_SECRET, {
      issuer: 'dobot-gateway',
      audience: 'dobot-gateway-client'
    });
    
    req.user = decoded;
    logger.security('Token verified', { 
      username: decoded.username, 
      role: decoded.role,
      ip: req.ip 
    });
    next();
  } catch (error) {
    logger.security('Invalid token', { 
      error: error.message, 
      ip: req.ip, 
      url: req.url 
    });
    
    if (error.name === 'TokenExpiredError') {
      return res.status(401).json({ 
        error: 'Token expired',
        code: 'TOKEN_EXPIRED'
      });
    } else if (error.name === 'JsonWebTokenError') {
      return res.status(401).json({ 
        error: 'Invalid token',
        code: 'INVALID_TOKEN'
      });
    } else {
      return res.status(401).json({ 
        error: 'Token verification failed',
        code: 'TOKEN_VERIFICATION_FAILED'
      });
    }
  }
}

// Check if user has required permission
function requirePermission(permission) {
  return (req, res, next) => {
    if (!req.user) {
      return res.status(401).json({ 
        error: 'Authentication required',
        code: 'AUTH_REQUIRED'
      });
    }

    if (!req.user.permissions || !req.user.permissions.includes(permission)) {
      logger.security('Insufficient permissions', { 
        username: req.user.username,
        required: permission,
        has: req.user.permissions,
        ip: req.ip
      });
      return res.status(403).json({ 
        error: 'Insufficient permissions',
        code: 'INSUFFICIENT_PERMISSIONS',
        required: permission
      });
    }

    next();
  };
}

// Check if user has required role
function requireRole(role) {
  return (req, res, next) => {
    if (!req.user) {
      return res.status(401).json({ 
        error: 'Authentication required',
        code: 'AUTH_REQUIRED'
      });
    }

    if (req.user.role !== role && req.user.role !== 'admin') {
      logger.security('Insufficient role', { 
        username: req.user.username,
        required: role,
        has: req.user.role,
        ip: req.ip
      });
      return res.status(403).json({ 
        error: 'Insufficient role',
        code: 'INSUFFICIENT_ROLE',
        required: role
      });
    }

    next();
  };
}

// Login endpoint handler
async function login(req, res) {
  try {
    const { username, password } = req.body;

    if (!username || !password) {
      return res.status(400).json({ 
        error: 'Username and password required',
        code: 'MISSING_CREDENTIALS'
      });
    }

    // Find user
    const user = users.find(u => u.username === username);
    if (!user) {
      logger.security('Login attempt with unknown username', { username, ip: req.ip });
      return res.status(401).json({ 
        error: 'Invalid credentials',
        code: 'INVALID_CREDENTIALS'
      });
    }

    // Verify password
    const isValidPassword = await bcrypt.compare(password, user.password);
    if (!isValidPassword) {
      logger.security('Login attempt with invalid password', { username, ip: req.ip });
      return res.status(401).json({ 
        error: 'Invalid credentials',
        code: 'INVALID_CREDENTIALS'
      });
    }

    // Generate token
    const token = generateToken(user);
    
    // Set HTTP-only cookie
    res.cookie('token', token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'strict',
      maxAge: 8 * 60 * 60 * 1000 // 8 hours
    });

    logger.security('User logged in successfully', { 
      username: user.username, 
      role: user.role,
      ip: req.ip 
    });

    res.json({
      success: true,
      user: {
        id: user.id,
        username: user.username,
        role: user.role,
        permissions: user.permissions
      },
      token // Also return token for API clients
    });

  } catch (error) {
    logger.error('Login error:', error);
    res.status(500).json({ 
      error: 'Internal server error',
      code: 'LOGIN_ERROR'
    });
  }
}

// Logout endpoint handler
function logout(req, res) {
  res.clearCookie('token');
  logger.security('User logged out', { 
    username: req.user?.username,
    ip: req.ip 
  });
  res.json({ success: true, message: 'Logged out successfully' });
}

// Get current user info
function getCurrentUser(req, res) {
  if (!req.user) {
    return res.status(401).json({ 
      error: 'Not authenticated',
      code: 'NOT_AUTHENTICATED'
    });
  }

  res.json({
    user: {
      id: req.user.id,
      username: req.user.username,
      role: req.user.role,
      permissions: req.user.permissions
    }
  });
}

// Socket.io authentication middleware
function socketAuth(socket, next) {
  const token = socket.handshake.auth.token || socket.handshake.query.token;
  
  if (!token) {
    logger.security('Socket connection without token', { 
      ip: socket.handshake.address 
    });
    return next(new Error('Authentication required'));
  }

  try {
    const decoded = jwt.verify(token, JWT_SECRET, {
      issuer: 'dobot-gateway',
      audience: 'dobot-gateway-client'
    });
    
    socket.user = decoded;
    logger.security('Socket authenticated', { 
      username: decoded.username,
      ip: socket.handshake.address 
    });
    next();
  } catch (error) {
    logger.security('Socket authentication failed', { 
      error: error.message,
      ip: socket.handshake.address 
    });
    next(new Error('Authentication failed'));
  }
}

// Rate limiting for auth endpoints
const authAttempts = new Map();
const MAX_ATTEMPTS = 5;
const WINDOW_MS = 15 * 60 * 1000; // 15 minutes

function authRateLimit(req, res, next) {
  const ip = req.ip;
  const now = Date.now();
  
  if (!authAttempts.has(ip)) {
    authAttempts.set(ip, { count: 0, resetTime: now + WINDOW_MS });
  }
  
  const attempts = authAttempts.get(ip);
  
  if (now > attempts.resetTime) {
    attempts.count = 0;
    attempts.resetTime = now + WINDOW_MS;
  }
  
  if (attempts.count >= MAX_ATTEMPTS) {
    logger.security('Too many auth attempts', { ip, attempts: attempts.count });
    return res.status(429).json({
      error: 'Too many authentication attempts',
      code: 'TOO_MANY_ATTEMPTS',
      retryAfter: Math.ceil((attempts.resetTime - now) / 1000)
    });
  }
  
  attempts.count++;
  next();
}

module.exports = {
  generateToken,
  verifyToken,
  requirePermission,
  requireRole,
  login,
  logout,
  getCurrentUser,
  socketAuth,
  authRateLimit,
  users
};
