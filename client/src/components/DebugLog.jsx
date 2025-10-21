import { useState } from 'react';
import { Terminal, X, ChevronDown, ChevronUp, Trash2, AlertCircle, Info, CheckCircle, AlertTriangle } from 'lucide-react';
import { useDebugLog } from '../contexts/DebugLogContext';

export default function DebugLog() {
  const { logs, clearLogs } = useDebugLog();
  const [isExpanded, setIsExpanded] = useState(false);

  const getIcon = (type) => {
    switch (type) {
      case 'error':
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      case 'warning':
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      case 'success':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      default:
        return <Info className="h-4 w-4 text-blue-500" />;
    }
  };

  const getTextColor = (type) => {
    switch (type) {
      case 'error':
        return 'text-red-700';
      case 'warning':
        return 'text-yellow-700';
      case 'success':
        return 'text-green-700';
      default:
        return 'text-gray-700';
    }
  };

  const errorCount = logs.filter(log => log.type === 'error').length;
  const warningCount = logs.filter(log => log.type === 'warning').length;

  return (
    <div className="fixed bottom-4 right-4 z-50 w-80 max-w-[calc(100vw-2rem)] max-h-[calc(100vh-2rem)]">
      {/* Collapsed Header */}
      <div
        className="bg-gray-900 text-white rounded-t-lg px-3 py-1.5 cursor-pointer hover:bg-gray-800 transition-colors flex items-center justify-between shadow-lg"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-2">
          <Terminal className="h-3.5 w-3.5" />
          <span className="font-medium text-xs">Debug</span>
          {errorCount > 0 && (
            <span className="bg-red-500 text-white text-xs px-1.5 py-0.5 rounded-full font-medium">
              {errorCount}
            </span>
          )}
          {warningCount > 0 && (
            <span className="bg-yellow-500 text-white text-xs px-1.5 py-0.5 rounded-full font-medium">
              {warningCount}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {logs.length > 0 && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                clearLogs();
              }}
              className="p-1 hover:bg-gray-700 rounded"
              title="Clear logs"
            >
              <Trash2 className="h-3 w-3" />
            </button>
          )}
          {isExpanded ? (
            <ChevronDown className="h-3.5 w-3.5" />
          ) : (
            <ChevronUp className="h-3.5 w-3.5" />
          )}
        </div>
      </div>

      {/* Expanded Content - Terminal Style */}
      {isExpanded && (
        <div className="bg-gray-950 text-gray-200 border border-gray-700 rounded-b-lg shadow-lg h-64 max-h-64 overflow-hidden flex flex-col font-mono text-xs">
          {logs.length === 0 ? (
            <div className="p-3 text-center text-gray-500">
              No logs
            </div>
          ) : (
            <div className="flex-1 overflow-y-auto px-2 py-1 space-y-0.5">
              {logs.map((log) => (
                <div key={log.id} className="leading-tight">
                  <span className="text-gray-500 text-[10px]">
                    [{log.timestamp.toLocaleTimeString()}]
                  </span>
                  {' '}
                  <span className={
                    log.type === 'error' ? 'text-red-400' :
                    log.type === 'warning' ? 'text-yellow-400' :
                    log.type === 'success' ? 'text-green-400' :
                    'text-blue-400'
                  }>
                    {log.type.toUpperCase()}:
                  </span>
                  {' '}
                  <span className="text-gray-200">
                    {log.message}
                  </span>
                  {log.details && (
                    <div className="text-gray-400 text-[10px] ml-20">
                      → {log.details}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
