import { Wifi, WifiOff, Square } from 'lucide-react';
import { useSocket } from '../hooks/useSocket';

export default function Header({ user, onEmergencyStop }) {
  const { connected } = useSocket(user?.token);

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Left side */}
          <div className="flex items-center">
            <h1 className="text-xl font-semibold text-gray-900">
              Dobot Gateway
            </h1>
          </div>

          {/* Center - Emergency Stop Button */}
          <div className="flex items-center">
            <button
              onClick={onEmergencyStop}
              className="flex flex-col items-center justify-center bg-red-600 hover:bg-red-700 text-white font-bold rounded-full w-16 h-16 shadow-lg hover:shadow-xl transition-all duration-200 hover:scale-105 active:scale-95"
              title="Emergency Stop"
              aria-label="Emergency Stop"
            >
              <Square className="h-5 w-5 mb-1" />
              <span className="text-xs font-bold leading-none">STOP</span>
            </button>
          </div>

          {/* Right side */}
          <div className="flex items-center space-x-4">
            {/* Connection status */}
            <div className="flex items-center space-x-2">
              {connected ? (
                <div className="flex items-center text-green-600">
                  <Wifi className="h-4 w-4" />
                  <span className="text-sm font-medium">Connected</span>
                </div>
              ) : (
                <div className="flex items-center text-red-600">
                  <WifiOff className="h-4 w-4" />
                  <span className="text-sm font-medium">Disconnected</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
