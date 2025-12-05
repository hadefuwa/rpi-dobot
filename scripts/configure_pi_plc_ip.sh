#!/bin/bash

# Script to configure Raspberry Pi with static IP 192.168.7.5
# This puts the Pi on the same subnet as the PLC (192.168.7.x)

echo "=========================================="
echo "Configure Pi IP to 192.168.7.5"
echo "=========================================="
echo ""
echo "This will configure the Pi to have IP address 192.168.7.5"
echo "on the PLC subnet (192.168.7.0/24)"
echo ""
echo "WARNING: This will change your network configuration!"
echo "Make sure you have physical access to the Pi in case you lose SSH connection."
echo ""
echo "Press Enter to continue or Ctrl+C to cancel..."
read

# Detect which interface to configure
echo ""
echo "Detecting network interfaces..."
INTERFACES=$(ip link show | grep -E "^[0-9]+:" | awk -F: '{print $2}' | tr -d ' ' | grep -v lo)

echo "Available interfaces:"
for iface in $INTERFACES; do
    IP=$(ip addr show $iface 2>/dev/null | grep "inet " | awk '{print $2}' | cut -d/ -f1)
    if [ ! -z "$IP" ]; then
        echo "  $iface - Current IP: $IP"
    else
        echo "  $iface - No IP assigned"
    fi
done

echo ""
echo "Which interface do you want to configure?"
echo "Options:"
echo "  1. eth0 (Ethernet port)"
echo "  2. wlan0 (WiFi)"
echo "  3. eth1 (Second Ethernet/USB adapter)"
echo "  4. Custom interface name"
echo ""
read -p "Enter choice (1-4): " CHOICE

case $CHOICE in
    1)
        INTERFACE_NAME="eth0"
        ;;
    2)
        INTERFACE_NAME="wlan0"
        echo "WARNING: Configuring WiFi with static IP may disconnect you from current network!"
        read -p "Are you sure? (y/n): " CONFIRM
        if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
            echo "Cancelled."
            exit 1
        fi
        ;;
    3)
        INTERFACE_NAME="eth1"
        ;;
    4)
        read -p "Enter interface name: " INTERFACE_NAME
        ;;
    *)
        echo "Invalid choice. Using eth0 as default."
        INTERFACE_NAME="eth0"
        ;;
esac

# Check if interface exists
if ! ip link show $INTERFACE_NAME > /dev/null 2>&1; then
    echo "Error: Interface $INTERFACE_NAME does not exist!"
    exit 1
fi

echo ""
echo "Configuring $INTERFACE_NAME with IP 192.168.7.5/24..."

# Backup current configuration
echo "Backing up current network configuration..."
sudo cp /etc/dhcpcd.conf /etc/dhcpcd.conf.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null || true

# Configure using dhcpcd (Raspberry Pi default)
if [ -f /etc/dhcpcd.conf ]; then
    echo "Configuring via dhcpcd.conf..."
    
    # Remove any existing configuration for this interface
    sudo sed -i "/^interface $INTERFACE_NAME$/,/^$/d" /etc/dhcpcd.conf
    
    # Add new configuration
    echo "" | sudo tee -a /etc/dhcpcd.conf
    echo "# Static IP configuration for PLC subnet" | sudo tee -a /etc/dhcpcd.conf
    echo "interface $INTERFACE_NAME" | sudo tee -a /etc/dhcpcd.conf
    echo "static ip_address=192.168.7.5/24" | sudo tee -a /etc/dhcpcd.conf
    
    # If it's WiFi, disable wpa_supplicant
    if [ "$INTERFACE_NAME" = "wlan0" ]; then
        echo "nohook wpa_supplicant" | sudo tee -a /etc/dhcpcd.conf
    fi
    
    echo "Configuration added to /etc/dhcpcd.conf"
fi

# Also configure using systemd-networkd (if available)
if [ -d /etc/systemd/network ]; then
    echo "Also configuring via systemd-networkd..."
    sudo tee /etc/systemd/network/${INTERFACE_NAME}.network > /dev/null <<EOF
[Match]
Name=$INTERFACE_NAME

[Network]
Address=192.168.7.5/24
EOF
    echo "Configuration added to /etc/systemd/network/${INTERFACE_NAME}.network"
fi

# Apply configuration immediately (without reboot)
echo ""
echo "Applying network configuration..."
echo "This may temporarily disconnect your network connection."

# Try to apply using ip command
sudo ip addr flush dev $INTERFACE_NAME 2>/dev/null || true
sudo ip addr add 192.168.7.5/24 dev $INTERFACE_NAME 2>/dev/null || true

# Restart networking services
if systemctl is-active --quiet dhcpcd; then
    echo "Restarting dhcpcd service..."
    sudo systemctl restart dhcpcd
fi

if systemctl is-active --quiet systemd-networkd; then
    echo "Restarting systemd-networkd service..."
    sudo systemctl restart systemd-networkd
fi

# Wait a moment for network to settle
sleep 3

# Verify configuration
echo ""
echo "=========================================="
echo "Verification"
echo "=========================================="
echo ""
echo "Current IP configuration for $INTERFACE_NAME:"
ip addr show $INTERFACE_NAME | grep "inet " || echo "No IP assigned yet"

echo ""
echo "Testing connectivity to PLC (192.168.7.2)..."
if ping -c 2 -W 2 192.168.7.2 > /dev/null 2>&1; then
    echo "✓ SUCCESS: Can reach PLC at 192.168.7.2"
    echo ""
    echo "Testing S7Comm port (102)..."
    if timeout 2 bash -c "echo > /dev/tcp/192.168.7.2/102" 2>/dev/null; then
        echo "✓ SUCCESS: S7Comm port (102) is accessible"
        echo ""
        echo "=========================================="
        echo "✓ Configuration Complete!"
        echo "=========================================="
        echo ""
        echo "Your Pi is now configured with IP: 192.168.7.5"
        echo "PLC is at: 192.168.7.2"
        echo ""
        echo "You may need to restart the application:"
        echo "  pm2 restart pwa-dobot-plc"
    else
        echo "⚠ WARNING: Cannot reach port 102 (S7Comm)"
        echo "   PLC may not be configured for remote access."
        echo "   Check PLC settings in TIA Portal."
    fi
else
    echo "✗ WARNING: Cannot reach PLC at 192.168.7.2"
    echo ""
    echo "Troubleshooting:"
    echo "1. Check network cable is connected"
    echo "2. Verify PLC is powered on"
    echo "3. Check PLC IP is actually 192.168.7.2"
    echo "4. You may need to reboot: sudo reboot"
fi

echo ""
echo "Current routing table:"
ip route show

echo ""
echo "=========================================="
echo "Configuration Summary"
echo "=========================================="
echo "Interface: $INTERFACE_NAME"
echo "IP Address: 192.168.7.5/24"
echo "PLC IP: 192.168.7.2"
echo ""
echo "If you need to revert changes, restore from backup:"
echo "  sudo cp /etc/dhcpcd.conf.backup.* /etc/dhcpcd.conf"
echo "  sudo systemctl restart dhcpcd"
echo ""

