import { useState, useEffect } from 'react';
import { Activity, Cpu, CheckCircle, AlertCircle } from 'lucide-react';
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

    if (socket) {
      socket.on('status', (status) => {
        setSystemStatus(status);
        setLastUpdate(new Date());
      });

      socket.on('pose_updated', (pose) => {
        setSystemStatus(prev => ({
          ...prev,
          dobot: { ...prev?.dobot, pose }
        }));
      });

      socket.on('dobot_connected', () => toast.success('Dobot connected'));
      socket.on('dobot_disconnected', () => toast.error('Dobot disconnected'));
      socket.on('plc_connected', () => toast.success('PLC connected'));
      socket.on('plc_disconnected', () => toast.error('PLC disconnected'));
      socket.on('emergency_stop', () => toast.error('EMERGENCY STOP!', { duration: 10000 }));
    }

    const interval = setInterval(fetchSystemStatus, 5000);
    return () => { if (interval) clearInterval(interval); };
  }, [socket]);

  const fetchSystemStatus = async () => {
    try {
      const response = await systemAPI.getStatus();
      setSystemStatus(response.data);
      setLastUpdate(new Date());
    } catch (error) {
      console.error('Failed to fetch system status:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusIcon = (status) => {
    return (status === 'connected' || status === true)
      ? <CheckCircle className="h-3 w-3 text-green-500" />
      : <AlertCircle className="h-3 w-3 text-red-500" />;
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Activity className="h-8 w-8 animate-spin text-blue-500" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
            <p className="text-sm text-gray-600 mt-1">
              Real-time monitoring and control of the Dobot Gateway system
            </p>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-sm text-gray-500">
              Last update: {lastUpdate ? lastUpdate.toLocaleTimeString() : 'Never'}
            </div>
            <div className={`status-indicator ${
              connected ? 'status-connected' : 'status-disconnected'
            }`}>
              {connected ? 'Connected' : 'Disconnected'}
            </div>
          </div>
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-12 gap-6">
        
        {/* Left Column - System Status (3 cols) */}
        <div className="col-span-3 space-y-6">
          {/* System Status Cards */}
          <div className="grid gap-4">
            {/* Dobot Status */}
            <div className="card">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold text-gray-900">Dobot Robot</h3>
                {getStatusIcon(systemStatus?.dobot?.connected)}
              </div>
              <div className="space-y-2">
                <div className={`text-sm ${
                  systemStatus?.dobot?.connected ? 'text-green-600' : 'text-red-600'
                }`}>
                  {systemStatus?.dobot?.connected ? 'Connected' : 'Disconnected'}
                </div>
                {systemStatus?.dobot?.pose && (
                  <div className="text-xs text-gray-500 space-y-1">
                    <div>X: {systemStatus.dobot.pose.x.toFixed(1)}mm</div>
                    <div>Y: {systemStatus.dobot.pose.y.toFixed(1)}mm</div>
                    <div>Z: {systemStatus.dobot.pose.z.toFixed(1)}mm</div>
                  </div>
                )}
              </div>
            </div>

            {/* PLC Status */}
            <div className="card">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold text-gray-900">PLC Controller</h3>
                {getStatusIcon(systemStatus?.plc?.connected)}
              </div>
              <div className={`text-sm ${
                systemStatus?.plc?.connected ? 'text-green-600' : 'text-red-600'
              }`}>
                {systemStatus?.plc?.connected ? 'Connected' : 'Disconnected'}
              </div>
            </div>

            {/* Bridge Status */}
            <div className="card">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold text-gray-900">Bridge Service</h3>
                {getStatusIcon(systemStatus?.bridge?.running)}
              </div>
              <div className={`text-sm ${
                systemStatus?.bridge?.running ? 'text-green-600' : 'text-red-600'
              }`}>
                {systemStatus?.bridge?.running ? 'Running' : 'Stopped'}
              </div>
            </div>

            {/* System Info */}
            <div className="card">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold text-gray-900">System Info</h3>
                <Cpu className="h-4 w-4 text-blue-500" />
              </div>
              <div className="text-xs text-gray-600 space-y-1">
                <div>Uptime: {systemStatus?.system?.uptime ?
                  `${Math.floor(systemStatus.system.uptime / 3600)}h ${Math.floor((systemStatus.system.uptime % 3600) / 60)}m`
                  : 'N/A'}
                </div>
                <div>Memory: {systemStatus?.system?.memory ?
                  `${Math.round(systemStatus.system.memory.heapUsed / 1024 / 1024)}MB`
                  : 'N/A'}
                </div>
              </div>
            </div>
          </div>

          {/* Connection Status */}
          <div className="card">
            <h3 className="text-sm font-semibold text-gray-900 mb-3">Connection Status</h3>
            <ConnectionStatus
              socket={socket}
              connected={connected}
              systemStatus={systemStatus}
            />
          </div>
        </div>

        {/* Middle Column - Controls (5 cols) */}
        <div className="col-span-5">
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Robot Controls</h3>
            <ControlPanel
              socket={socket}
              connected={connected}
              compact={false}
            />
          </div>
        </div>

        {/* Right Column - Monitoring (4 cols) */}
        <div className="col-span-4 space-y-6">
          {/* Current Pose */}
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Current Position</h3>
            <PoseDisplay
              pose={systemStatus?.dobot?.pose}
              connected={systemStatus?.dobot?.connected}
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
      </div>
    </div>
  );
}
