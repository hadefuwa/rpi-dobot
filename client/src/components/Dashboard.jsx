import { useState, useEffect } from 'react';
import { Activity, Cpu, CheckCircle, AlertCircle, HelpCircle, ChevronDown, ChevronUp } from 'lucide-react';
import ConnectionStatus from './ConnectionStatus';
import PoseDisplay from './PoseDisplay';
import ControlPanel from './ControlPanel';
import PLCMonitor from './PLCMonitor';
import PLCDataTable from './PLCDataTable';
import { systemAPI } from '../services/api';
import { useDebugLog } from '../contexts/DebugLogContext';

export default function Dashboard({ socket, connected }) {
  const { addLog } = useDebugLog();
  const [systemStatus, setSystemStatus] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [showHelp, setShowHelp] = useState(false);

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

      socket.on('dobot_connected', () => addLog('success', 'Dobot connected'));
      socket.on('dobot_disconnected', () => addLog('error', 'Dobot disconnected'));
      socket.on('plc_connected', () => addLog('success', 'PLC connected'));
      socket.on('plc_disconnected', () => addLog('error', 'PLC disconnected'));
      socket.on('emergency_stop', () => addLog('error', 'EMERGENCY STOP!'));
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
      addLog('error', 'Failed to fetch system status', error.message);
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
            <button
              onClick={() => setShowHelp(!showHelp)}
              className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded-lg transition-colors"
            >
              <HelpCircle className="h-4 w-4" />
              Help
              {showHelp ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            </button>
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

      {/* Help Section */}
      {showHelp && (
        <div className="mb-6 card bg-blue-50 border-blue-200">
          <div className="flex items-start gap-3">
            <HelpCircle className="h-5 w-5 text-blue-600 mt-0.5 flex-shrink-0" />
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-gray-900 mb-3">How to Use This App</h3>

              <div className="space-y-4 text-sm text-gray-700">
                <div>
                  <h4 className="font-semibold text-gray-900 mb-2">🎯 Quick Start</h4>
                  <ul className="list-disc list-inside space-y-1 ml-2">
                    <li><strong>Home Button:</strong> Send the robot to its home position (safe starting point)</li>
                    <li><strong>Stop Button:</strong> Immediately stop all robot movement</li>
                    <li><strong>Emergency Stop:</strong> Red button in top-right corner - use in case of emergency</li>
                  </ul>
                </div>

                <div>
                  <h4 className="font-semibold text-gray-900 mb-2">🎮 Robot Controls</h4>
                  <ul className="list-disc list-inside space-y-1 ml-2">
                    <li><strong>Target Position:</strong> Enter X, Y, Z coordinates (in mm) and R rotation (in degrees)</li>
                    <li><strong>Preset Positions:</strong> Click preset buttons (Home, Pick, Place, High) to set common positions</li>
                    <li><strong>Move Button:</strong> Click to move the robot to the target position (only enabled when values are valid)</li>
                    <li><strong>Suction Cup:</strong> Toggle on/off to control the vacuum gripper</li>
                  </ul>
                </div>

                <div>
                  <h4 className="font-semibold text-gray-900 mb-2">📊 Monitoring</h4>
                  <ul className="list-disc list-inside space-y-1 ml-2">
                    <li><strong>System Status:</strong> Left panel shows connection status for Dobot, PLC, and Bridge</li>
                    <li><strong>Current Position:</strong> Right panel displays real-time robot coordinates</li>
                    <li><strong>PLC Monitor:</strong> Shows PLC inputs/outputs and trigger status</li>
                  </ul>
                </div>

                <div>
                  <h4 className="font-semibold text-gray-900 mb-2">⚠️ Safety Limits</h4>
                  <ul className="list-disc list-inside space-y-1 ml-2">
                    <li>X & Y: -300mm to +300mm</li>
                    <li>Z: -100mm to +400mm</li>
                    <li>R: -180° to +180°</li>
                    <li>Values outside these ranges will be rejected</li>
                  </ul>
                </div>

                <div className="pt-2 border-t border-blue-300">
                  <p className="text-xs text-gray-600">
                    💡 <strong>Tip:</strong> Always ensure the Dobot is connected (green status) before sending commands.
                    Use the Home button first if you're unsure of the robot's current position.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Main Grid */}
      <div className="grid grid-cols-3 gap-6">

        {/* Left Column - System Status */}
        <div className="space-y-6">
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

        {/* Middle Column - Controls */}
        <div>
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Robot Controls</h3>
            <ControlPanel
              socket={socket}
              connected={connected}
              compact={false}
            />
          </div>
        </div>

        {/* Right Column - Monitoring */}
        <div className="space-y-6">
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

          {/* PLC Data Table */}
          <div className="card">
            <PLCDataTable
              socket={socket}
              connected={connected}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
