import { useState, useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './hooks/useAuth';
import { useSocket } from './hooks/useSocket';
import Login from './components/Login';
import Dashboard from './components/Dashboard';
import ControlPanel from './components/ControlPanel';
import PLCMonitor from './components/PLCMonitor';
import Settings from './components/Settings';
import EmergencyStop from './components/EmergencyStop';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import LoadingSpinner from './components/LoadingSpinner';
import './App.css';

function App() {
  const { user, login, logout, isLoading } = useAuth();

  // Skip auth - use fake user for development
  const fakeUser = user || {
    username: 'admin',
    role: 'admin',
    token: 'fake-token-no-auth'
  };

  const { socket, connected } = useSocket(fakeUser?.token);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // Handle emergency stop
  const handleEmergencyStop = async () => {
    try {
      const response = await fetch('/api/emergency-stop', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (response.ok) {
        console.log('Emergency stop executed');
      } else {
        console.error('Emergency stop failed');
      }
    } catch (error) {
      console.error('Emergency stop error:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <EmergencyStop onEmergencyStop={handleEmergencyStop} />

      <Header
        user={fakeUser}
        onLogout={logout}
        onMenuClick={() => setSidebarOpen(!sidebarOpen)}
      />
      
      <div className="flex">
        <Sidebar
          isOpen={sidebarOpen}
          onClose={() => setSidebarOpen(false)}
        />

        <main className="flex-1 w-full">
          <Routes>
            <Route 
              path="/" 
              element={
                <Dashboard 
                  socket={socket} 
                  connected={connected}
                />
              } 
            />
            <Route 
              path="/control" 
              element={
                <div className="min-h-screen bg-gray-50 p-6">
                  <div className="max-w-6xl mx-auto">
                    <h1 className="text-2xl font-bold text-gray-900 mb-6">Control Panel</h1>
                    <ControlPanel 
                      socket={socket} 
                      connected={connected}
                    />
                  </div>
                </div>
              } 
            />
            <Route 
              path="/plc" 
              element={
                <div className="min-h-screen bg-gray-50 p-6">
                  <div className="max-w-6xl mx-auto">
                    <h1 className="text-2xl font-bold text-gray-900 mb-6">PLC Monitor</h1>
                    <PLCMonitor 
                      socket={socket} 
                      connected={connected}
                    />
                  </div>
                </div>
              } 
            />
            <Route 
              path="/settings" 
              element={
                <div className="min-h-screen bg-gray-50 p-6">
                  <div className="max-w-4xl mx-auto">
                    <h1 className="text-2xl font-bold text-gray-900 mb-6">Settings</h1>
                    <Settings />
                  </div>
                </div>
              } 
            />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}

export default App;
