import { AlertTriangle } from 'lucide-react';

export default function EmergencyStop({ onEmergencyStop }) {
  return (
    <button
      onClick={onEmergencyStop}
      className="emergency-stop"
      title="Emergency Stop"
      aria-label="Emergency Stop"
    >
      <AlertTriangle className="h-4 w-4 mb-1" />
      <span className="text-xs font-bold leading-none">E-STOP</span>
    </button>
  );
}
