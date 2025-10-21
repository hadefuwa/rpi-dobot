const snap7 = require('node-snap7');
const logger = require('../utils/logger');
const EventEmitter = require('events');

class S7Client extends EventEmitter {
  constructor(ip = '192.168.0.10', rack = 0, slot = 1) {
    super();
    this.ip = ip;
    this.rack = rack;
    this.slot = slot;
    this.client = new snap7.S7Client();
    this.connected = false;
    this.connecting = false;
    
    // Connection retry settings
    this.connectionRetries = 0;
    this.maxRetries = 3;
    this.retryDelay = 1000; // 1 second between retries
    this.lastConnectionAttempt = 0;
    this.connectionAttemptInterval = 5000; // 5 seconds between connection attempts
    
    // Connection monitoring
    this.connectionTime = null;
    this.lastReadTime = null;
    
    // Auto-reconnect timer
    this.reconnectTimer = null;
    this.reconnectInterval = 10000; // Check connection every 10 seconds
    
    // Start auto-reconnect monitoring
    this.startAutoReconnect();
  }

  startAutoReconnect() {
    // Periodically check connection and reconnect if needed
    this.reconnectTimer = setInterval(() => {
      if (!this.connected && !this.connecting) {
        const now = Date.now();
        if (now - this.lastConnectionAttempt >= this.connectionAttemptInterval) {
          logger.info('Auto-reconnect: Attempting to reconnect to PLC...');
          this.connect().catch(err => {
            logger.error(`Auto-reconnect failed: ${err.message}`);
          });
        }
      }
    }, this.reconnectInterval);
  }

