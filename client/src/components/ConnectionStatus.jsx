import { useState, useEffect } from 'react';
import { Wifi, WifiOff, RefreshCw, CheckCircle, AlertCircle } from 'lucide-react';

export default function ConnectionStatus({ socket, connected, systemStatus }) {
  const [lastPing, setLastPing] = useState(null);
  const [pingTime, setPingTime] = useState(null);

  useEffect(() => {
    if (socket) {
      // Ping the server to test connection
      const pingInterval = setInterval(() => {
        const start = Date.now();
        socket.emit('ping', () => {
          setPingTime(Date.now() - start);
          setLastPing(new Date());
        });
      }, 5000);

      return () => clearInterval(pingInterval);
    }
  }, [socket]);

  const getConnectionQuality = (ping) => {
    if (!ping) return { quality: 'Unknown', color: 'text-gray-500' };
    if (ping < 50) return { quality: 'Excellent', color: 'text-green-500' };
    if (ping < 100) return { quality: 'Good', color: 'text-yellow-500' };
    if (ping < 200) return { quality: 'Fair', color: 'text-orange-500' };
    return { quality: 'Poor', color: 'text-red-500' };
  };

  const quality = getConnectionQuality(pingTime);

  return (
    <div className="space-y-4">
      {/* WebSocket Connection */}
      <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
        <div className="flex items-center space-x-3">
          {connected ? (
            <Wifi className="h-5 w-5 text-green-500" />
          ) : (
            <WifiOff className="h-5 w-5 text-red-500" />
          )}
          <div>
            <p className="font-medium text-gray-900">WebSocket</p>
            <p className="text-sm text-gray-600">
              {connected ? 'Connected' : 'Disconnected'}
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          {connected ? (
            <CheckCircle className="h-4 w-4 text-green-500" />
          ) : (
            <AlertCircle className="h-4 w-4 text-red-500" />
          )}
        </div>
      </div>

      {/* Connection Quality */}
      {connected && (
        <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
          <div className="flex items-center space-x-3">
            <RefreshCw className="h-5 w-5 text-blue-500" />
            <div>
              <p className="font-medium text-gray-900">Latency</p>
              <p className="text-sm text-gray-600">
                {pingTime ? `${pingTime}ms` : 'Measuring...'}
              </p>
            </div>
          </div>
          <div className="text-right">
            <p className={`text-sm font-medium ${quality.color}`}>
              {quality.quality}
            </p>
            {lastPing && (
              <p className="text-xs text-gray-500">
                {lastPing.toLocaleTimeString()}
              </p>
            )}
          </div>
        </div>
      )}

      {/* System Connections */}
      <div className="space-y-2">
        <h4 className="text-sm font-medium text-gray-900">System Connections</h4>
        
        {/* Dobot Connection */}
        <div className="flex items-center justify-between p-2 bg-gray-50 rounded">
          <span className="text-sm text-gray-700">Dobot Magician</span>
          <div className="flex items-center space-x-2">
            {systemStatus?.dobot?.connected ? (
              <CheckCircle className="h-4 w-4 text-green-500" />
            ) : (
              <AlertCircle className="h-4 w-4 text-red-500" />
            )}
            <span className={`text-xs ${
              systemStatus?.dobot?.connected ? 'text-green-600' : 'text-red-600'
            }`}>
              {systemStatus?.dobot?.connected ? 'Online' : 'Offline'}
            </span>
          </div>
        </div>

        {/* PLC Connection */}
        <div className="flex items-center justify-between p-2 bg-gray-50 rounded">
          <span className="text-sm text-gray-700">S7-1200 PLC</span>
          <div className="flex items-center space-x-2">
            {systemStatus?.plc?.connected ? (
              <CheckCircle className="h-4 w-4 text-green-500" />
            ) : (
              <AlertCircle className="h-4 w-4 text-red-500" />
            )}
            <span className={`text-xs ${
              systemStatus?.plc?.connected ? 'text-green-600' : 'text-red-600'
            }`}>
              {systemStatus?.plc?.connected ? 'Online' : 'Offline'}
            </span>
          </div>
        </div>

        {/* Bridge Service */}
        <div className="flex items-center justify-between p-2 bg-gray-50 rounded">
          <span className="text-sm text-gray-700">Bridge Service</span>
          <div className="flex items-center space-x-2">
            {systemStatus?.bridge?.running ? (
              <CheckCircle className="h-4 w-4 text-green-500" />
            ) : (
              <AlertCircle className="h-4 w-4 text-red-500" />
            )}
            <span className={`text-xs ${
              systemStatus?.bridge?.running ? 'text-green-600' : 'text-red-600'
            }`}>
              {systemStatus?.bridge?.running ? 'Running' : 'Stopped'}
            </span>
          </div>
        </div>
      </div>

      {/* Connection Status Summary */}
      <div className="mt-4 p-3 bg-blue-50 rounded-lg">
        <div className="flex items-center space-x-2">
          <div className={`w-2 h-2 rounded-full ${
            connected && systemStatus?.dobot?.connected && systemStatus?.plc?.connected
              ? 'bg-green-500' 
              : 'bg-red-500'
          }`} />
          <span className="text-sm font-medium text-gray-900">
            {connected && systemStatus?.dobot?.connected && systemStatus?.plc?.connected
              ? 'All systems operational'
              : 'System issues detected'
            }
          </span>
        </div>
        <p className="text-xs text-gray-600 mt-1">
          {connected && systemStatus?.dobot?.connected && systemStatus?.plc?.connected
            ? 'Ready for operation'
            : 'Check connections and try again'
          }
        </p>
      </div>
    </div>
  );
}
