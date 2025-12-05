#!/bin/bash

# Script to configure Raspberry Pi network for PLC communication
# This sets up routing to reach PLC on 192.168.7.x subnet

echo "=========================================="
echo "PLC Network Configuration Setup"
echo "=========================================="
echo ""
echo "This script will configure network routing to reach PLC at 192.168.7.2"
echo "Your Pi is currently on: 192.168.1.x"
echo "PLC is on: 192.168.7.2"
echo ""
echo "Press Enter to continue or Ctrl+C to cancel..."
read

# Method 1: Add static route (if you have a gateway/router that can reach 192.168.7.0/24)
echo ""
echo "Method 1: Adding static route to 192.168.7.0/24 network"
echo "This assumes you have a gateway/router that can reach the PLC subnet"
echo ""

# Get default gateway
DEFAULT_GATEWAY=$(ip route | grep default | awk '{print $3}' | head -n 1)
echo "Detected default gateway: $DEFAULT_GATEWAY"

if [ -z "$DEFAULT_GATEWAY" ]; then
    echo "Warning: No default gateway found. You may need to specify a gateway manually."
    read -p "Enter gateway IP for 192.168.7.0/24 network (or press Enter to skip): " MANUAL_GATEWAY
    if [ ! -z "$MANUAL_GATEWAY" ]; then
        DEFAULT_GATEWAY=$MANUAL_GATEWAY
    fi
fi

if [ ! -z "$DEFAULT_GATEWAY" ]; then
    # Add static route
    echo "Adding static route: 192.168.7.0/24 via $DEFAULT_GATEWAY"
    sudo ip route add 192.168.7.0/24 via $DEFAULT_GATEWAY 2>/dev/null || echo "Route may already exist"
    
    # Make route persistent
    if [ ! -f /etc/systemd/network/plc-route.network ]; then
        echo "Creating persistent route configuration..."
        sudo mkdir -p /etc/systemd/network
        sudo tee /etc/systemd/network/plc-route.network > /dev/null <<EOF
[Route]
Destination=192.168.7.0/24
Gateway=$DEFAULT_GATEWAY
EOF
        echo "Persistent route configuration created"
    fi
fi

# Method 2: Check for second network interface (USB Ethernet adapter)
echo ""
echo "Method 2: Checking for additional network interfaces..."
INTERFACES=$(ip link show | grep -E "^[0-9]+:" | awk -F: '{print $2}' | tr -d ' ' | grep -v lo)

for iface in $INTERFACES; do
    IP=$(ip addr show $iface 2>/dev/null | grep "inet " | awk '{print $2}' | cut -d/ -f1)
    if [ ! -z "$IP" ]; then
        echo "Found interface: $iface with IP: $IP"
    fi
done

echo ""
echo "If you have a second Ethernet interface (USB-to-Ethernet adapter) connected to the PLC network:"
echo "You can configure it with a static IP on 192.168.7.x subnet"
echo ""
read -p "Do you want to configure a second interface for direct PLC connection? (y/n): " CONFIGURE_INTERFACE

if [ "$CONFIGURE_INTERFACE" = "y" ] || [ "$CONFIGURE_INTERFACE" = "Y" ]; then
    echo ""
    echo "Available interfaces:"
    ip link show | grep -E "^[0-9]+:" | awk -F: '{print $2}' | tr -d ' ' | grep -v lo
    echo ""
    read -p "Enter interface name (e.g., eth1, enp0s3): " INTERFACE_NAME
    
    if [ ! -z "$INTERFACE_NAME" ]; then
        read -p "Enter IP address for this interface (e.g., 192.168.7.10): " STATIC_IP
        
        if [ ! -z "$STATIC_IP" ]; then
            echo "Configuring $INTERFACE_NAME with IP $STATIC_IP..."
            
            # Create network configuration
            sudo tee /etc/systemd/network/${INTERFACE_NAME}.network > /dev/null <<EOF
[Match]
Name=$INTERFACE_NAME

[Network]
Address=$STATIC_IP/24
EOF
            
            echo "Configuration created. You may need to restart networking:"
            echo "  sudo systemctl restart systemd-networkd"
            echo "  or"
            echo "  sudo ifdown $INTERFACE_NAME && sudo ifup $INTERFACE_NAME"
        fi
    fi
fi

# Test connectivity
echo ""
echo "=========================================="
echo "Testing PLC Connectivity"
echo "=========================================="
echo ""

echo "Testing ping to 192.168.7.2..."
if ping -c 2 -W 2 192.168.7.2 > /dev/null 2>&1; then
    echo "✓ SUCCESS: Can reach PLC at 192.168.7.2"
    echo ""
    echo "Testing S7Comm port (102)..."
    if timeout 2 bash -c "echo > /dev/tcp/192.168.7.2/102" 2>/dev/null; then
        echo "✓ SUCCESS: S7Comm port (102) is accessible"
    else
        echo "⚠ WARNING: Cannot reach port 102 (S7Comm). PLC may not be configured for remote access."
        echo "   Check PLC settings in TIA Portal:"
        echo "   - Enable 'Permit access with PUT/GET communication from remote partner'"
    fi
else
    echo "✗ FAILED: Cannot reach PLC at 192.168.7.2"
    echo ""
    echo "Troubleshooting steps:"
    echo "1. Check if PLC is powered on and connected"
    echo "2. Verify PLC IP address is 192.168.7.2"
    echo "3. Check network cable connections"
    echo "4. Verify routing: ip route show"
    echo "5. Try manual route: sudo ip route add 192.168.7.0/24 via YOUR_GATEWAY_IP"
fi

echo ""
echo "Current routing table:"
ip route show | grep -E "192.168.7|default"

echo ""
echo "=========================================="
echo "Configuration complete!"
echo "=========================================="
echo ""
echo "If routing was configured, you may need to:"
echo "  sudo systemctl restart systemd-networkd"
echo "  or reboot the Pi"
echo ""

