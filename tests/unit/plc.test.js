const S7Client = require('../../server/services/plc');

// Mock node-snap7
jest.mock('node-snap7', () => {
  return {
    S7Client: jest.fn().mockImplementation(() => ({
      ConnectTo: jest.fn(),
      Connected: jest.fn(() => true),
      DBRead: jest.fn(),
      DBWrite: jest.fn(),
      MBRead: jest.fn(),
      MBWrite: jest.fn(),
      Disconnect: jest.fn()
    }))
  };
});

describe('S7Client', () => {
  let client;
  let mockSnap7;

  beforeEach(() => {
    const snap7 = require('node-snap7');
    mockSnap7 = new snap7.S7Client();
    client = new S7Client('192.168.0.10', 0, 1);
    client.client = mockSnap7;
  });

  describe('constructor', () => {
    test('initializes with correct default values', () => {
      expect(client.ip).toBe('192.168.0.10');
      expect(client.rack).toBe(0);
      expect(client.slot).toBe(1);
      expect(client.connected).toBe(false);
    });
  });

  describe('connect', () => {
    test('connects successfully', async () => {
      mockSnap7.ConnectTo.mockImplementation((ip, rack, slot, callback) => {
        callback(null);
      });
      mockSnap7.Connected.mockReturnValue(true);

      await client.connect();

      expect(client.connected).toBe(true);
      expect(mockSnap7.ConnectTo).toHaveBeenCalledWith('192.168.0.10', 0, 1, expect.any(Function));
    });

    test('handles connection failure', async () => {
      mockSnap7.ConnectTo.mockImplementation((ip, rack, slot, callback) => {
        callback(new Error('Connection failed'));
      });

      await expect(client.connect()).rejects.toThrow('PLC connection failed: Error: Connection failed');
    });

    test('retries connection on failure', async () => {
      let callCount = 0;
      mockSnap7.ConnectTo.mockImplementation((ip, rack, slot, callback) => {
        callCount++;
        if (callCount < 3) {
          callback(new Error('Connection failed'));
        } else {
          callback(null);
        }
      });
      mockSnap7.Connected.mockReturnValue(true);

      // Mock setTimeout to make test synchronous
      jest.spyOn(global, 'setTimeout').mockImplementation((fn) => fn());

      await client.connect();

      expect(callCount).toBe(3);
      expect(client.connected).toBe(true);
    });
  });

  describe('readDB', () => {
    beforeEach(() => {
      client.connected = true;
    });

    test('reads data block successfully', async () => {
      const mockBuffer = Buffer.from([0x40, 0x20, 0x00, 0x00]); // 2.5 as float
      mockSnap7.DBRead.mockImplementation((dbNumber, start, size, buffer, callback) => {
        mockBuffer.copy(buffer);
        callback(null);
      });

      const result = await client.readDB(1, 0, 4);

      expect(result).toEqual(mockBuffer);
      expect(mockSnap7.DBRead).toHaveBeenCalledWith(1, 0, 4, expect.any(Buffer), expect.any(Function));
    });

    test('handles read error', async () => {
      mockSnap7.DBRead.mockImplementation((dbNumber, start, size, buffer, callback) => {
        callback(new Error('Read failed'));
      });

      await expect(client.readDB(1, 0, 4)).rejects.toThrow('Read failed');
    });

    test('throws error when not connected', async () => {
      client.connected = false;

      await expect(client.readDB(1, 0, 4)).rejects.toThrow('PLC not connected');
    });
  });

  describe('writeDB', () => {
    beforeEach(() => {
      client.connected = true;
    });

    test('writes data block successfully', async () => {
      const data = Buffer.from([0x40, 0x20, 0x00, 0x00]);
      mockSnap7.DBWrite.mockImplementation((dbNumber, start, size, buffer, callback) => {
        callback(null);
      });

      await client.writeDB(1, 0, data);

      expect(mockSnap7.DBWrite).toHaveBeenCalledWith(1, 0, 4, data, expect.any(Function));
    });

    test('handles write error', async () => {
      const data = Buffer.from([0x40, 0x20, 0x00, 0x00]);
      mockSnap7.DBWrite.mockImplementation((dbNumber, start, size, buffer, callback) => {
        callback(new Error('Write failed'));
      });

      await expect(client.writeDB(1, 0, data)).rejects.toThrow('Write failed');
    });
  });

  describe('readMBit', () => {
    beforeEach(() => {
      client.connected = true;
    });

    test('reads merker bit successfully', async () => {
      mockSnap7.MBRead.mockImplementation((byteNum, size, buffer, callback) => {
        buffer[0] = 0x05; // Bit 0 and 2 set
        callback(null);
      });

      const result = await client.readMBit('M0.0');
      expect(result).toBe(1);

      const result2 = await client.readMBit('M0.1');
      expect(result2).toBe(0);
    });

    test('handles read error', async () => {
      mockSnap7.MBRead.mockImplementation((byteNum, size, buffer, callback) => {
        callback(new Error('Read failed'));
      });

      await expect(client.readMBit('M0.0')).rejects.toThrow('Read failed');
    });
  });

  describe('writeMBit', () => {
    beforeEach(() => {
      client.connected = true;
    });

    test('writes merker bit successfully', async () => {
      mockSnap7.MBRead.mockImplementation((byteNum, size, buffer, callback) => {
        buffer[0] = 0x00; // All bits clear
        callback(null);
      });
      mockSnap7.MBWrite.mockImplementation((byteNum, size, buffer, callback) => {
        callback(null);
      });

      await client.writeMBit('M0.0', true);

      expect(mockSnap7.MBRead).toHaveBeenCalledWith(0, 1, expect.any(Buffer), expect.any(Function));
      expect(mockSnap7.MBWrite).toHaveBeenCalledWith(0, 1, expect.any(Buffer), expect.any(Function));
    });
  });

  describe('data type conversion', () => {
    test('parseReal converts big-endian float correctly', () => {
      const buffer = Buffer.from([0x40, 0x20, 0x00, 0x00]); // 2.5 as big-endian float
      const result = client.parseReal(buffer, 0);
      expect(result).toBeCloseTo(2.5, 1);
    });

    test('encodeReal converts float to big-endian correctly', () => {
      const result = client.encodeReal(2.5);
      expect(result.readFloatBE(0)).toBeCloseTo(2.5, 1);
    });

    test('parseInt converts big-endian int16 correctly', () => {
      const buffer = Buffer.from([0x00, 0x64]); // 100 as big-endian int16
      const result = client.parseInt(buffer, 0);
      expect(result).toBe(100);
    });

    test('encodeInt converts int16 to big-endian correctly', () => {
      const result = client.encodeInt(100);
      expect(result.readInt16BE(0)).toBe(100);
    });
  });

  describe('high-level methods', () => {
    beforeEach(() => {
      client.connected = true;
    });

    test('readPoseFromDB reads pose correctly', async () => {
      const mockBuffer = Buffer.alloc(12);
      mockBuffer.writeFloatBE(100.5, 0);  // X
      mockBuffer.writeFloatBE(200.5, 4);  // Y
      mockBuffer.writeFloatBE(300.5, 8);  // Z
      
      mockSnap7.DBRead.mockImplementation((dbNumber, start, size, buffer, callback) => {
        mockBuffer.copy(buffer);
        callback(null);
      });

      const pose = await client.readPoseFromDB(1, 0);

      expect(pose).toEqual({
        x: 100.5,
        y: 200.5,
        z: 300.5
      });
    });

    test('writePoseToDB writes pose correctly', async () => {
      const pose = { x: 100.5, y: 200.5, z: 300.5 };
      mockSnap7.DBWrite.mockImplementation((dbNumber, start, size, buffer, callback) => {
        callback(null);
      });

      await client.writePoseToDB(pose, 1, 12);

      expect(mockSnap7.DBWrite).toHaveBeenCalledWith(1, 12, 12, expect.any(Buffer), expect.any(Function));
    });
  });

  describe('health check', () => {
    test('returns connected status when healthy', async () => {
      client.connected = true;
      mockSnap7.MBRead.mockImplementation((byteNum, size, buffer, callback) => {
        buffer[0] = 0x00;
        callback(null);
      });

      const health = await client.healthCheck();

      expect(health.status).toBe('connected');
      expect(health.timestamp).toBeDefined();
    });

    test('returns error status when unhealthy', async () => {
      client.connected = true;
      mockSnap7.MBRead.mockImplementation((byteNum, size, buffer, callback) => {
        callback(new Error('Read failed'));
      });

      const health = await client.healthCheck();

      expect(health.status).toBe('error');
      expect(health.error).toBeDefined();
      expect(client.connected).toBe(false);
    });

    test('returns disconnected status when not connected', async () => {
      client.connected = false;

      const health = await client.healthCheck();

      expect(health.status).toBe('disconnected');
    });
  });
});
