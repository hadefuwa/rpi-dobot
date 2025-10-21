import { useState, useEffect } from 'react';
import { Activity, Cpu, Zap, AlertCircle, CheckCircle } from 'lucide-react';
import ConnectionStatus from './ConnectionStatus';
import PoseDisplay from './PoseDisplay';
import ControlPanel from './ControlPanel';
import PLCMonitor from './PLCMonitor';
import { systemAPI } from '../services/api';
import toast from 'react-hot-toast';

export default function Dashboard({ socket, connected }) {
  const [systemStatus, setSystemStatus] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(null);

  useEffect(() => {
    fetchSystemStatus();
    
    // Set up real-time updates via socket
    if (socket) {
      socket.on('status', (status) => {
        setSystemStatus(status);
        setLastUpdate(new Date());
      });

      socket.on('pose_updated', (pose) => {
        // Update pose in real-time
        setSystemStatus(prev => ({
          ...prev,
          dobot: { ...prev?.dobot, pose }
        }));
      });

      socket.on('dobot_connected', () => {
        toast.success('Dobot connected');
      });

      socket.on('dobot_disconnected', () => {
        toast.error('Dobot disconnected');
      });

      socket.on('plc_connected', () => {
        toast.success('PLC connected');
      });

      socket.on('plc_disconnected', () => {
        toast.error('PLC disconnected');
      });

      socket.on('emergency_stop', () => {
        toast.error('EMERGENCY STOP TRIGGERED!', { duration: 10000 });
      });
    }

    // Poll for status updates every 5 seconds
    const interval = setInterval(fetchSystemStatus, 5000);

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [socket]);

  const fetchSystemStatus = async () => {
    try {
      const response = await systemAPI.getStatus();
      setSystemStatus(response.data);
      setLastUpdate(new Date());
    } catch (error) {
      console.error('Failed to fetch system status:', error);
      toast.error('Failed to fetch system status');
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusIcon = (status) => {
    if (status === 'connected' || status === true) {
      return <CheckCircle className="h-4 w-4 text-green-500" />;
    }
    return <AlertCircle className="h-4 w-4 text-red-500" />;
  };

  const getStatusText = (status) => {
    if (status === 'connected' || status === true) {
      return 'Connected';
    }
    return 'Disconnected';
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <Activity className="h-8 w-8 animate-spin text-blue-500 mx-auto mb-4" />
          <p className="text-gray-600">Loading system status...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">System Dashboard</h1>
          <p className="text-gray-600">
            Monitor and control your Dobot Magician via S7-1200 PLC
          </p>
        </div>
        <div className="text-sm text-gray-500">
          {lastUpdate && `Last updated: ${lastUpdate.toLocaleTimeString()}`}
        </div>
      </div>

      {/* System Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Dobot Status */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Dobot Magician</h3>
            {getStatusIcon(systemStatus?.dobot?.connected)}
          </div>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Status:</span>
              <span className={`text-sm font-medium ${
                systemStatus?.dobot?.connected ? 'text-green-600' : 'text-red-600'
              }`}>
                {getStatusText(systemStatus?.dobot?.connected)}
              </span>
            </div>
            {systemStatus?.dobot?.pose && (
              <div className="text-xs text-gray-500">
                <div>X: {systemStatus.dobot.pose.x.toFixed(1)}mm</div>
                <div>Y: {systemStatus.dobot.pose.y.toFixed(1)}mm</div>
                <div>Z: {systemStatus.dobot.pose.z.toFixed(1)}mm</div>
              </div>
            )}
          </div>
        </div>

        {/* PLC Status */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">S7-1200 PLC</h3>
            {getStatusIcon(systemStatus?.plc?.connected)}
          </div>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Status:</span>
              <span className={`text-sm font-medium ${
                systemStatus?.plc?.connected ? 'text-green-600' : 'text-red-600'
              }`}>
                {getStatusText(systemStatus?.plc?.connected)}
              </span>
            </div>
            {systemStatus?.plc?.health && (
              <div className="text-xs text-gray-500">
                <div>Health: {systemStatus.plc.health.status}</div>
              </div>
            )}
          </div>
        </div>

        {/* Bridge Status */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Bridge Service</h3>
            {getStatusIcon(systemStatus?.bridge?.running)}
          </div>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Status:</span>
              <span className={`text-sm font-medium ${
                systemStatus?.bridge?.running ? 'text-green-600' : 'text-red-600'
              }`}>
                {systemStatus?.bridge?.running ? 'Running' : 'Stopped'}
              </span>
            </div>
            {systemStatus?.bridge?.isExecuting && (
              <div className="text-xs text-orange-600">
                <div>Executing command...</div>
              </div>
            )}
          </div>
        </div>

        {/* System Health */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">System Health</h3>
            <Cpu className="h-5 w-5 text-blue-500" />
          </div>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Uptime:</span>
              <span className="text-sm font-medium">
                {systemStatus?.system?.uptime ? 
                  `${Math.floor(systemStatus.system.uptime / 3600)}h ${Math.floor((systemStatus.system.uptime % 3600) / 60)}m` 
                  : 'N/A'
                }
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Memory:</span>
              <span className="text-sm font-medium">
                {systemStatus?.system?.memory ? 
                  `${Math.round(systemStatus.system.memory.heapUsed / 1024 / 1024)}MB` 
                  : 'N/A'
                }
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Real-time Components */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Connection Status */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Connection Status</h3>
          <ConnectionStatus 
            socket={socket} 
            connected={connected}
            systemStatus={systemStatus}
          />
        </div>

        {/* Current Pose */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Current Pose</h3>
          <PoseDisplay 
            pose={systemStatus?.dobot?.pose}
            connected={systemStatus?.dobot?.connected}
          />
        </div>
      </div>

      {/* Quick Controls */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Controls</h3>
        <ControlPanel 
          socket={socket} 
          connected={connected}
          compact={true}
        />
      </div>

      {/* PLC Monitor */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">PLC Monitor</h3>
        <PLCMonitor 
          socket={socket} 
          connected={connected}
          compact={true}
        />
      </div>
    </div>
  );
}
