import { createContext, useContext, useState } from 'react';

const DebugLogContext = createContext();

export function DebugLogProvider({ children }) {
  const [logs, setLogs] = useState([]);

  const addLog = (type, message, details = null) => {
    const timestamp = new Date();
    const log = {
      id: Date.now() + Math.random(),
      type, // 'info', 'error', 'warning', 'success'
      message,
      details,
      timestamp
    };

    setLogs(prev => [log, ...prev].slice(0, 100)); // Keep last 100 logs
  };

  const clearLogs = () => setLogs([]);

  return (
    <DebugLogContext.Provider value={{ logs, addLog, clearLogs }}>
      {children}
    </DebugLogContext.Provider>
  );
}

export function useDebugLog() {
  const context = useContext(DebugLogContext);
  if (!context) {
    throw new Error('useDebugLog must be used within DebugLogProvider');
  }
  return context;
}
