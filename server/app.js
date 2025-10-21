require('dotenv').config();
const express = require('express');
const http = require('http');
const https = require('https');
const fs = require('fs');
const path = require('path');
const cors = require('cors');
const helmet = require('helmet');
const cookieParser = require('cookie-parser');
const rateLimit = require('express-rate-limit');
const { Server } = require('socket.io');

// Import services
const DobotClient = require('./services/dobot');
const S7Client = require('./services/plc');
const Bridge = require('./services/bridge');
const logger = require('./utils/logger');
const { socketAuth } = require('./middleware/auth');

// Import routes
const apiRoutes = require('./routes/api');

class DobotGateway {
  constructor() {
    this.app = express();
    this.server = null;
    this.io = null;
    this.dobotClient = null;
    this.plcClient = null;
    this.bridge = null;
    this.isShuttingDown = false;
  }

  async initialize() {
    try {
      // Initialize services
      await this.initializeServices();
      
      // Setup Express app
      this.setupExpress();
      
      // Setup Socket.io
      this.setupSocketIO();
      
      // Setup routes
      this.setupRoutes();
      
      // Setup error handling
      this.setupErrorHandling();
      
      // Setup graceful shutdown
      this.setupGracefulShutdown();
      
      logger.info('Dobot Gateway initialized successfully');
      
    } catch (error) {
      logger.error('Failed to initialize Dobot Gateway:', error);
      throw error;
    }
  }

  async initializeServices() {
    // Initialize Dobot client
    this.dobotClient = new DobotClient(
      process.env.DOBOT_HOST,
      parseInt(process.env.DOBOT_PORT),
      process.env.DOBOT_USE_USB === 'true',
      process.env.DOBOT_USB_PATH
    );

    // Initialize PLC client
    this.plcClient = new S7Client(
      process.env.PLC_IP,
      parseInt(process.env.PLC_RACK),
      parseInt(process.env.PLC_SLOT)
    );

    // Initialize Bridge
    this.bridge = new Bridge(this.dobotClient, this.plcClient, {
      pollInterval: parseInt(process.env.POLL_INTERVAL) || 100
    });

    // Setup service event handlers
    this.setupServiceEventHandlers();

    // Connect to services
    await this.connectToServices();
  }

  setupServiceEventHandlers() {
    // Dobot event handlers
    this.dobotClient.on('connected', () => {
      logger.dobot('Dobot connected');
      this.io?.emit('dobot_connected');
    });

    this.dobotClient.on('disconnected', () => {
      logger.dobot('Dobot disconnected');
      this.io?.emit('dobot_disconnected');
    });

    this.dobotClient.on('error', (error) => {
      logger.error('Dobot error:', error);
      this.io?.emit('dobot_error', { message: error.message });
    });

    // PLC event handlers
    this.plcClient.on?.('connected', () => {
      logger.plc('PLC connected');
      this.io?.emit('plc_connected');
    });

    this.plcClient.on?.('disconnected', () => {
      logger.plc('PLC disconnected');
      this.io?.emit('plc_disconnected');
    });

    // Bridge event handlers
    this.bridge.on('started', () => {
      logger.bridge('Bridge started');
      this.io?.emit('bridge_started');
    });

    this.bridge.on('stopped', () => {
      logger.bridge('Bridge stopped');
      this.io?.emit('bridge_stopped');
    });

    this.bridge.on('pose_updated', (pose) => {
      this.io?.emit('pose_updated', pose);
    });

    this.bridge.on('movement_started', (data) => {
      this.io?.emit('movement_started', data);
    });

    this.bridge.on('movement_stopped', () => {
      this.io?.emit('movement_stopped');
    });

    this.bridge.on('homing_started', (data) => {
      this.io?.emit('homing_started', data);
    });

    this.bridge.on('emergency_stop', () => {
      logger.error('Emergency stop triggered');
      this.io?.emit('emergency_stop');
    });

    this.bridge.on('error', (error) => {
      logger.error('Bridge error:', error);
      this.io?.emit('bridge_error', { message: error.message });
    });
  }

  async connectToServices() {
    try {
      // Connect to Dobot
      logger.info('Connecting to Dobot...');
      await this.dobotClient.connect();
      
      // Connect to PLC
      logger.info('Connecting to PLC...');
      await this.plcClient.connect();
      
      // Start bridge
      logger.info('Starting bridge service...');
      await this.bridge.start();
      
    } catch (error) {
      logger.error('Failed to connect to services:', error);
      // Don't throw - allow server to start even if services are unavailable
    }
  }

  setupExpress() {
    // Security middleware - Adjust CSP for HTTP vs HTTPS
    const isHTTPS = process.env.NODE_ENV === 'production';
    this.app.use(helmet({
      contentSecurityPolicy: {
        directives: {
          defaultSrc: ["'self'"],
          styleSrc: ["'self'", "'unsafe-inline'"],
          scriptSrc: ["'self'"],
          imgSrc: ["'self'", "data:", "https:"],
          connectSrc: ["'self'", "wss:", "ws:"],
          upgradeInsecureRequests: isHTTPS ? [] : null
        }
      }
    }));

    // CORS configuration
    this.app.use(cors({
      origin: process.env.NODE_ENV === 'production' 
        ? ['https://raspberrypi.local', 'https://localhost'] 
        : true,
      credentials: true
    }));

    // Rate limiting
    const limiter = rateLimit({
      windowMs: 15 * 60 * 1000, // 15 minutes
      max: 100, // limit each IP to 100 requests per windowMs
      message: 'Too many requests from this IP'
    });
    this.app.use(limiter);

    // Body parsing
    this.app.use(express.json({ limit: '10mb' }));
    this.app.use(express.urlencoded({ extended: true }));
    this.app.use(cookieParser());

    // Request logging
    this.app.use(logger.request);

    // Serve static files from client build
    const clientBuildPath = path.join(__dirname, '../client/dist');
    if (fs.existsSync(clientBuildPath)) {
      this.app.use(express.static(clientBuildPath));
    }

    // Store services in app locals for route access
    this.app.locals.dobotClient = this.dobotClient;
    this.app.locals.plcClient = this.plcClient;
    this.app.locals.bridge = this.bridge;
  }

