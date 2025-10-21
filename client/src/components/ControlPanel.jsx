import { useState } from 'react';
import {
  Home,
  Move,
  Square,
  Grip,
  Play,
  Pause,
  RotateCcw,
  Loader2,
  MapPin
} from 'lucide-react';
import { dobotAPI } from '../services/api';
import { useDebugLog } from '../contexts/DebugLogContext';

export default function ControlPanel({ socket, connected, compact = false }) {
  const { addLog } = useDebugLog();
  const [isLoading, setIsLoading] = useState({});
  const [targetPose, setTargetPose] = useState({ x: 200, y: 0, z: 100, r: 0 });
  const [suctionEnabled, setSuctionEnabled] = useState(false);

  const setLoading = (action, loading) => {
    setIsLoading(prev => ({ ...prev, [action]: loading }));
  };

  const handleCommand = async (command, params = {}) => {
    if (!connected) {
      addLog('warning', 'Not connected to server');
      return;
    }

    setLoading(command, true);

    try {
      let response;

      switch (command) {
        case 'home':
          response = await dobotAPI.home();
          addLog('success', 'Home command sent');
          break;

        case 'move':
          response = await dobotAPI.move(targetPose.x, targetPose.y, targetPose.z, targetPose.r);
          addLog('success', `Move command sent to (${targetPose.x}, ${targetPose.y}, ${targetPose.z})`);
          break;

        case 'stop':
          response = await dobotAPI.stop();
          addLog('success', 'Stop command sent');
          break;

        case 'suction':
          response = await dobotAPI.setGrip(suctionEnabled);
          addLog('success', `Suction cup ${suctionEnabled ? 'enabled' : 'disabled'}`);
          break;

        default:
          throw new Error('Unknown command');
      }

      // Emit via socket for real-time updates
      if (socket) {
        socket.emit('dobot_command', { command, params });
      }

    } catch (error) {
      console.error('Command failed:', error);
      addLog('error', 'Command failed', error.message);
    } finally {
      setLoading(command, false);
    }
  };

  const handlePoseChange = (axis, value) => {
    const numValue = parseFloat(value);
    if (!isNaN(numValue)) {
      setTargetPose(prev => ({ ...prev, [axis]: numValue }));
    }
  };

  const validatePose = (pose) => {
    const limits = {
      x: { min: -300, max: 300 },
      y: { min: -300, max: 300 },
      z: { min: -100, max: 400 },
      r: { min: -180, max: 180 }
    };
    
    for (const [axis, value] of Object.entries(pose)) {
      if (value < limits[axis].min || value > limits[axis].max) {
        return false;
      }
    }
    return true;
  };

  const isPoseValid = validatePose(targetPose);

  if (compact) {
    return (
      <div className="space-y-4">
        {/* Quick Actions */}
        <div className="grid grid-cols-2 gap-2">
          <button
            onClick={() => handleCommand('home')}
            disabled={isLoading.home || !connected}
            className="btn btn-primary btn-sm"
          >
            {isLoading.home ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Home className="h-4 w-4" />
            )}
            Home
          </button>
          
          <button
            onClick={() => handleCommand('stop')}
            disabled={isLoading.stop || !connected}
            className="btn btn-error btn-sm"
          >
            {isLoading.stop ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Square className="h-4 w-4" />
            )}
            Stop
          </button>
        </div>

        {/* Suction Control */}
        <div className="flex items-center justify-between p-2 bg-gray-50 rounded">
          <span className="text-sm text-gray-700">Suction Cup</span>
          <button
            onClick={() => {
              setSuctionEnabled(!suctionEnabled);
              handleCommand('suction');
            }}
            disabled={isLoading.suction || !connected}
            className={`btn btn-sm ${
              suctionEnabled ? 'btn-success' : 'btn-secondary'
            }`}
          >
            {isLoading.suction ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Grip className="h-4 w-4" />
            )}
            {suctionEnabled ? 'On' : 'Off'}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Quick Actions */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <button
          onClick={() => handleCommand('home')}
          disabled={isLoading.home || !connected}
          className="btn btn-primary"
        >
          {isLoading.home ? (
            <Loader2 className="h-5 w-5 animate-spin" />
          ) : (
            <Home className="h-5 w-5" />
          )}
          Home
        </button>
        
        <button
          onClick={() => handleCommand('stop')}
          disabled={isLoading.stop || !connected}
          className="btn btn-error"
        >
          {isLoading.stop ? (
            <Loader2 className="h-5 w-5 animate-spin" />
          ) : (
            <Square className="h-5 w-5" />
          )}
          Stop
        </button>
        
        <button
          onClick={() => {
            setSuctionEnabled(!suctionEnabled);
            handleCommand('suction');
          }}
          disabled={isLoading.suction || !connected}
          className={`btn ${
            suctionEnabled ? 'btn-success' : 'btn-secondary'
          }`}
        >
          {isLoading.suction ? (
            <Loader2 className="h-5 w-5 animate-spin" />
          ) : (
            <Grip className="h-5 w-5" />
          )}
          Suction
        </button>
        
        <button
          onClick={() => handleCommand('move')}
          disabled={isLoading.move || !connected || !isPoseValid}
          className="btn btn-warning"
        >
          {isLoading.move ? (
            <Loader2 className="h-5 w-5 animate-spin" />
          ) : (
            <Move className="h-5 w-5" />
          )}
          Move
        </button>
      </div>

      {/* Target Position Input */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Target Position</h3>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <label className="label">X (mm)</label>
            <input
              type="number"
              value={targetPose.x}
              onChange={(e) => handlePoseChange('x', e.target.value)}
              className={`input ${!isPoseValid ? 'input-error' : ''}`}
              min="-300"
              max="300"
              step="0.1"
            />
          </div>
          
          <div>
            <label className="label">Y (mm)</label>
            <input
              type="number"
              value={targetPose.y}
              onChange={(e) => handlePoseChange('y', e.target.value)}
              className={`input ${!isPoseValid ? 'input-error' : ''}`}
              min="-300"
              max="300"
              step="0.1"
            />
          </div>
          
          <div>
            <label className="label">Z (mm)</label>
            <input
              type="number"
              value={targetPose.z}
              onChange={(e) => handlePoseChange('z', e.target.value)}
              className={`input ${!isPoseValid ? 'input-error' : ''}`}
              min="-100"
              max="400"
              step="0.1"
            />
          </div>
          
          <div>
            <label className="label">R (°)</label>
            <input
              type="number"
              value={targetPose.r}
              onChange={(e) => handlePoseChange('r', e.target.value)}
              className={`input ${!isPoseValid ? 'input-error' : ''}`}
              min="-180"
              max="180"
              step="0.1"
            />
          </div>
        </div>
        
        {!isPoseValid && (
          <p className="form-error mt-2">
            Position values are outside safe operating range
          </p>
        )}
      </div>

      {/* Preset Positions */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Preset Positions</h3>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
          <button
            onClick={() => setTargetPose({ x: 200, y: 0, z: 100, r: 0 })}
            className="btn btn-secondary btn-sm"
          >
            <MapPin className="h-4 w-4" />
            Home
          </button>
          
          <button
            onClick={() => setTargetPose({ x: 100, y: 100, z: 150, r: 45 })}
            className="btn btn-secondary btn-sm"
          >
            <MapPin className="h-4 w-4" />
            Pick
          </button>
          
          <button
            onClick={() => setTargetPose({ x: -100, y: -100, z: 150, r: -45 })}
            className="btn btn-secondary btn-sm"
          >
            <MapPin className="h-4 w-4" />
            Place
          </button>
          
          <button
            onClick={() => setTargetPose({ x: 0, y: 0, z: 200, r: 0 })}
            className="btn btn-secondary btn-sm"
          >
            <MapPin className="h-4 w-4" />
            High
          </button>
        </div>
      </div>

      {/* Status */}
      <div className="p-3 bg-gray-50 rounded-lg">
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-600">Connection Status:</span>
          <span className={`text-sm font-medium ${
            connected ? 'text-green-600' : 'text-red-600'
          }`}>
            {connected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
      </div>
    </div>
  );
}
