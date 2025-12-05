#!/bin/bash

# Script to properly configure network for 192.168.7.5
# Handles different network managers

echo "=========================================="
echo "Fixing Network Configuration for 192.168.7.5"
echo "=========================================="

# Check which network manager is being used
echo "Checking network manager..."
if systemctl is-active --quiet NetworkManager; then
    NETWORK_MANAGER="NetworkManager"
    echo "Detected: NetworkManager"
elif systemctl is-active --quiet systemd-networkd; then
    NETWORK_MANAGER="systemd-networkd"
    echo "Detected: systemd-networkd"
elif [ -f /etc/dhcpcd.conf ]; then
    NETWORK_MANAGER="dhcpcd"
    echo "Detected: dhcpcd (config file exists)"
else
    NETWORK_MANAGER="unknown"
    echo "Unknown network manager"
fi

# Fix dhcpcd.conf if it exists
if [ -f /etc/dhcpcd.conf ]; then
    echo ""
    echo "Fixing /etc/dhcpcd.conf..."
    
    # Backup
    sudo cp /etc/dhcpcd.conf /etc/dhcpcd.conf.backup.$(date +%Y%m%d_%H%M%S)
    
    # Remove the malformed line (all on one line)
    sudo sed -i '/# Static IP for PLC subnetinterface eth0static ip_address=192.168.7.5\/24/d' /etc/dhcpcd.conf
    
    # Remove any existing eth0 static config
    sudo sed -i '/^interface eth0$/,/^$/d' /etc/dhcpcd.conf
    
    # Add properly formatted configuration
    echo "" | sudo tee -a /etc/dhcpcd.conf
    echo "# Static IP for PLC subnet" | sudo tee -a /etc/dhcpcd.conf
    echo "interface eth0" | sudo tee -a /etc/dhcpcd.conf
    echo "static ip_address=192.168.7.5/24" | sudo tee -a /etc/dhcpcd.conf
    
    echo "✓ Fixed dhcpcd.conf"
fi

# Configure using systemd-networkd
if [ "$NETWORK_MANAGER" = "systemd-networkd" ] || [ ! -z "$(which networkctl)" ]; then
    echo ""
    echo "Configuring via systemd-networkd..."
    
    sudo mkdir -p /etc/systemd/network
    
    # Create or update eth0 network file
    sudo tee /etc/systemd/network/eth0.network > /dev/null <<EOF
[Match]
Name=eth0

[Network]
Address=192.168.7.5/24
EOF
    
    echo "✓ Created /etc/systemd/network/eth0.network"
    
    # Restart systemd-networkd
    echo "Restarting systemd-networkd..."
    sudo systemctl restart systemd-networkd
    sleep 2
fi

# Configure using NetworkManager (if available)
if [ "$NETWORK_MANAGER" = "NetworkManager" ]; then
    echo ""
    echo "Configuring via NetworkManager..."
    
    # Use nmcli to set static IP
    sudo nmcli connection modify "Wired connection 1" ipv4.addresses 192.168.7.5/24 ipv4.method manual 2>/dev/null || \
    sudo nmcli connection modify eth0 ipv4.addresses 192.168.7.5/24 ipv4.method manual 2>/dev/null || \
    echo "Note: NetworkManager configuration may need manual setup"
    
    sudo systemctl restart NetworkManager
    sleep 2
fi

# Try to apply immediately using ip command
echo ""
echo "Applying IP configuration immediately..."
sudo ip addr flush dev eth0 2>/dev/null || true
sudo ip addr add 192.168.7.5/24 dev eth0 2>/dev/null || true
sudo ip link set eth0 up 2>/dev/null || true

sleep 2

# Verify
echo ""
echo "=========================================="
echo "Verification"
echo "=========================================="
echo ""
echo "Current IP addresses:"
hostname -I

echo ""
echo "eth0 configuration:"
ip addr show eth0 | grep "inet " || echo "No IP on eth0"

echo ""
echo "Testing PLC connectivity..."
if ping -c 2 -W 2 192.168.7.2 > /dev/null 2>&1; then
    echo "✓ SUCCESS: Can reach PLC at 192.168.7.2"
else
    echo "✗ Cannot reach PLC. Check:"
    echo "  1. Ethernet cable connected to PLC network"
    echo "  2. PLC is powered on"
    echo "  3. PLC IP is 192.168.7.2"
    echo ""
    echo "You may need to reboot: sudo reboot"
fi

echo ""
echo "=========================================="
echo "Done!"
echo "=========================================="