  stopAutoReconnect() {
    if (this.reconnectTimer) {
      clearInterval(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  async connect() {
    // Don't attempt connection too frequently
    const now = Date.now();
    if (now - this.lastConnectionAttempt < this.connectionAttemptInterval) {
      return this.connected;
    }
    
    this.lastConnectionAttempt = now;
    
    // If already connecting, wait
    if (this.connecting) {
      logger.debug('Connection attempt already in progress');
      return this.connected;
    }
    
    // If already connected, verify and return
    if (this.connected) {
      try {
        const isConnected = this.client.Connected();
        if (isConnected) {
          return true;
        } else {
          // Connection lost, need to reconnect
          logger.warn('PLC connection lost, reconnecting...');
          this.connected = false;
        }
      } catch (err) {
        logger.warn('Error checking connection status:', err);
        this.connected = false;
      }
    }
    
    this.connecting = true;
    
    return new Promise((resolve, reject) => {
      logger.info(`Connecting to PLC at ${this.ip}, rack ${this.rack}, slot ${this.slot}`);
      
      // Set connection timeout
      const connectionTimeout = setTimeout(() => {
        this.connecting = false;
        reject(new Error(`PLC connection timeout after 10 seconds to ${this.ip}`));
      }, 10000);

      this.client.ConnectTo(this.ip, this.rack, this.slot, (err) => {
        clearTimeout(connectionTimeout);
        this.connecting = false;
        
        if (err) {
          this.connectionRetries++;
          logger.error(`PLC connection attempt ${this.connectionRetries} failed: ${err}`);
          
          if (this.connectionRetries < this.maxRetries) {
            logger.info(`Retrying PLC connection in ${this.retryDelay}ms...`);
            setTimeout(() => {
              this.connectionRetries--; // Don't count this as a new attempt
              this.connect().then(resolve).catch(reject);
            }, this.retryDelay);
          } else {
            this.connected = false;
            this.connectionRetries = 0;
            reject(new Error(`PLC connection failed after ${this.maxRetries} attempts: ${err}`));
          }
        } else {
          this.connected = true;
          this.connectionRetries = 0;
          this.connectionTime = now;
          logger.info(`✅ Connected to S7-1200 PLC at ${this.ip} (Rack: ${this.rack}, Slot: ${this.slot})`);
          this.emit('connected');
          resolve(true);
        }
      });
    });
  }

  async ensureConnected() {
    if (!this.connected) {
      logger.debug('Not connected, attempting to connect...');
      await this.connect();
    }
    return this.connected;
  }

  async readDB(dbNumber, start, size, timeout = 5000) {
    return new Promise(async (resolve, reject) => {
      try {
        // Ensure we're connected before reading
        await this.ensureConnected();
        
        if (!this.connected) {
          reject(new Error('PLC not connected'));
          return;
        }

        let timeoutId = setTimeout(() => {
          logger.error(`DB Read timeout after ${timeout}ms for DB${dbNumber}`);
          this.connected = false; // Mark as disconnected on timeout
          reject(new Error(`DB Read timeout after ${timeout}ms - Check if DB${dbNumber} exists and is accessible (non-optimized)`));
        }, timeout);

        const buffer = Buffer.alloc(size);
        this.client.DBRead(dbNumber, start, size, buffer, (err) => {
          clearTimeout(timeoutId);
          if (err) {
            logger.error(`DB Read error for DB${dbNumber}: ${err}`);
            // Mark as disconnected if we get a connection error
            if (err.message && (err.message.includes('connection') || err.message.includes('timeout'))) {
              this.connected = false;
            }
            reject(err);
          } else {
            this.lastReadTime = Date.now();
            logger.debug(`Read DB${dbNumber} from ${start}, size ${size}`);
            resolve(buffer);
          }
        });
      } catch (error) {
        reject(error);
      }
    });
  }

  async writeDB(dbNumber, start, buffer) {
    return new Promise(async (resolve, reject) => {
      try {
        await this.ensureConnected();
        
        if (!this.connected) {
          reject(new Error('PLC not connected'));
          return;
        }

        this.client.DBWrite(dbNumber, start, buffer.length, buffer, (err) => {
          if (err) {
            logger.error(`DB Write error: ${err}`);
            if (err.message && err.message.includes('connection')) {
              this.connected = false;
            }
            reject(err);
          } else {
            logger.debug(`Wrote to DB${dbNumber} at ${start}, size ${buffer.length}`);
            resolve();
          }
        });
      } catch (error) {
        reject(error);
      }
    });
  }

  async readMBit(address) {
    // Read Merker bit (e.g., M0.0)
    const [byte, bit] = address.split('.');
    const byteNum = parseInt(byte.substring(1));
    
    return new Promise(async (resolve, reject) => {
      try {
        await this.ensureConnected();
        
        if (!this.connected) {
          reject(new Error('PLC not connected'));
          return;
        }

        const buffer = Buffer.alloc(1);
        this.client.MBRead(byteNum, 1, buffer, (err) => {
          if (err) {
            logger.error(`MB Read error for ${address}: ${err}`);
            if (err.message && err.message.includes('connection')) {
              this.connected = false;
            }
            reject(err);
          } else {
            const bitValue = (buffer[0] >> parseInt(bit)) & 1;
            logger.debug(`Read ${address} = ${bitValue}`);
            resolve(bitValue);
          }
        });
      } catch (error) {
        reject(error);
      }
    });
  }

  async writeMBit(address, value) {
    const [byte, bit] = address.split('.');
    const byteNum = parseInt(byte.substring(1));
    
    return new Promise(async (resolve, reject) => {
      try {
        await this.ensureConnected();
        
        if (!this.connected) {
          reject(new Error('PLC not connected'));
          return;
        }

        // Read-modify-write
        const buffer = Buffer.alloc(1);
        await new Promise((readResolve, readReject) => {
          this.client.MBRead(byteNum, 1, buffer, (err) => {
            if (err) readReject(err);
            else readResolve();
          });
        });
        
        if (value) {
          buffer[0] |= (1 << parseInt(bit));
        } else {
          buffer[0] &= ~(1 << parseInt(bit));
        }
        
        this.client.MBWrite(byteNum, 1, buffer, (err) => {
          if (err) {
            logger.error(`MB Write error for ${address}: ${err}`);
            if (err.message && err.message.includes('connection')) {
              this.connected = false;
            }
            reject(err);
          } else {
            logger.debug(`Wrote ${address} = ${value}`);
            resolve();
          }
        });
      } catch (error) {
        reject(error);
      }
    });
  }

  async readMByte(address) {
    // Read Merker byte (e.g., MB0)
    const byteNum = parseInt(address.substring(2));
    
    return new Promise(async (resolve, reject) => {
      try {
        await this.ensureConnected();
        
        if (!this.connected) {
          reject(new Error('PLC not connected'));
          return;
        }

        const buffer = Buffer.alloc(1);
        this.client.MBRead(byteNum, 1, buffer, (err) => {
          if (err) {
            logger.error(`MB Read error for ${address}: ${err}`);
            if (err.message && err.message.includes('connection')) {
              this.connected = false;
            }
            reject(err);
          } else {
            logger.debug(`Read ${address} = ${buffer[0]}`);
            resolve(buffer[0]);
          }
        });
      } catch (error) {
        reject(error);
      }
    });
  }

  async writeMByte(address, value) {
    const byteNum = parseInt(address.substring(2));
    
    return new Promise(async (resolve, reject) => {
      try {
        await this.ensureConnected();
        
        if (!this.connected) {
          reject(new Error('PLC not connected'));
          return;
        }

        const buffer = Buffer.alloc(1);
        buffer.writeUInt8(value, 0);
        
        this.client.MBWrite(byteNum, 1, buffer, (err) => {
          if (err) {
            logger.error(`MB Write error for ${address}: ${err}`);
            if (err.message && err.message.includes('connection')) {
              this.connected = false;
            }
            reject(err);
          } else {
            logger.debug(`Wrote ${address} = ${value}`);
            resolve();
          }
        });
      } catch (error) {
        reject(error);
      }
    });
  }

  // Data type conversion methods
  parseReal(buffer, offset) {
    return buffer.readFloatBE(offset); // S7 uses big-endian
  }

  encodeReal(value) {
    const buffer = Buffer.allocUnsafe(4);
    buffer.writeFloatBE(value, 0);
    return buffer;
  }

  parseInt(buffer, offset) {
    return buffer.readInt16BE(offset);
  }

  encodeInt(value) {
    const buffer = Buffer.allocUnsafe(2);
    buffer.writeInt16BE(value, 0);
    return buffer;
  }

  parseDInt(buffer, offset) {
    return buffer.readInt32BE(offset);
  }

  encodeDInt(value) {
    const buffer = Buffer.allocUnsafe(4);
    buffer.writeInt32BE(value, 0);
    return buffer;
  }

  parseWord(buffer, offset) {
    return buffer.readUInt16BE(offset);
  }

  encodeWord(value) {
    const buffer = Buffer.allocUnsafe(2);
    buffer.writeUInt16BE(value, 0);
    return buffer;
  }

  parseDWord(buffer, offset) {
    return buffer.readUInt32BE(offset);
  }

  encodeDWord(value) {
    const buffer = Buffer.allocUnsafe(4);
    buffer.writeUInt32BE(value, 0);
    return buffer;
  }

  // High-level methods for common operations
  async readPoseFromDB(dbNumber = 1) {
    try {
      const buffer = await this.readDB(dbNumber, 0, 12); // Read 3 REALs (X, Y, Z)
      return {
        x: this.parseReal(buffer, 0),
        y: this.parseReal(buffer, 4),
        z: this.parseReal(buffer, 8)
      };
    } catch (error) {
      logger.error(`Failed to read pose from DB${dbNumber}: ${error.message}`);
      // Return default values if DB read fails
      return {
        x: 0.0,
        y: 0.0,
        z: 0.0
      };
    }
  }

  async writePoseToDB(pose, dbNumber = 1, offset = 12) {
    const buffer = Buffer.concat([
      this.encodeReal(pose.x),
      this.encodeReal(pose.y),
      this.encodeReal(pose.z)
    ]);
    await this.writeDB(dbNumber, offset, buffer);
  }

  async readStatusFromDB(dbNumber = 1, offset = 24) {
    const buffer = await this.readDB(dbNumber, offset, 2);
    return this.parseInt(buffer, 0);
  }

  async writeStatusToDB(status, dbNumber = 1, offset = 24) {
    const buffer = this.encodeInt(status);
    await this.writeDB(dbNumber, offset, buffer);
  }

  async getControlBits() {
    try {
      const [start, stop, home, estop, suction, ready, busy, error] = await Promise.all([
        this.readMBit('M0.0'),
        this.readMBit('M0.1'),
        this.readMBit('M0.2'),
        this.readMBit('M0.3'),
        this.readMBit('M0.4'),
        this.readMBit('M0.5'),
        this.readMBit('M0.6'),
        this.readMBit('M0.7')
      ]);

      return { start, stop, home, estop, suction, ready, busy, error };
    } catch (error) {
      logger.error(`Failed to read control bits: ${error.message}`);
      // Return default values if control bits read fails
      return { start: false, stop: false, home: false, estop: false, suction: false, ready: false, busy: false, error: false };
    }
  }

  async setControlBits(bits) {
    const promises = [];
    if (bits.start !== undefined) promises.push(this.writeMBit('M0.0', bits.start));
    if (bits.stop !== undefined) promises.push(this.writeMBit('M0.1', bits.stop));
    if (bits.home !== undefined) promises.push(this.writeMBit('M0.2', bits.home));
    if (bits.estop !== undefined) promises.push(this.writeMBit('M0.3', bits.estop));
    
    await Promise.all(promises);
  }

  isConnected() {
    // Use our own connected flag as it's more reliable
    return this.connected;
  }

  async disconnect() {
    this.stopAutoReconnect();
    
    if (this.connected) {
      try {
        this.client.Disconnect();
        this.connected = false;
        logger.info('PLC disconnected');
        this.emit('disconnected');
      } catch (err) {
        logger.error('Error disconnecting from PLC:', err);
      }
    }
  }

  // Check if a specific DB exists and is accessible
  async checkDBExists(dbNumber) {
    try {
      if (!this.isConnected()) {
        return { exists: false, error: 'Not connected' };
      }
      
      // Try to read a small amount of data from the DB
      await this.readDB(dbNumber, 0, 1);
      return { exists: true, accessible: true };
    } catch (error) {
      return { exists: false, accessible: false, error: error.message };
    }
  }

  // Test basic PLC connectivity
  async testConnection() {
    try {
      if (!this.client) {
        return { success: false, error: 'Client not initialized' };
      }

      // Try to read a simple merker bit to test connection
      const buffer = Buffer.alloc(1);
      return new Promise((resolve) => {
        const timeout = setTimeout(() => {
          resolve({ success: false, error: 'Connection test timeout' });
        }, 3000);

        this.client.MBRead(0, 1, buffer, (err) => {
          clearTimeout(timeout);
          if (err) {
            resolve({ success: false, error: err.message });
          } else {
            resolve({ success: true, message: 'Connection test successful' });
          }
        });
      });
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  // Health check method
  async healthCheck() {
    try {
      if (!this.isConnected()) {
        return { status: 'disconnected', error: 'Not connected' };
      }
      
      // Test basic connectivity first
      const connectionTest = await this.testConnection();
      if (!connectionTest.success) {
        this.connected = false;
        return { status: 'error', error: connectionTest.error };
      }
      
      // Check if DB1 exists
      const db1Check = await this.checkDBExists(1);
      
      return { 
        status: 'connected', 
        timestamp: Date.now(),
        connectionTime: this.connectionTime,
        lastReadTime: this.lastReadTime,
        connectionTest: connectionTest,
        db1: db1Check
      };
    } catch (error) {
      this.connected = false;
      return { status: 'error', error: error.message };
    }
  }

  // Get connection statistics
  getStats() {
    return {
      connected: this.connected,
      connecting: this.connecting,
      connectionTime: this.connectionTime,
      lastReadTime: this.lastReadTime,
      lastConnectionAttempt: this.lastConnectionAttempt,
      connectionRetries: this.connectionRetries,
      ip: this.ip,
      rack: this.rack,
      slot: this.slot
    };
  }
}

module.exports = S7Client;