  setupSocketIO() {
    this.server = this.createServer();
    
    this.io = new Server(this.server, {
      cors: {
        origin: process.env.NODE_ENV === 'production' 
          ? ['https://raspberrypi.local', 'https://localhost'] 
          : true,
        credentials: true
      },
      perMessageDeflate: {
        threshold: 1024,
        zlibDeflateOptions: {
          chunkSize: 1024,
          memLevel: 7,
          level: 3
        }
      }
    });

    // Socket authentication
    this.io.use(socketAuth);

    // Socket connection handling
    this.io.on('connection', (socket) => {
      logger.info('Client connected', { 
        username: socket.user.username,
        socketId: socket.id 
      });

      // Send initial status
      socket.emit('status', {
        dobot: { connected: this.dobotClient.connected },
        plc: { connected: this.plcClient.isConnected() },
        bridge: this.bridge.getStatus()
      });

      // Handle client commands
      socket.on('dobot_command', async (data) => {
        try {
          const { command, params } = data;
          const result = await this.bridge.executeCommand(command, params);
          socket.emit('command_result', { success: true, result });
        } catch (error) {
          socket.emit('command_result', { success: false, error: error.message });
        }
      });

      socket.on('disconnect', () => {
        logger.info('Client disconnected', { socketId: socket.id });
      });
    });
  }

  createServer() {
    const port = parseInt(process.env.PORT) || 443;
    const httpPort = parseInt(process.env.HTTP_PORT) || 8080;

    if (process.env.NODE_ENV === 'production' && fs.existsSync(process.env.SSL_KEY_PATH) && fs.existsSync(process.env.SSL_CERT_PATH)) {
      // HTTPS server
      const options = {
        key: fs.readFileSync(process.env.SSL_KEY_PATH),
        cert: fs.readFileSync(process.env.SSL_CERT_PATH)
      };
      
      const httpsServer = https.createServer(options, this.app);
      httpsServer.listen(port, () => {
        logger.info(`HTTPS server running on port ${port}`);
      });

      // Also start HTTP server for redirects
      const httpServer = http.createServer((req, res) => {
        res.writeHead(301, { Location: `https://${req.headers.host}${req.url}` });
        res.end();
      });
      httpServer.listen(httpPort, () => {
        logger.info(`HTTP server running on port ${httpPort} (redirects to HTTPS)`);
      });

      return httpsServer;
    } else {
      // HTTP server for development
      const httpServer = http.createServer(this.app);
      httpServer.listen(httpPort, () => {
        logger.info(`HTTP server running on port ${httpPort}`);
      });
      return httpServer;
    }
  }

  setupRoutes() {
    // API routes
    this.app.use('/api', apiRoutes);

    // Health check endpoint
    this.app.get('/health', (req, res) => {
      res.json({ 
        status: 'ok', 
        timestamp: Date.now(),
        uptime: process.uptime()
      });
    });

    // Serve React app for all other routes
    this.app.get('*', (req, res) => {
      const clientBuildPath = path.join(__dirname, '../client/dist/index.html');
      if (fs.existsSync(clientBuildPath)) {
        res.sendFile(clientBuildPath);
      } else {
        res.status(404).json({ error: 'Client not built. Run npm run build:client' });
      }
    });
  }

  setupErrorHandling() {
    // 404 handler
    this.app.use((req, res) => {
      res.status(404).json({ error: 'Not found' });
    });

    // Global error handler
    this.app.use((error, req, res, next) => {
      logger.error('Unhandled error:', error);
      res.status(500).json({ 
        error: 'Internal server error',
        ...(process.env.NODE_ENV === 'development' && { details: error.message })
      });
    });

    // Handle uncaught exceptions
    process.on('uncaughtException', (error) => {
      logger.error('Uncaught Exception:', error);
      this.shutdown(1);
    });

    // Handle unhandled promise rejections
    process.on('unhandledRejection', (reason, promise) => {
      logger.error('Unhandled Rejection at:', promise, 'reason:', reason);
      this.shutdown(1);
    });
  }

  setupGracefulShutdown() {
    const signals = ['SIGTERM', 'SIGINT', 'SIGUSR2'];
    
    signals.forEach(signal => {
      process.on(signal, () => {
        logger.info(`Received ${signal}, shutting down gracefully`);
        this.shutdown(0);
      });
    });
  }

  async shutdown(code = 0) {
    if (this.isShuttingDown) return;
    this.isShuttingDown = true;

    logger.info('Shutting down Dobot Gateway...');

    try {
      // Stop bridge
      if (this.bridge) {
        await this.bridge.stop();
      }

      // Disconnect from services
      if (this.dobotClient) {
        await this.dobotClient.disconnect();
      }

      if (this.plcClient) {
        await this.plcClient.disconnect();
      }

      // Close server
      if (this.server) {
        this.server.close(() => {
          logger.info('Server closed');
          process.exit(code);
        });
      } else {
        process.exit(code);
      }

    } catch (error) {
      logger.error('Error during shutdown:', error);
      process.exit(1);
    }
  }
}

// Start the application
if (require.main === module) {
  const gateway = new DobotGateway();
  
  gateway.initialize().catch(error => {
    logger.error('Failed to start Dobot Gateway:', error);
    process.exit(1);
  });
}

module.exports = DobotGateway;
