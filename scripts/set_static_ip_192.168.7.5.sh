#!/bin/bash

# Simple script to set Pi IP to 192.168.7.5
# This is a direct approach using dhcpcd

echo "=========================================="
echo "Setting Pi IP to 192.168.7.5"
echo "=========================================="

# Determine which interface to use
echo "Checking network interfaces..."
ETH0_IP=$(ip addr show eth0 2>/dev/null | grep "inet " | awk '{print $2}' | cut -d/ -f1)
ETH1_IP=$(ip addr show eth1 2>/dev/null | grep "inet " | awk '{print $2}' | cut -d/ -f1)

echo "eth0 IP: ${ETH0_IP:-not configured}"
echo "eth1 IP: ${ETH1_IP:-not configured}"

# Ask which interface
echo ""
read -p "Which interface to configure? (eth0/eth1) [default: eth0]: " IFACE
IFACE=${IFACE:-eth0}

if ! ip link show $IFACE > /dev/null 2>&1; then
    echo "Error: Interface $IFACE does not exist!"
    exit 1
fi

echo ""
echo "Configuring $IFACE with IP 192.168.7.5/24..."

# Backup dhcpcd.conf
sudo cp /etc/dhcpcd.conf /etc/dhcpcd.conf.backup.$(date +%Y%m%d_%H%M%S)

# Remove any existing configuration for this interface
sudo sed -i "/^interface $IFACE$/,/^$/d" /etc/dhcpcd.conf

# Add static IP configuration
echo "" | sudo tee -a /etc/dhcpcd.conf
echo "# Static IP for PLC subnet - added $(date)" | sudo tee -a /etc/dhcpcd.conf
echo "interface $IFACE" | sudo tee -a /etc/dhcpcd.conf
echo "static ip_address=192.168.7.5/24" | sudo tee -a /etc/dhcpcd.conf

echo ""
echo "Configuration added to /etc/dhcpcd.conf"
echo ""
echo "Restarting dhcpcd service..."
sudo systemctl restart dhcpcd

echo ""
echo "Waiting 5 seconds for network to configure..."
sleep 5

# Check new IP
NEW_IP=$(ip addr show $IFACE 2>/dev/null | grep "inet " | awk '{print $2}' | cut -d/ -f1)
echo ""
echo "Current IP on $IFACE: ${NEW_IP:-not configured}"

if [ "$NEW_IP" = "192.168.7.5" ]; then
    echo "✓ SUCCESS: IP configured correctly!"
    echo ""
    echo "Testing PLC connectivity..."
    if ping -c 2 -W 2 192.168.7.2 > /dev/null 2>&1; then
        echo "✓ SUCCESS: Can ping PLC at 192.168.7.2"
    else
        echo "⚠ WARNING: Cannot ping PLC. Check cable and PLC power."
    fi
else
    echo "⚠ Configuration may need a reboot to take effect."
    echo "  Run: sudo reboot"
fi

echo ""
echo "To revert, restore backup:"
echo "  sudo cp /etc/dhcpcd.conf.backup.* /etc/dhcpcd.conf"
echo "  sudo systemctl restart dhcpcd"

