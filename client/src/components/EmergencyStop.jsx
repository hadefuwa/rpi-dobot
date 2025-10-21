import { AlertTriangle } from 'lucide-react';

export default function EmergencyStop({ onEmergencyStop }) {
  return (
    <button
      onClick={onEmergencyStop}
      className="emergency-stop"
      title="Emergency Stop"
      aria-label="Emergency Stop"
    >
      <div className="flex flex-col items-center">
        <AlertTriangle className="h-6 w-6" />
        <span className="text-xs font-bold">E-STOP</span>
      </div>
    </button>
  );
}
