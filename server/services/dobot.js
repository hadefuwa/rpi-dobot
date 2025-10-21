const net = require('net');
const { SerialPort } = require('serialport');
const { EventEmitter } = require('events');
const logger = require('../utils/logger');

class DobotClient extends EventEmitter {
  constructor(host = '192.168.0.30', port = 29999, useUSB = false, usbPath = '/dev/ttyUSB0') {
    super();
    this.host = host;
    this.port = port;
    this.useUSB = useUSB;
    this.usbPath = usbPath;
    this.socket = null;
    this.serialPort = null;  // Fixed: renamed from this.port to this.serialPort to avoid conflict
    this.connected = false;
    this.commandQueue = [];
    this.responseHandlers = new Map();
    this.commandId = 0;
  }

  async connect() {
    try {
      if (this.useUSB) {
        await this.connectUSB();
      } else {
        await this.connectTCP();
      }
      this.connected = true;
      this.emit('connected');
      logger.info('Dobot connected successfully');
    } catch (error) {
      logger.error('Dobot connection failed:', error);
      throw error;
    }
  }

  async connectTCP() {
    return new Promise((resolve, reject) => {
      this.socket = new net.Socket();
      
      this.socket.connect(this.port, this.host, () => {
        logger.info(`Connected to Dobot via TCP at ${this.host}:${this.port}`);
        resolve();
      });

      this.socket.on('data', (data) => this.handleResponse(data));
      this.socket.on('error', (err) => {
        logger.error('Dobot TCP error:', err);
        this.handleError(err);
      });
      this.socket.on('close', () => this.handleDisconnect());
      
      setTimeout(() => {
        if (!this.connected) {
          reject(new Error('Dobot TCP connection timeout'));
        }
      }, 5000);
    });
  }

  async connectUSB() {
    return new Promise((resolve, reject) => {
      this.serialPort = new SerialPort({
        path: this.usbPath,
        baudRate: 115200,
        dataBits: 8,
        stopBits: 1,
        parity: 'none'
      }, (err) => {
        if (err) {
          logger.error('Dobot USB connection failed:', err);
          reject(err);
        } else {
          logger.info(`Connected to Dobot via USB at ${this.usbPath}`);
          resolve();
        }
      });

      this.serialPort.on('data', (data) => this.handleResponse(data));
      this.serialPort.on('error', (err) => {
        logger.error('Dobot USB error:', err);
        this.handleError(err);
      });
      this.serialPort.on('close', () => this.handleDisconnect());
    });
  }

  buildPacket(cmdId, ctrl = 0x00, params = Buffer.alloc(0)) {
    const length = params.length + 2;
    const buffer = Buffer.allocUnsafe(5 + params.length);
    
    // Header
    buffer.writeUInt8(0xAA, 0);
    buffer.writeUInt8(0xAA, 1);
    // Length
    buffer.writeUInt8(length, 2);
    // Command ID
    buffer.writeUInt8(cmdId, 3);
    // Control byte
    buffer.writeUInt8(ctrl, 4);
    
    // Parameters (little-endian)
    if (params.length > 0) {
      params.copy(buffer, 5);
    }
    
    // Calculate checksum (2's complement of sum of bytes 2 to end)
    let sum = 0;
    for (let i = 2; i < buffer.length; i++) {
      sum += buffer[i];
    }
    const checksum = Buffer.allocUnsafe(1);
    checksum.writeUInt8((~sum + 1) & 0xFF, 0);
    
    return Buffer.concat([buffer, checksum]);
  }

