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
    <div className="h-[calc(100vh-70px)] overflow-hidden p-2">
      {/* Compact Header */}
      <div className="flex items-center justify-between mb-2">
        <h1 className="text-lg font-bold">Dashboard</h1>
        <span className="text-xs text-gray-500">
          {lastUpdate && lastUpdate.toLocaleTimeString()}
        </span>
      </div>

      {/* Single Page Grid - No Scroll */}
      <div className="grid grid-cols-12 gap-2 h-[calc(100%-40px)]">

        {/* Left Column - Status Indicators (3 cols) */}
        <div className="col-span-3 space-y-2">
          {/* Dobot */}
          <div className="card p-2">
            <div className="flex items-center justify-between mb-1">
              <h3 className="text-xs font-semibold">Dobot</h3>
              {getStatusIcon(systemStatus?.dobot?.connected)}
            </div>
            <div className="text-xs text-gray-600">
              {systemStatus?.dobot?.connected ? 'Connected' : 'Disconnected'}
            </div>
            {systemStatus?.dobot?.pose && (
              <div className="text-[10px] text-gray-500 mt-1">
                <div>X: {systemStatus.dobot.pose.x.toFixed(0)}</div>
                <div>Y: {systemStatus.dobot.pose.y.toFixed(0)}</div>
                <div>Z: {systemStatus.dobot.pose.z.toFixed(0)}</div>
              </div>
            )}
          </div>

          {/* PLC */}
          <div className="card p-2">
            <div className="flex items-center justify-between mb-1">
              <h3 className="text-xs font-semibold">PLC</h3>
              {getStatusIcon(systemStatus?.plc?.connected)}
            </div>
            <div className="text-xs text-gray-600">
              {systemStatus?.plc?.connected ? 'Connected' : 'Disconnected'}
            </div>
          </div>

          {/* Bridge */}
          <div className="card p-2">
            <div className="flex items-center justify-between mb-1">
              <h3 className="text-xs font-semibold">Bridge</h3>
              {getStatusIcon(systemStatus?.bridge?.running)}
            </div>
            <div className="text-xs text-gray-600">
              {systemStatus?.bridge?.running ? 'Running' : 'Stopped'}
            </div>
          </div>

          {/* System */}
          <div className="card p-2">
            <div className="flex items-center justify-between mb-1">
              <h3 className="text-xs font-semibold">System</h3>
              <Cpu className="h-3 w-3 text-blue-500" />
            </div>
            <div className="text-[10px] text-gray-600">
              <div>Up: {systemStatus?.system?.uptime ?
                `${Math.floor(systemStatus.system.uptime / 3600)}h ${Math.floor((systemStatus.system.uptime % 3600) / 60)}m`
                : 'N/A'}
              </div>
              <div>Mem: {systemStatus?.system?.memory ?
                `${Math.round(systemStatus.system.memory.heapUsed / 1024 / 1024)}MB`
                : 'N/A'}
              </div>
            </div>
          </div>

          {/* Connection Status */}
          <div className="card p-2 flex-1 overflow-auto">
            <h3 className="text-xs font-semibold mb-1">Connections</h3>
            <ConnectionStatus
              socket={socket}
              connected={connected}
              systemStatus={systemStatus}
            />
          </div>
        </div>

        {/* Middle Column - Controls (5 cols) */}
        <div className="col-span-5 space-y-2 overflow-auto">
          <div className="card p-3">
            <h3 className="text-sm font-semibold mb-2">Controls</h3>
            <ControlPanel
              socket={socket}
              connected={connected}
              compact={true}
            />
          </div>
        </div>

        {/* Right Column - Monitoring (4 cols) */}
        <div className="col-span-4 space-y-2 overflow-auto">
          {/* Current Pose */}
          <div className="card p-2">
            <h3 className="text-xs font-semibold mb-2">Current Pose</h3>
            <PoseDisplay
              pose={systemStatus?.dobot?.pose}
              connected={systemStatus?.dobot?.connected}
            />
          </div>

          {/* PLC Monitor */}
          <div className="card p-2">
            <h3 className="text-xs font-semibold mb-2">PLC Monitor</h3>
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
