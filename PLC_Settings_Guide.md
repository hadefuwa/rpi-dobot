# PLC Settings Guide

## How to Change PLC IP Address and Test Connection

### 1. Access the Settings Page
- Open your web application
- Navigate to the **Settings** page (usually in the sidebar or main menu)
- You'll see a "PLC Configuration" section

### 2. Change PLC Settings
In the PLC Configuration section, you can modify:
- **IP Address**: Enter your PLC's IP address (e.g., `192.168.0.10`)
- **Rack**: Usually `0` for S7-1200 (default)
- **Slot**: Usually `1` for S7-1200 (default)

### 3. Test the Connection
- Click the **"Test Connection"** button next to the PLC Configuration heading
- The system will attempt to connect to your PLC with the current settings
- You'll see a detailed test result showing:
  - Connection status (Success/Failed)
  - IP, Rack, and Slot being tested
  - Connection test details
  - Health check results

### 4. Save Settings
- After testing and confirming the connection works, click **"Save"**
- The settings will be applied to your system
- You may need to restart the application for some changes to take effect

## Troubleshooting Common Issues

### If Test Connection Fails:

1. **Check PLC IP Address**
   - Verify the IP address is correct
   - Ensure the PLC is on the same network as your Raspberry Pi
   - Test with: `ping YOUR_PLC_IP`

2. **Check PLC Configuration**
   - In TIA Portal, ensure "Permit access with PUT/GET communication from remote partner" is enabled
   - Disable "Optimized block access" for any DBs you're accessing
   - Ensure the PLC is in RUN mode

3. **Check Network Connectivity**
   - Test basic connectivity: `ping YOUR_PLC_IP`
   - Test S7Comm port: `telnet YOUR_PLC_IP 102`
   - Check firewall settings

4. **Check Rack/Slot Values**
   - For S7-1200: Rack=0, Slot=1 (default)
   - For S7-1500: Rack=0, Slot=1 or 2
   - For S7-300: Rack=0, Slot=2

### Common Error Messages and Solutions:

- **"Connection timeout"**: PLC not reachable or wrong IP
- **"Access denied"**: PUT/GET communication not enabled on PLC
- **"DB not accessible"**: Optimized block access enabled on PLC
- **"Connection refused"**: PLC not in RUN mode or wrong rack/slot

## API Endpoints for Advanced Users

You can also test the PLC connection directly via API:

```bash
# Test current PLC connection
curl http://localhost:8080/api/plc/test

# Test specific PLC settings
curl -X POST http://localhost:8080/api/settings/test-plc \
  -H "Content-Type: application/json" \
  -d '{"ip":"192.168.0.10","rack":0,"slot":1}'

# Get current settings
curl http://localhost:8080/api/settings

# Save new settings
curl -X POST http://localhost:8080/api/settings \
  -H "Content-Type: application/json" \
  -d '{"plc":{"ip":"192.168.0.10","rack":0,"slot":1}}'
```

## Next Steps

After successfully configuring your PLC connection:
1. Go to the PLC Monitor page to see real-time data
2. Check the Dashboard for system status
3. Test control operations if needed

If you continue to have issues, check the application logs:
```bash
pm2 logs dobot-gateway
# or
tail -f /var/log/dobot-gateway/combined.log
```
