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
    <div className="min-h-screen bg-gray-100">
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

        <main className="flex-1 p-4 md:p-6 lg:p-8 max-w-7xl mx-auto w-full">
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
                <ControlPanel 
                  socket={socket} 
                  connected={connected}
                />
              } 
            />
            <Route 
              path="/plc" 
              element={
                <PLCMonitor 
                  socket={socket} 
                  connected={connected}
                />
              } 
            />
            <Route 
              path="/settings" 
              element={<Settings />} 
            />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}

export default App;
