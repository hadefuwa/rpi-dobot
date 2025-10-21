import { useState, useEffect } from 'react';
import { MapPin, RotateCcw, AlertCircle } from 'lucide-react';

export default function PoseDisplay({ pose, connected }) {
  const [previousPose, setPreviousPose] = useState(null);
  const [movementDetected, setMovementDetected] = useState(false);

  useEffect(() => {
    if (pose && previousPose) {
      const threshold = 0.1; // 0.1mm threshold
      const moved = 
        Math.abs(pose.x - previousPose.x) > threshold ||
        Math.abs(pose.y - previousPose.y) > threshold ||
        Math.abs(pose.z - previousPose.z) > threshold ||
        Math.abs(pose.r - previousPose.r) > threshold;
      
      setMovementDetected(moved);
      
      // Reset movement indicator after 2 seconds
      if (moved) {
        setTimeout(() => setMovementDetected(false), 2000);
      }
    }
    
    if (pose) {
      setPreviousPose(pose);
    }
  }, [pose, previousPose]);

  if (!connected) {
    return (
      <div className="flex items-center justify-center h-32 text-gray-500">
        <div className="text-center">
          <AlertCircle className="h-8 w-8 mx-auto mb-2" />
          <p className="text-sm">Dobot not connected</p>
        </div>
      </div>
    );
  }

  if (!pose) {
    return (
      <div className="flex items-center justify-center h-32 text-gray-500">
        <div className="text-center">
          <MapPin className="h-8 w-8 mx-auto mb-2" />
          <p className="text-sm">No pose data available</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Position Display */}
      <div className="grid grid-cols-2 gap-4">
        <div className="text-center p-3 bg-gray-50 rounded-lg">
          <div className="text-2xl font-bold text-blue-600">
            {pose.x.toFixed(1)}
          </div>
          <div className="text-xs text-gray-600 uppercase">X (mm)</div>
        </div>
        
        <div className="text-center p-3 bg-gray-50 rounded-lg">
          <div className="text-2xl font-bold text-green-600">
            {pose.y.toFixed(1)}
          </div>
          <div className="text-xs text-gray-600 uppercase">Y (mm)</div>
        </div>
        
        <div className="text-center p-3 bg-gray-50 rounded-lg">
          <div className="text-2xl font-bold text-purple-600">
            {pose.z.toFixed(1)}
          </div>
          <div className="text-xs text-gray-600 uppercase">Z (mm)</div>
        </div>
        
        <div className="text-center p-3 bg-gray-50 rounded-lg">
          <div className="text-2xl font-bold text-orange-600">
            {pose.r.toFixed(1)}
          </div>
          <div className="text-xs text-gray-600 uppercase">R (°)</div>
        </div>
      </div>

      {/* Movement Indicator */}
      {movementDetected && (
        <div className="flex items-center justify-center p-2 bg-green-100 text-green-800 rounded-lg">
          <RotateCcw className="h-4 w-4 mr-2 animate-spin" />
          <span className="text-sm font-medium">Robot Moving</span>
        </div>
      )}

      {/* Status Summary */}
      <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
        <div className="flex items-center space-x-2">
          <MapPin className="h-4 w-4 text-blue-500" />
          <span className="text-sm font-medium text-gray-900">Current Position</span>
        </div>
        <div className="text-xs text-gray-600">
          {new Date().toLocaleTimeString()}
        </div>
      </div>

      {/* Coordinate System Info */}
      <div className="text-xs text-gray-500 space-y-1">
        <div className="flex justify-between">
          <span>X Range:</span>
          <span>-300 to 300 mm</span>
        </div>
        <div className="flex justify-between">
          <span>Y Range:</span>
          <span>-300 to 300 mm</span>
        </div>
        <div className="flex justify-between">
          <span>Z Range:</span>
          <span>-100 to 400 mm</span>
        </div>
        <div className="flex justify-between">
          <span>R Range:</span>
          <span>-180 to 180°</span>
        </div>
      </div>
    </div>
  );
}
