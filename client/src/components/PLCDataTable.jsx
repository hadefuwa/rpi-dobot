import { useState, useEffect } from 'react';
import { Database, RefreshCw, Loader2 } from 'lucide-react';
import { plcAPI } from '../services/api';
import { useDebugLog } from '../contexts/DebugLogContext';

export default function PLCDataTable({ socket, connected }) {
  const { addLog } = useDebugLog();
  const [plcData, setPlcData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(null);

  useEffect(() => {
    fetchPLCData();

    if (socket) {
      socket.on('plc_data_updated', (data) => {
        setPlcData(data);
        setLastUpdate(new Date());
      });
    }

    const interval = setInterval(fetchPLCData, 3000);
    return () => clearInterval(interval);
  }, [socket]);

  const fetchPLCData = async () => {
    if (!connected) return;

    try {
      setIsLoading(true);
      const [poseResponse, controlResponse] = await Promise.all([
        plcAPI.getPose().catch(() => ({ data: { x: 0, y: 0, z: 0 } })),
        plcAPI.getControl().catch(() => ({ data: { start: false, stop: false, home: false, estop: false } }))
      ]);

      setPlcData({
        pose: poseResponse.data,
        control: controlResponse.data
      });
      setLastUpdate(new Date());
    } catch (error) {
      addLog('error', 'Failed to fetch PLC data table', error.message);
    } finally {
      setIsLoading(false);
    }
  };

  if (!plcData) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="h-6 w-6 animate-spin text-blue-500" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Database className="h-4 w-4 text-blue-500" />
          <h4 className="text-sm font-semibold text-gray-900">PLC Data (DB1)</h4>
        </div>
        <button
          onClick={fetchPLCData}
          disabled={isLoading || !connected}
          className="p-1.5 hover:bg-gray-100 rounded transition-colors"
          title="Refresh"
        >
          <RefreshCw className={`h-3.5 w-3.5 text-gray-600 ${isLoading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Data Table */}
      <div className="overflow-hidden rounded-lg border border-gray-200">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                Variable
              </th>
              <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                Type
              </th>
              <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                Offset
              </th>
              <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase">
                Value
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {/* Target Position */}
            <tr className="hover:bg-gray-50">
              <td className="px-3 py-2 text-xs font-medium text-gray-900">Target X</td>
              <td className="px-3 py-2 text-xs text-gray-600">REAL</td>
              <td className="px-3 py-2 text-xs text-gray-600">DBD0</td>
              <td className="px-3 py-2 text-xs text-right font-mono text-blue-600">
                {plcData.pose?.x?.toFixed(2) || '0.00'}
              </td>
            </tr>
            <tr className="hover:bg-gray-50">
              <td className="px-3 py-2 text-xs font-medium text-gray-900">Target Y</td>
              <td className="px-3 py-2 text-xs text-gray-600">REAL</td>
              <td className="px-3 py-2 text-xs text-gray-600">DBD4</td>
              <td className="px-3 py-2 text-xs text-right font-mono text-blue-600">
                {plcData.pose?.y?.toFixed(2) || '0.00'}
              </td>
            </tr>
            <tr className="hover:bg-gray-50">
              <td className="px-3 py-2 text-xs font-medium text-gray-900">Target Z</td>
              <td className="px-3 py-2 text-xs text-gray-600">REAL</td>
              <td className="px-3 py-2 text-xs text-gray-600">DBD8</td>
              <td className="px-3 py-2 text-xs text-right font-mono text-blue-600">
                {plcData.pose?.z?.toFixed(2) || '0.00'}
              </td>
            </tr>

            {/* Separator - M Memory (Merker Bits) */}
            <tr className="bg-blue-50">
              <td colSpan="4" className="px-3 py-1.5 text-xs font-semibold text-blue-900">
                M Memory (Merker Bits)
              </td>
            </tr>

            {/* Control Bits - Commands (Write) */}
            <tr className="hover:bg-gray-50">
              <td className="px-3 py-2 text-xs font-medium text-gray-900">Start Robot Command</td>
              <td className="px-3 py-2 text-xs text-gray-600">BOOL</td>
              <td className="px-3 py-2 text-xs text-gray-600">M0.0</td>
              <td className="px-3 py-2 text-xs text-right">
                <span className={`px-2 py-0.5 rounded text-xs font-semibold ${
                  plcData.control?.start ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'
                }`}>
                  {plcData.control?.start ? 'TRUE' : 'FALSE'}
                </span>
              </td>
            </tr>
            <tr className="hover:bg-gray-50">
              <td className="px-3 py-2 text-xs font-medium text-gray-900">Stop Robot Command</td>
              <td className="px-3 py-2 text-xs text-gray-600">BOOL</td>
              <td className="px-3 py-2 text-xs text-gray-600">M0.1</td>
              <td className="px-3 py-2 text-xs text-right">
                <span className={`px-2 py-0.5 rounded text-xs font-semibold ${
                  plcData.control?.stop ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-600'
                }`}>
                  {plcData.control?.stop ? 'TRUE' : 'FALSE'}
                </span>
              </td>
            </tr>
            <tr className="hover:bg-gray-50">
              <td className="px-3 py-2 text-xs font-medium text-gray-900">Home / Reset Command</td>
              <td className="px-3 py-2 text-xs text-gray-600">BOOL</td>
              <td className="px-3 py-2 text-xs text-gray-600">M0.2</td>
              <td className="px-3 py-2 text-xs text-right">
                <span className={`px-2 py-0.5 rounded text-xs font-semibold ${
                  plcData.control?.home ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-600'
                }`}>
                  {plcData.control?.home ? 'TRUE' : 'FALSE'}
                </span>
              </td>
            </tr>
            <tr className="hover:bg-gray-50">
              <td className="px-3 py-2 text-xs font-medium text-gray-900">Emergency Stop</td>
              <td className="px-3 py-2 text-xs text-gray-600">BOOL</td>
              <td className="px-3 py-2 text-xs text-gray-600">M0.3</td>
              <td className="px-3 py-2 text-xs text-right">
                <span className={`px-2 py-0.5 rounded text-xs font-semibold ${
                  plcData.control?.estop ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-600'
                }`}>
                  {plcData.control?.estop ? 'TRUE' : 'FALSE'}
                </span>
              </td>
            </tr>

            {/* Additional M Memory Bits */}
            <tr className="hover:bg-gray-50">
              <td className="px-3 py-2 text-xs font-medium text-gray-900">Suction Cup Enable</td>
              <td className="px-3 py-2 text-xs text-gray-600">BOOL</td>
              <td className="px-3 py-2 text-xs text-gray-600">M0.4</td>
              <td className="px-3 py-2 text-xs text-right">
                <span className={`px-2 py-0.5 rounded text-xs font-semibold ${
                  plcData.control?.suction ? 'bg-purple-100 text-purple-700' : 'bg-gray-100 text-gray-600'
                }`}>
                  {plcData.control?.suction ? 'TRUE' : 'FALSE'}
                </span>
              </td>
            </tr>
            <tr className="bg-green-50 hover:bg-green-100">
              <td className="px-3 py-2 text-xs font-medium text-gray-900">Robot Ready Status</td>
              <td className="px-3 py-2 text-xs text-gray-600">BOOL</td>
              <td className="px-3 py-2 text-xs text-gray-600">M0.5</td>
              <td className="px-3 py-2 text-xs text-right">
                <span className={`px-2 py-0.5 rounded text-xs font-semibold ${
                  plcData.control?.ready ? 'bg-green-200 text-green-800' : 'bg-gray-100 text-gray-600'
                }`}>
                  {plcData.control?.ready ? 'READY' : 'NOT READY'}
                </span>
              </td>
            </tr>
            <tr className="bg-yellow-50 hover:bg-yellow-100">
              <td className="px-3 py-2 text-xs font-medium text-gray-900">Robot Busy Status</td>
              <td className="px-3 py-2 text-xs text-gray-600">BOOL</td>
              <td className="px-3 py-2 text-xs text-gray-600">M0.6</td>
              <td className="px-3 py-2 text-xs text-right">
                <span className={`px-2 py-0.5 rounded text-xs font-semibold ${
                  plcData.control?.busy ? 'bg-yellow-200 text-yellow-800' : 'bg-gray-100 text-gray-600'
                }`}>
                  {plcData.control?.busy ? 'BUSY' : 'IDLE'}
                </span>
              </td>
            </tr>
            <tr className="bg-red-50 hover:bg-red-100">
              <td className="px-3 py-2 text-xs font-medium text-gray-900">Robot Error Status</td>
              <td className="px-3 py-2 text-xs text-gray-600">BOOL</td>
              <td className="px-3 py-2 text-xs text-gray-600">M0.7</td>
              <td className="px-3 py-2 text-xs text-right">
                <span className={`px-2 py-0.5 rounded text-xs font-semibold ${
                  plcData.control?.error ? 'bg-red-200 text-red-800' : 'bg-gray-100 text-gray-600'
                }`}>
                  {plcData.control?.error ? 'ERROR' : 'OK'}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* Last Update */}
      {lastUpdate && (
        <p className="text-xs text-gray-500 text-right">
          Last update: {lastUpdate.toLocaleTimeString()}
        </p>
      )}
    </div>
  );
}
