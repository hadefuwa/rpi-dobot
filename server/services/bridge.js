const { EventEmitter } = require('events');
const logger = require('../utils/logger');

class Bridge extends EventEmitter {
  constructor(dobot, plc, config = {}) {
    super();
    this.dobot = dobot;
    this.plc = plc;
    this.config = {
      pollInterval: config.pollInterval || 100,
      maxRetries: config.maxRetries || 3,
      retryDelay: config.retryDelay || 1000,
      ...config
    };
    
    this.state = {
      running: false,
      lastStartBit: false,
      lastStopBit: false,
      lastHomeBit: false,
      lastEStopBit: false,
      isExecuting: false,
      currentPose: { x: 0, y: 0, z: 0, r: 0 },
      lastPoseUpdate: 0,
      errorCount: 0,
      lastError: null
    };
    
    this.pollTimer = null;
    this.retryCount = 0;
    this.isPolling = false;
  }

  async start() {
    if (this.state.running) {
      logger.warn('Bridge is already running');
      return;
    }

    try {
      // Verify connections
      if (!this.dobot.connected) {
        throw new Error('Dobot not connected');
      }
      if (!this.plc.isConnected()) {
        throw new Error('PLC not connected');
      }

      this.state.running = true;
      this.state.errorCount = 0;
      this.state.lastError = null;
      
      logger.info('Starting bridge service');
      this.emit('started');
      
      // Start polling loop
      this.startPolling();
      
    } catch (error) {
      logger.error('Failed to start bridge:', error);
      this.state.running = false;
      throw error;
    }
  }

  async stop() {
    if (!this.state.running) {
      logger.warn('Bridge is not running');
      return;
    }

    this.state.running = false;
    this.stopPolling();
    
    logger.info('Bridge service stopped');
    this.emit('stopped');
  }

  startPolling() {
    if (this.isPolling) return;
    
    this.isPolling = true;
    this.poll();
  }

  stopPolling() {
    this.isPolling = false;
    if (this.pollTimer) {
      clearTimeout(this.pollTimer);
      this.pollTimer = null;
    }
  }

  async poll() {
    if (!this.state.running || !this.isPolling) return;

    try {
      await this.processCycle();
      this.state.errorCount = 0;
      this.retryCount = 0;
      
    } catch (error) {
      this.state.errorCount++;
      this.state.lastError = error;
      logger.error(`Bridge poll error (${this.state.errorCount}):`, error);
      
      // If too many errors, stop polling
      if (this.state.errorCount >= this.config.maxRetries) {
        logger.error('Too many bridge errors, stopping polling');
        this.state.running = false;
        this.emit('error', error);
        return;
      }
      
      // Wait before retrying
      await this.delay(this.config.retryDelay);
    }

    // Schedule next poll
    this.pollTimer = setTimeout(() => this.poll(), this.config.pollInterval);
  }

  async processCycle() {
    // Read PLC control bits
    const controlBits = await this.plc.getControlBits();
    
    // Handle emergency stop
    if (controlBits.estop && !this.state.lastEStopBit) {
      await this.handleEmergencyStop();
      this.state.lastEStopBit = controlBits.estop;
      return;
    }
    
    // Reset emergency stop state
    if (!controlBits.estop && this.state.lastEStopBit) {
      this.state.lastEStopBit = false;
      logger.info('Emergency stop cleared');
    }

    // Handle start command (edge detection)
    if (controlBits.start && !this.state.lastStartBit && !this.state.isExecuting) {
      await this.handleStartCommand();
    }

    // Handle home command (edge detection)
    if (controlBits.home && !this.state.lastHomeBit && !this.state.isExecuting) {
      await this.handleHomeCommand();
    }

    // Handle stop command (edge detection)
    if (controlBits.stop && !this.state.lastStopBit && this.state.isExecuting) {
      await this.handleStopCommand();
    }

    // Update pose feedback to PLC
    await this.updatePoseFeedback();

    // Update state tracking
    this.state.lastStartBit = controlBits.start;
    this.state.lastStopBit = controlBits.stop;
    this.state.lastHomeBit = controlBits.home;
  }

  async handleStartCommand() {
    try {
      logger.info('Processing start command from PLC');
      this.state.isExecuting = true;
      
      // Read target position from PLC
      const targetPose = await this.plc.readPoseFromDB(1, 0);
      
      // Validate coordinates
      this.validateCoordinates(targetPose.x, targetPose.y, targetPose.z);
      
      // Execute movement
      const queuedIndex = await this.dobot.movePTP(
        targetPose.x, 
        targetPose.y, 
        targetPose.z, 
        0 // Default R rotation
      );
      
      logger.info(`Movement queued with index ${queuedIndex}`);
      
      // Reset start bit in PLC
      await this.plc.writeMBit('M0.0', false);
      
      // Update status in PLC
      await this.plc.writeStatusToDB(1, 1); // Status: Executing
      
      this.emit('movement_started', { targetPose, queuedIndex });
      
    } catch (error) {
      logger.error('Start command failed:', error);
      await this.plc.writeStatusToDB(2, 1); // Status: Error
      this.state.isExecuting = false;
      throw error;
    }
  }

