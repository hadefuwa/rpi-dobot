import { useState, useEffect } from 'react';
import { 
  Cpu, 
  Database, 
  ToggleLeft, 
  ToggleRight, 
  RefreshCw,
  Loader2,
  AlertCircle,
  CheckCircle
} from 'lucide-react';
import { plcAPI } from '../services/api';
import toast from 'react-hot-toast';

export default function PLCMonitor({ socket, connected, compact = false }) {
  const [plcData, setPlcData] = useState({
    pose: { x: 0, y: 0, z: 0 },
    control: { start: false, stop: false, home: false, estop: false },
    status: 0
  });
  const [isLoading, setIsLoading] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(null);

  useEffect(() => {
    fetchPLCData();
    
    // Set up real-time updates via socket
    if (socket) {
      socket.on('plc_data_updated', (data) => {
        setPlcData(data);
        setLastUpdate(new Date());
      });
    }

    // Poll for updates every 2 seconds
    const interval = setInterval(fetchPLCData, 2000);

    return () => clearInterval(interval);
  }, [socket]);

  const fetchPLCData = async () => {
    if (!connected) return;
    
    try {
      setIsLoading(true);
      const [poseResponse, controlResponse] = await Promise.all([
        plcAPI.getPose(),
        plcAPI.getControl()
      ]);
      
      setPlcData({
        pose: poseResponse.data,
        control: controlResponse.data,
        status: 0 // Would need separate API call for status
      });
      setLastUpdate(new Date());
    } catch (error) {
      console.error('Failed to fetch PLC data:', error);
      if (!isLoading) {
        toast.error('Failed to fetch PLC data');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleControlBit = async (bit, value) => {
    if (!connected) {
      toast.error('Not connected to server');
      return;
    }

    try {
      await plcAPI.setControl({ [bit]: value });
      setPlcData(prev => ({
        ...prev,
        control: { ...prev.control, [bit]: value }
      }));
      toast.success(`${bit} ${value ? 'set' : 'cleared'}`);
    } catch (error) {
      console.error('Failed to set control bit:', error);
      toast.error(`Failed to set ${bit}`);
    }
  };

  const getStatusText = (status) => {
    const statusMap = {
      0: 'Idle',
      1: 'Executing',
      2: 'Error',
      3: 'Homing',
      4: 'Stopped',
      5: 'Emergency Stop'
    };
    return statusMap[status] || 'Unknown';
  };

  const getStatusColor = (status) => {
    const colorMap = {
      0: 'text-gray-600',
      1: 'text-blue-600',
      2: 'text-red-600',
      3: 'text-yellow-600',
      4: 'text-orange-600',
      5: 'text-red-600'
    };
    return colorMap[status] || 'text-gray-600';
  };

  if (compact) {
    return (
      <div className="space-y-4">
        {/* Control Bits */}
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-gray-900">Control Bits</h4>
          <div className="grid grid-cols-2 gap-2">
            {Object.entries(plcData.control).map(([bit, value]) => (
              <div key={bit} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                <span className="text-xs text-gray-700 capitalize">{bit}</span>
                <button
                  onClick={() => handleControlBit(bit, !value)}
                  disabled={!connected}
                  className={`flex items-center space-x-1 ${
                    value ? 'text-green-600' : 'text-gray-400'
                  }`}
                >
                  {value ? (
                    <ToggleRight className="h-4 w-4" />
                  ) : (
                    <ToggleLeft className="h-4 w-4" />
                  )}
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Status */}
        <div className="flex items-center justify-between p-2 bg-gray-50 rounded">
          <span className="text-sm text-gray-700">Status</span>
          <span className={`text-sm font-medium ${getStatusColor(plcData.status)}`}>
            {getStatusText(plcData.status)}
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Cpu className="h-5 w-5 text-blue-500" />
          <h3 className="text-lg font-semibold text-gray-900">PLC Monitor</h3>
        </div>
        <button
          onClick={fetchPLCData}
          disabled={isLoading || !connected}
          className="btn btn-secondary btn-sm"
        >
          {isLoading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <RefreshCw className="h-4 w-4" />
          )}
          Refresh
        </button>
      </div>

      {/* Connection Status */}
      <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
        <div className="flex items-center space-x-2">
          {connected ? (
            <CheckCircle className="h-4 w-4 text-green-500" />
          ) : (
            <AlertCircle className="h-4 w-4 text-red-500" />
          )}
          <span className="text-sm font-medium text-gray-900">
            PLC Connection
          </span>
        </div>
        <span className={`text-sm ${
          connected ? 'text-green-600' : 'text-red-600'
        }`}>
          {connected ? 'Connected' : 'Disconnected'}
        </span>
      </div>

      {/* PLC Pose Data */}
      <div className="card">
        <h4 className="text-md font-semibold text-gray-900 mb-4">PLC Pose Data</h4>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center p-3 bg-gray-50 rounded">
            <div className="text-xl font-bold text-blue-600">
              {plcData.pose.x.toFixed(1)}
            </div>
            <div className="text-xs text-gray-600">X (mm)</div>
          </div>
          
          <div className="text-center p-3 bg-gray-50 rounded">
            <div className="text-xl font-bold text-green-600">
              {plcData.pose.y.toFixed(1)}
            </div>
            <div className="text-xs text-gray-600">Y (mm)</div>
          </div>
          
          <div className="text-center p-3 bg-gray-50 rounded">
            <div className="text-xl font-bold text-purple-600">
              {plcData.pose.z.toFixed(1)}
            </div>
            <div className="text-xs text-gray-600">Z (mm)</div>
          </div>
          
          <div className="text-center p-3 bg-gray-50 rounded">
            <div className="text-xl font-bold text-orange-600">
              {plcData.status}
            </div>
            <div className="text-xs text-gray-600">Status</div>
          </div>
        </div>
      </div>

      {/* Control Bits */}
      <div className="card">
        <h4 className="text-md font-semibold text-gray-900 mb-4">Control Bits</h4>
        <div className="grid grid-cols-2 gap-4">
          {Object.entries(plcData.control).map(([bit, value]) => (
            <div key={bit} className="flex items-center justify-between p-3 bg-gray-50 rounded">
              <div className="flex items-center space-x-2">
                <Database className="h-4 w-4 text-gray-500" />
                <span className="text-sm font-medium text-gray-900 capitalize">
                  {bit}
                </span>
              </div>
              <button
                onClick={() => handleControlBit(bit, !value)}
                disabled={!connected}
                className={`flex items-center space-x-2 p-2 rounded ${
                  value 
                    ? 'bg-green-100 text-green-700' 
                    : 'bg-gray-100 text-gray-500'
                }`}
              >
                {value ? (
                  <ToggleRight className="h-5 w-5" />
                ) : (
                  <ToggleLeft className="h-5 w-5" />
                )}
                <span className="text-sm font-medium">
                  {value ? 'ON' : 'OFF'}
                </span>
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Status Information */}
      <div className="card">
        <h4 className="text-md font-semibold text-gray-900 mb-4">System Status</h4>
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">Current Status:</span>
            <span className={`text-sm font-medium ${getStatusColor(plcData.status)}`}>
              {getStatusText(plcData.status)}
            </span>
          </div>
          
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">Last Update:</span>
            <span className="text-sm text-gray-500">
              {lastUpdate ? lastUpdate.toLocaleTimeString() : 'Never'}
            </span>
          </div>
        </div>
      </div>

      {/* Memory Map Reference */}
      <div className="card">
        <h4 className="text-md font-semibold text-gray-900 mb-4">Memory Map</h4>
        <div className="text-xs text-gray-600 space-y-1">
          <div className="flex justify-between">
            <span>M0.0:</span>
            <span>Start Command</span>
          </div>
          <div className="flex justify-between">
            <span>M0.1:</span>
            <span>Stop Command</span>
          </div>
          <div className="flex justify-between">
            <span>M0.2:</span>
            <span>Home Command</span>
          </div>
          <div className="flex justify-between">
            <span>M0.3:</span>
            <span>Emergency Stop</span>
          </div>
          <div className="flex justify-between">
            <span>DB1.DBD0-8:</span>
            <span>Target Position</span>
          </div>
          <div className="flex justify-between">
            <span>DB1.DBD12-20:</span>
            <span>Current Position</span>
          </div>
        </div>
      </div>
    </div>
  );
}
