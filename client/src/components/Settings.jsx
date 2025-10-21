import { useState, useEffect } from 'react';
import { 
  Settings as SettingsIcon, 
  Save, 
  RefreshCw, 
  AlertCircle,
  CheckCircle,
  Wifi,
  Cpu,
  Database,
  TestTube
} from 'lucide-react';
import { systemAPI } from '../services/api';
import toast from 'react-hot-toast';

export default function Settings() {
  const [settings, setSettings] = useState({
    dobot: {
      host: '192.168.0.30',
      port: 29999,
      useUSB: false,
      usbPath: '/dev/ttyUSB0'
    },
    plc: {
      ip: '192.168.0.10',
      rack: 0,
      slot: 1
    },
    system: {
      pollInterval: 100,
      logLevel: 'info'
    }
  });
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isTestingPLC, setIsTestingPLC] = useState(false);
  const [systemInfo, setSystemInfo] = useState(null);
  const [plcTestResult, setPlcTestResult] = useState(null);

  useEffect(() => {
    fetchSystemInfo();
    loadSettings();
  }, []);

  const fetchSystemInfo = async () => {
    try {
      setIsLoading(true);
      const response = await systemAPI.getStatus();
      setSystemInfo(response.data);
    } catch (error) {
      console.error('Failed to fetch system info:', error);
      toast.error('Failed to fetch system information');
    } finally {
      setIsLoading(false);
    }
  };

  const loadSettings = async () => {
    try {
      const response = await systemAPI.getSettings();
      setSettings(response.data);
    } catch (error) {
      console.error('Failed to load settings:', error);
      toast.error('Failed to load settings');
    }
  };

  const handleSettingChange = (category, key, value) => {
    setSettings(prev => ({
      ...prev,
      [category]: {
        ...prev[category],
        [key]: value
      }
    }));
  };

  const handleSave = async () => {
    try {
      setIsSaving(true);
      await systemAPI.saveSettings(settings);
      toast.success('Settings saved successfully');
    } catch (error) {
      console.error('Failed to save settings:', error);
      toast.error('Failed to save settings');
    } finally {
      setIsSaving(false);
    }
  };

  const testPLCConnection = async () => {
    try {
      setIsTestingPLC(true);
      setPlcTestResult(null);
      
      const response = await systemAPI.testPLCConnection(settings.plc);
      setPlcTestResult(response.data);
      
      if (response.data.success) {
        toast.success('PLC connection test successful!');
      } else {
        toast.error('PLC connection test failed');
      }
    } catch (error) {
      console.error('PLC connection test failed:', error);
      toast.error('PLC connection test failed');
      setPlcTestResult({ success: false, error: error.message });
    } finally {
      setIsTestingPLC(false);
    }
  };

  const handleReset = () => {
    setSettings({
      dobot: {
        host: '192.168.0.30',
        port: 29999,
        useUSB: false,
        usbPath: '/dev/ttyUSB0'
      },
      plc: {
        ip: '192.168.0.10',
        rack: 0,
        slot: 1
      },
      system: {
        pollInterval: 100,
        logLevel: 'info'
      }
    });
    toast.success('Settings reset to defaults');
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <SettingsIcon className="h-5 w-5 text-blue-500" />
          <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        </div>
        <div className="flex space-x-2">
          <button
            onClick={handleReset}
            className="btn btn-secondary"
          >
            <RefreshCw className="h-4 w-4" />
            Reset
          </button>
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="btn btn-primary"
          >
            {isSaving ? (
              <RefreshCw className="h-4 w-4 animate-spin" />
            ) : (
              <Save className="h-4 w-4" />
            )}
            Save
          </button>
        </div>
      </div>

      {/* System Information */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">System Information</h3>
        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <RefreshCw className="h-6 w-6 animate-spin text-blue-500" />
          </div>
        ) : systemInfo ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <div className="flex items-center space-x-2">
                <Cpu className="h-4 w-4 text-gray-500" />
                <span className="text-sm text-gray-600">Uptime:</span>
                <span className="text-sm font-medium">
                  {Math.floor(systemInfo.system.uptime / 3600)}h {Math.floor((systemInfo.system.uptime % 3600) / 60)}m
                </span>
              </div>
              <div className="flex items-center space-x-2">
                <Database className="h-4 w-4 text-gray-500" />
                <span className="text-sm text-gray-600">Memory:</span>
                <span className="text-sm font-medium">
                  {Math.round(systemInfo.system.memory.heapUsed / 1024 / 1024)}MB
                </span>
              </div>
            </div>
            <div className="space-y-2">
              <div className="flex items-center space-x-2">
                <Wifi className="h-4 w-4 text-gray-500" />
                <span className="text-sm text-gray-600">Dobot:</span>
                <span className={`text-sm font-medium ${
                  systemInfo.dobot.connected ? 'text-green-600' : 'text-red-600'
                }`}>
                  {systemInfo.dobot.connected ? 'Connected' : 'Disconnected'}
                </span>
              </div>
              <div className="flex items-center space-x-2">
                <Database className="h-4 w-4 text-gray-500" />
                <span className="text-sm text-gray-600">PLC:</span>
                <span className={`text-sm font-medium ${
                  systemInfo.plc.connected ? 'text-green-600' : 'text-red-600'
                }`}>
                  {systemInfo.plc.connected ? 'Connected' : 'Disconnected'}
                </span>
              </div>
            </div>
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            <AlertCircle className="h-8 w-8 mx-auto mb-2" />
            <p>Failed to load system information</p>
          </div>
        )}
      </div>

      {/* Dobot Settings */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Dobot Configuration</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="label">Host/IP Address</label>
            <input
              type="text"
              value={settings.dobot.host}
              onChange={(e) => handleSettingChange('dobot', 'host', e.target.value)}
              className="input"
              placeholder="192.168.0.30"
            />
          </div>
          
          <div>
            <label className="label">Port</label>
            <input
              type="number"
              value={settings.dobot.port}
              onChange={(e) => handleSettingChange('dobot', 'port', parseInt(e.target.value))}
              className="input"
              min="1"
              max="65535"
            />
          </div>
          
          <div className="md:col-span-2">
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={settings.dobot.useUSB}
                onChange={(e) => handleSettingChange('dobot', 'useUSB', e.target.checked)}
                className="rounded"
              />
              <span className="text-sm font-medium text-gray-900">Use USB Connection</span>
            </label>
          </div>
          
          {settings.dobot.useUSB && (
            <div className="md:col-span-2">
              <label className="label">USB Device Path</label>
              <input
                type="text"
                value={settings.dobot.usbPath}
                onChange={(e) => handleSettingChange('dobot', 'usbPath', e.target.value)}
                className="input"
                placeholder="/dev/ttyUSB0"
              />
            </div>
          )}
        </div>
      </div>

      {/* PLC Settings */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">PLC Configuration</h3>
          <button
            onClick={testPLCConnection}
            disabled={isTestingPLC}
            className="btn btn-secondary btn-sm"
          >
            {isTestingPLC ? (
              <RefreshCw className="h-4 w-4 animate-spin" />
            ) : (
              <TestTube className="h-4 w-4" />
            )}
            {isTestingPLC ? 'Testing...' : 'Test Connection'}
          </button>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="label">IP Address</label>
            <input
              type="text"
              value={settings.plc.ip}
              onChange={(e) => handleSettingChange('plc', 'ip', e.target.value)}
              className="input"
              placeholder="192.168.0.10"
            />
          </div>
          
          <div>
            <label className="label">Rack</label>
            <input
              type="number"
              value={settings.plc.rack}
              onChange={(e) => handleSettingChange('plc', 'rack', parseInt(e.target.value))}
              className="input"
              min="0"
              max="7"
            />
          </div>
          
          <div>
            <label className="label">Slot</label>
            <input
              type="number"
              value={settings.plc.slot}
              onChange={(e) => handleSettingChange('plc', 'slot', parseInt(e.target.value))}
              className="input"
              min="0"
              max="31"
            />
          </div>
        </div>
        
        {/* PLC Test Results */}
        {plcTestResult && (
          <div className={`mt-4 p-4 rounded-lg border ${
            plcTestResult.success 
              ? 'bg-green-50 border-green-200' 
              : 'bg-red-50 border-red-200'
          }`}>
            <div className="flex items-start space-x-2">
              {plcTestResult.success ? (
                <CheckCircle className="h-5 w-5 text-green-600 mt-0.5" />
              ) : (
                <AlertCircle className="h-5 w-5 text-red-600 mt-0.5" />
              )}
              <div className="flex-1">
                <h4 className={`text-sm font-medium ${
                  plcTestResult.success ? 'text-green-800' : 'text-red-800'
                }`}>
                  PLC Connection Test {plcTestResult.success ? 'Successful' : 'Failed'}
                </h4>
                <div className="mt-2 text-sm">
                  <p className={plcTestResult.success ? 'text-green-700' : 'text-red-700'}>
                    <strong>IP:</strong> {plcTestResult.config?.ip} | 
                    <strong> Rack:</strong> {plcTestResult.config?.rack} | 
                    <strong> Slot:</strong> {plcTestResult.config?.slot}
                  </p>
                  {plcTestResult.connectionTest && (
                    <p className={plcTestResult.success ? 'text-green-700' : 'text-red-700'}>
                      <strong>Connection:</strong> {plcTestResult.connectionTest.message || plcTestResult.connectionTest.error}
                    </p>
                  )}
                  {plcTestResult.healthCheck && (
                    <p className={plcTestResult.success ? 'text-green-700' : 'text-red-700'}>
                      <strong>Health:</strong> {plcTestResult.healthCheck.status} 
                      {plcTestResult.healthCheck.error && ` - ${plcTestResult.healthCheck.error}`}
                    </p>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* System Settings */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">System Configuration</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="label">Poll Interval (ms)</label>
            <input
              type="number"
              value={settings.system.pollInterval}
              onChange={(e) => handleSettingChange('system', 'pollInterval', parseInt(e.target.value))}
              className="input"
              min="50"
              max="1000"
            />
            <p className="text-xs text-gray-500 mt-1">
              Lower values = more responsive, higher CPU usage
            </p>
          </div>
          
          <div>
            <label className="label">Log Level</label>
            <select
              value={settings.system.logLevel}
              onChange={(e) => handleSettingChange('system', 'logLevel', e.target.value)}
              className="input"
            >
              <option value="error">Error</option>
              <option value="warn">Warning</option>
              <option value="info">Info</option>
              <option value="debug">Debug</option>
            </select>
          </div>
        </div>
      </div>

      {/* Safety Notice */}
      <div className="card bg-yellow-50 border-yellow-200">
        <div className="flex items-start space-x-2">
          <AlertCircle className="h-5 w-5 text-yellow-600 mt-0.5" />
          <div>
            <h4 className="text-sm font-medium text-yellow-800">Safety Notice</h4>
            <p className="text-sm text-yellow-700 mt-1">
              Changing these settings may affect system operation. Ensure you understand 
              the implications before saving. Some changes may require a system restart.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