  async sendCommand(cmdId, ctrl = 0x00, params = Buffer.alloc(0), timeout = 2000) {
    if (!this.connected) {
      throw new Error('Dobot not connected');
    }
    
    const packet = this.buildPacket(cmdId, ctrl, params);
    const commandId = ++this.commandId;
    
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        this.responseHandlers.delete(commandId);
        reject(new Error(`Command ${cmdId} timeout after ${timeout}ms`));
      }, timeout);
      
      this.responseHandlers.set(commandId, { resolve, reject, timer, cmdId });
      
      try {
        if (this.useUSB) {
          this.serialPort.write(packet);
        } else {
          this.socket.write(packet);
        }
        logger.debug(`Sent command ${cmdId} with ID ${commandId}`);
      } catch (error) {
        this.responseHandlers.delete(commandId);
        clearTimeout(timer);
        reject(error);
      }
    });
  }

  handleResponse(data) {
    try {
      // Parse packet header
      if (data.length < 6) {
        logger.warn('Received incomplete packet');
        return;
      }

      const header1 = data.readUInt8(0);
      const header2 = data.readUInt8(1);
      
      if (header1 !== 0xAA || header2 !== 0xAA) {
        logger.warn('Invalid packet header');
        return;
      }

      const length = data.readUInt8(2);
      const cmdId = data.readUInt8(3);
      const ctrl = data.readUInt8(4);
      const payload = data.slice(5, data.length - 1);
      const checksum = data.readUInt8(data.length - 1);

      // Verify checksum
      let sum = 0;
      for (let i = 2; i < data.length - 1; i++) {
        sum += data[i];
      }
      const expectedChecksum = (~sum + 1) & 0xFF;
      
      if (checksum !== expectedChecksum) {
        logger.warn(`Checksum mismatch for command ${cmdId}`);
        return;
      }

      // Find and resolve waiting command
      for (const [commandId, handler] of this.responseHandlers) {
        if (handler.cmdId === cmdId) {
          clearTimeout(handler.timer);
          this.responseHandlers.delete(commandId);
          handler.resolve({ 
            payload, 
            ctrl, 
            cmdId,
            queuedIndex: payload.length >= 4 ? payload.readUInt32LE(0) : undefined
          });
          break;
        }
      }

      this.emit(`response_${cmdId}`, { payload, ctrl, cmdId });
      logger.debug(`Received response for command ${cmdId}`);
      
    } catch (error) {
      logger.error('Error handling Dobot response:', error);
    }
  }

  handleError(error) {
    this.connected = false;
    this.emit('error', error);
    
    // Reject all pending commands
    for (const [commandId, handler] of this.responseHandlers) {
      clearTimeout(handler.timer);
      handler.reject(new Error('Connection lost'));
    }
    this.responseHandlers.clear();
  }

  handleDisconnect() {
    this.connected = false;
    this.emit('disconnected');
    logger.warn('Dobot disconnected');
  }

  // High-level command methods
  async getPose() {
    const response = await this.sendCommand(0x0A, 0x00);
    return {
      x: response.payload.readFloatLE(0),
      y: response.payload.readFloatLE(4),
      z: response.payload.readFloatLE(8),
      r: response.payload.readFloatLE(12)
    };
  }

  async home() {
    const response = await this.sendCommand(0x1F, 0x02); // Queued command
    return response.queuedIndex;
  }

  async movePTP(x, y, z, r, mode = 0x01) {
    // Validate coordinates
    this.validateCoordinates(x, y, z, r);
    
    const params = Buffer.allocUnsafe(17);
    params.writeUInt8(mode, 0); // Mode: MOVJ_XYZ
    params.writeFloatLE(x, 1);
    params.writeFloatLE(y, 5);
    params.writeFloatLE(z, 9);
    params.writeFloatLE(r, 13);
    
    const response = await this.sendCommand(0x54, 0x02, params);
    return response.queuedIndex;
  }

  async clearQueue() {
    const response = await this.sendCommand(0xF5, 0x00);
    return response;
  }

  async setSuctionCup(enable) {
    const params = Buffer.allocUnsafe(1);
    params.writeUInt8(enable ? 1 : 0, 0);
    const response = await this.sendCommand(0x3E, 0x00, params);
    return response;
  }

  async getStatus() {
    const response = await this.sendCommand(0x10, 0x00);
    return {
      queuedCmdIndex: response.payload.readUInt32LE(0),
      isIdle: response.payload.readUInt8(4) === 1
    };
  }

  validateCoordinates(x, y, z, r) {
    const limits = {
      x: { min: -300, max: 300 },
      y: { min: -300, max: 300 },
      z: { min: -100, max: 400 },
      r: { min: -180, max: 180 }
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
    if (r < limits.r.min || r > limits.r.max) {
      throw new Error(`R rotation ${r} out of range [${limits.r.min}, ${limits.r.max}]`);
    }
  }

  async disconnect() {
    if (this.socket) {
      this.socket.destroy();
      this.socket = null;
    }
    if (this.serialPort) {
      this.serialPort.close();
      this.serialPort = null;
    }
    this.connected = false;
    this.emit('disconnected');
    logger.info('Dobot disconnected');
  }
}

module.exports = DobotClient;
