import { useAuth } from './hooks/useAuth';
import { useSocket } from './hooks/useSocket';
import { DebugLogProvider } from './contexts/DebugLogContext';
import Dashboard from './components/Dashboard';
import Header from './components/Header';
import DebugLog from './components/DebugLog';
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
    <DebugLogProvider>
      <div className="min-h-screen bg-gray-50 relative">
        <Header user={fakeUser} onEmergencyStop={handleEmergencyStop} />

        <main className="w-full pb-20">
          <Dashboard
            socket={socket}
            connected={connected}
          />
        </main>

        <DebugLog />
      </div>
    </DebugLogProvider>
  );
}

export default App;
