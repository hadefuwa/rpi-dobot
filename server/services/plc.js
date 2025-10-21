const snap7 = require('node-snap7');
const logger = require('../utils/logger');

class S7Client {
  constructor(ip = '192.168.0.10', rack = 0, slot = 1) {
    this.ip = ip;
    this.rack = rack;
    this.slot = slot;
    this.client = new snap7.S7Client();
    this.connected = false;
    this.connectionRetries = 0;
    this.maxRetries = 5;
    this.retryDelay = 2000;
  }

  async connect() {
    return new Promise((resolve, reject) => {
      this.client.ConnectTo(this.ip, this.rack, this.slot, (err) => {
        if (err) {
          this.connectionRetries++;
          logger.error(`PLC connection attempt ${this.connectionRetries} failed: ${err}`);
          
          if (this.connectionRetries < this.maxRetries) {
            setTimeout(() => {
              this.connect().then(resolve).catch(reject);
            }, this.retryDelay);
          } else {
            reject(new Error(`PLC connection failed after ${this.maxRetries} attempts: ${err}`));
          }
        } else {
          this.connected = this.client.Connected();
          this.connectionRetries = 0;
          logger.info(`Connected to S7-1200 PLC at ${this.ip}`);
          resolve();
        }
      });
    });
  }

  async readDB(dbNumber, start, size) {
    return new Promise((resolve, reject) => {
      if (!this.connected) {
        reject(new Error('PLC not connected'));
        return;
      }

      const buffer = Buffer.alloc(size);
      this.client.DBRead(dbNumber, start, size, buffer, (err) => {
        if (err) {
          logger.error(`DB Read error: ${err}`);
          reject(err);
        } else {
          logger.debug(`Read DB${dbNumber} from ${start}, size ${size}`);
          resolve(buffer);
        }
      });
    });
  }

  async writeDB(dbNumber, start, buffer) {
    return new Promise((resolve, reject) => {
      if (!this.connected) {
        reject(new Error('PLC not connected'));
        return;
      }

      this.client.DBWrite(dbNumber, start, buffer.length, buffer, (err) => {
        if (err) {
          logger.error(`DB Write error: ${err}`);
          reject(err);
        } else {
          logger.debug(`Wrote to DB${dbNumber} at ${start}, size ${buffer.length}`);
          resolve();
        }
      });
    });
  }

  async readMBit(address) {
    // Read Merker bit (e.g., M0.0)
    const [byte, bit] = address.split('.');
    const byteNum = parseInt(byte.substring(1));
    
    return new Promise((resolve, reject) => {
      if (!this.connected) {
        reject(new Error('PLC not connected'));
        return;
      }

      const buffer = Buffer.alloc(1);
      this.client.MBRead(byteNum, 1, buffer, (err) => {
        if (err) {
          logger.error(`MB Read error for ${address}: ${err}`);
          reject(err);
        } else {
          const bitValue = (buffer[0] >> parseInt(bit)) & 1;
          logger.debug(`Read ${address} = ${bitValue}`);
          resolve(bitValue);
        }
      });
    });
  }

  async writeMBit(address, value) {
    const [byte, bit] = address.split('.');
    const byteNum = parseInt(byte.substring(1));
    
    return new Promise(async (resolve, reject) => {
      if (!this.connected) {
        reject(new Error('PLC not connected'));
        return;
      }

      try {
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
    
    return new Promise((resolve, reject) => {
      if (!this.connected) {
        reject(new Error('PLC not connected'));
        return;
      }

      const buffer = Buffer.alloc(1);
      this.client.MBRead(byteNum, 1, buffer, (err) => {
        if (err) {
          logger.error(`MB Read error for ${address}: ${err}`);
          reject(err);
        } else {
          logger.debug(`Read ${address} = ${buffer[0]}`);
          resolve(buffer[0]);
        }
      });
    });
  }

  async writeMByte(address, value) {
    const byteNum = parseInt(address.substring(2));
    
    return new Promise((resolve, reject) => {
      if (!this.connected) {
        reject(new Error('PLC not connected'));
        return;
      }

      const buffer = Buffer.alloc(1);
      buffer.writeUInt8(value, 0);
      
      this.client.MBWrite(byteNum, 1, buffer, (err) => {
        if (err) {
          logger.error(`MB Write error for ${address}: ${err}`);
          reject(err);
        } else {
          logger.debug(`Wrote ${address} = ${value}`);
          resolve();
        }
      });
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
    const buffer = await this.readDB(dbNumber, 0, 12); // Read 3 REALs (X, Y, Z)
    return {
      x: this.parseReal(buffer, 0),
      y: this.parseReal(buffer, 4),
      z: this.parseReal(buffer, 8)
    };
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
    const [start, stop, home, estop] = await Promise.all([
      this.readMBit('M0.0'),
      this.readMBit('M0.1'),
      this.readMBit('M0.2'),
      this.readMBit('M0.3')
    ]);
    
    return { start, stop, home, estop };
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
    return this.connected && this.client.Connected();
  }

  async disconnect() {
    if (this.connected) {
      this.client.Disconnect();
      this.connected = false;
      logger.info('PLC disconnected');
    }
  }

  // Health check method
  async healthCheck() {
    try {
      if (!this.isConnected()) {
        return { status: 'disconnected', error: 'Not connected' };
      }
      
      // Try to read a simple value to verify connection
      await this.readMBit('M0.0');
      return { status: 'connected', timestamp: Date.now() };
    } catch (error) {
      this.connected = false;
      return { status: 'error', error: error.message };
    }
  }
}

module.exports = S7Client;