  async handleHomeCommand() {
    try {
      logger.info('Processing home command from PLC');
      this.state.isExecuting = true;
      
      // Execute home command
      const queuedIndex = await this.dobot.home();
      
      logger.info(`Home command queued with index ${queuedIndex}`);
      
      // Reset home bit in PLC
      await this.plc.writeMBit('M0.2', false);
      
      // Update status in PLC
      await this.plc.writeStatusToDB(3, 1); // Status: Homing
      
      this.emit('homing_started', { queuedIndex });
      
    } catch (error) {
      logger.error('Home command failed:', error);
      await this.plc.writeStatusToDB(2, 1); // Status: Error
      this.state.isExecuting = false;
      throw error;
    }
  }

  async handleStopCommand() {
    try {
      logger.info('Processing stop command from PLC');
      
      // Clear Dobot command queue
      await this.dobot.clearQueue();
      
      // Reset stop bit in PLC
      await this.plc.writeMBit('M0.1', false);
      
      // Update status in PLC
      await this.plc.writeStatusToDB(4, 1); // Status: Stopped
      
      this.state.isExecuting = false;
      this.emit('movement_stopped');
      
    } catch (error) {
      logger.error('Stop command failed:', error);
      throw error;
    }
  }

  async handleEmergencyStop() {
    try {
      logger.error('EMERGENCY STOP TRIGGERED');
      
      // Clear Dobot command queue immediately
      await this.dobot.clearQueue();
      
      // Update status in PLC
      await this.plc.writeStatusToDB(5, 1); // Status: Emergency Stop
      
      this.state.isExecuting = false;
      this.emit('emergency_stop');
      
    } catch (error) {
      logger.error('Emergency stop handling failed:', error);
      throw error;
    }
  }

  async updatePoseFeedback() {
    try {
      // Only update pose if enough time has passed (avoid excessive updates)
      const now = Date.now();
      if (now - this.state.lastPoseUpdate < 50) { // 20Hz max
        return;
      }

      // Get current pose from Dobot
      const currentPose = await this.dobot.getPose();
      
      // Check if pose has changed significantly
      const poseChanged = this.hasPoseChanged(currentPose);
      
      if (poseChanged) {
        // Write pose to PLC
        await this.plc.writePoseToDB(currentPose, 1, 12);
        
        // Update internal state
        this.state.currentPose = currentPose;
        this.state.lastPoseUpdate = now;
        
        // Emit pose update event
        this.emit('pose_updated', currentPose);
        
        logger.debug('Pose updated', currentPose);
      }
      
    } catch (error) {
      logger.error('Pose feedback update failed:', error);
      // Don't throw here to avoid stopping the poll loop
    }
  }

  hasPoseChanged(newPose) {
    const threshold = 0.1; // 0.1mm threshold
    const current = this.state.currentPose;
    
    return Math.abs(newPose.x - current.x) > threshold ||
           Math.abs(newPose.y - current.y) > threshold ||
           Math.abs(newPose.z - current.z) > threshold ||
           Math.abs(newPose.r - current.r) > threshold;
  }

  validateCoordinates(x, y, z) {
    const limits = {
      x: { min: -300, max: 300 },
      y: { min: -300, max: 300 },
      z: { min: -100, max: 400 }
    };

    if (x < limits.x.min || x > limits.x.max) {
      throw new Error(`X position ${x} out of range [${limits.x.min}, ${limits.x.max}]`);
    }
    if (y < limits.y.min || y > limits.y.max) {
      throw new Error(`Y position ${y} out of range [${limits.y.min}, ${limits.y.max}]`);
    }
    if (z < limits.z.min || z > limits.z.max) {
      throw new Error(`Z position ${z} out of range [${limits.z.min}, ${limits.z.max}]`);
    }
  }

  async delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  // Get current bridge status
  getStatus() {
    return {
      running: this.state.running,
      isExecuting: this.state.isExecuting,
      currentPose: this.state.currentPose,
      errorCount: this.state.errorCount,
      lastError: this.state.lastError,
      dobotConnected: this.dobot.connected,
      plcConnected: this.plc.isConnected(),
      config: this.config
    };
  }

  // Manual command execution (for API)
  async executeCommand(command, params = {}) {
    if (!this.state.running) {
      throw new Error('Bridge not running');
    }

    try {
      switch (command) {
        case 'home':
          return await this.handleHomeCommand();
        case 'move':
          if (!params.x || !params.y || !params.z) {
            throw new Error('Move command requires x, y, z parameters');
          }
          this.validateCoordinates(params.x, params.y, params.z);
          const queuedIndex = await this.dobot.movePTP(params.x, params.y, params.z, params.r || 0);
          return { queuedIndex };
        case 'stop':
          return await this.handleStopCommand();
        case 'clear':
          return await this.dobot.clearQueue();
        case 'suction':
          return await this.dobot.setSuctionCup(params.enable || false);
        default:
          throw new Error(`Unknown command: ${command}`);
      }
    } catch (error) {
      logger.error(`Command execution failed: ${command}`, error);
      throw error;
    }
  }
}

module.exports = Bridge;
