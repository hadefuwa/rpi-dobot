const DobotClient = require('../../server/services/dobot');

describe('DobotClient', () => {
  let client;

  beforeEach(() => {
    client = new DobotClient('192.168.0.30', 29999);
  });

  describe('buildPacket', () => {
    test('builds correct packet structure for GetPose command', () => {
      const packet = client.buildPacket(0x0A, 0x00, Buffer.alloc(0));
      
      // Check header
      expect(packet[0]).toBe(0xAA);
      expect(packet[1]).toBe(0xAA);
      
      // Check length
      expect(packet[2]).toBe(0x02); // 0 bytes payload + 2
      
      // Check command ID
      expect(packet[3]).toBe(0x0A);
      
      // Check control byte
      expect(packet[4]).toBe(0x00);
      
      // Verify checksum
      let sum = 0;
      for (let i = 2; i < packet.length - 1; i++) {
        sum += packet[i];
      }
      const expectedChecksum = (~sum + 1) & 0xFF;
      expect(packet[packet.length - 1]).toBe(expectedChecksum);
    });

    test('builds correct packet with parameters', () => {
      const params = Buffer.allocUnsafe(4);
      params.writeFloatLE(100.5, 0);
      const packet = client.buildPacket(0x54, 0x02, params);
      
      expect(packet[2]).toBe(0x06); // 4 bytes payload + 2
      expect(packet[3]).toBe(0x54);
      expect(packet[4]).toBe(0x02);
      
      // Check parameters are copied correctly
      expect(packet.readFloatLE(5)).toBeCloseTo(100.5, 1);
    });

    test('calculates checksum correctly for various commands', () => {
      const testCases = [
        { cmdId: 0x0A, ctrl: 0x00, params: Buffer.alloc(0) },
        { cmdId: 0x1F, ctrl: 0x02, params: Buffer.alloc(0) },
        { cmdId: 0x54, ctrl: 0x02, params: Buffer.alloc(17) }
      ];

      testCases.forEach(({ cmdId, ctrl, params }) => {
        const packet = client.buildPacket(cmdId, ctrl, params);
        
        let sum = 0;
        for (let i = 2; i < packet.length - 1; i++) {
          sum += packet[i];
        }
        const expectedChecksum = (~sum + 1) & 0xFF;
        expect(packet[packet.length - 1]).toBe(expectedChecksum);
      });
    });
  });

  describe('validateCoordinates', () => {
    test('accepts valid coordinates', () => {
      expect(() => {
        client.validateCoordinates(200, 0, 100, 0);
      }).not.toThrow();
    });

    test('rejects X coordinates out of range', () => {
      expect(() => {
        client.validateCoordinates(400, 0, 100, 0);
      }).toThrow('X position 400 out of range [-300, 300]');
    });

    test('rejects Y coordinates out of range', () => {
      expect(() => {
        client.validateCoordinates(200, -400, 100, 0);
      }).toThrow('Y position -400 out of range [-300, 300]');
    });

    test('rejects Z coordinates out of range', () => {
      expect(() => {
        client.validateCoordinates(200, 0, 500, 0);
      }).toThrow('Z position 500 out of range [-100, 400]');
    });

    test('rejects R rotation out of range', () => {
      expect(() => {
        client.validateCoordinates(200, 0, 100, 200);
      }).toThrow('R rotation 200 out of range [-180, 180]');
    });
  });

  describe('handleResponse', () => {
    test('parses valid response correctly', () => {
      const mockData = Buffer.from([0xAA, 0xAA, 0x06, 0x0A, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]);
      // Calculate correct checksum
      let sum = 0;
      for (let i = 2; i < mockData.length - 1; i++) {
        sum += mockData[i];
      }
      mockData[mockData.length - 1] = (~sum + 1) & 0xFF;

      const responseHandler = jest.fn();
      client.on('response_0x0A', responseHandler);
      
      client.handleResponse(mockData);
      
      expect(responseHandler).toHaveBeenCalledWith({
        payload: Buffer.from([0x00, 0x00, 0x00, 0x00]),
        ctrl: 0x00,
        cmdId: 0x0A
      });
    });

    test('ignores packets with invalid header', () => {
      const mockData = Buffer.from([0xBB, 0xBB, 0x02, 0x0A, 0x00, 0xF6]);
      const responseHandler = jest.fn();
      client.on('response_0x0A', responseHandler);
      
      client.handleResponse(mockData);
      
      expect(responseHandler).not.toHaveBeenCalled();
    });

    test('ignores packets with invalid checksum', () => {
      const mockData = Buffer.from([0xAA, 0xAA, 0x02, 0x0A, 0x00, 0x00]);
      const responseHandler = jest.fn();
      client.on('response_0x0A', responseHandler);
      
      client.handleResponse(mockData);
      
      expect(responseHandler).not.toHaveBeenCalled();
    });
  });

  describe('connection management', () => {
    test('initializes with correct default values', () => {
      expect(client.host).toBe('192.168.0.30');
      expect(client.port).toBe(29999);
      expect(client.connected).toBe(false);
      expect(client.socket).toBe(null);
    });

    test('handles connection errors', () => {
      const errorHandler = jest.fn();
      client.on('error', errorHandler);
      
      client.handleError(new Error('Connection failed'));
      
      expect(client.connected).toBe(false);
      expect(errorHandler).toHaveBeenCalledWith(expect.any(Error));
    });

    test('handles disconnection', () => {
      const disconnectHandler = jest.fn();
      client.on('disconnected', disconnectHandler);
      
      client.handleDisconnect();
      
      expect(client.connected).toBe(false);
      expect(disconnectHandler).toHaveBeenCalled();
    });
  });
});
