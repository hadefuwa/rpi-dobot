#!/bin/bash

echo "=========================================="
echo "WiFi Access Point Fix Script"
echo "=========================================="
echo ""

echo "Step 1: Stopping services..."
sudo systemctl stop hostapd
sudo systemctl stop dnsmasq
sleep 2

echo ""
echo "Step 2: Unmasking hostapd..."
sudo systemctl unmask hostapd

echo ""
echo "Step 3: Checking configuration files..."

if [ ! -f /etc/hostapd/hostapd.conf ]; then
    echo "❌ hostapd.conf not found! Run setup script first."
    exit 1
fi

if ! grep -q "DAEMON_CONF" /etc/default/hostapd; then
    echo "⚠️  Setting DAEMON_CONF..."
    echo 'DAEMON_CONF="/etc/hostapd/hostapd.conf"' | sudo tee -a /etc/default/hostapd
fi

echo ""
echo "Step 4: Restarting network interface..."
sudo ip link set wlan0 down
sleep 1
sudo ip link set wlan0 up
sleep 2

echo ""
echo "Step 5: Starting services..."
sudo systemctl start dnsmasq
sleep 2
sudo systemctl start hostapd
sleep 3

echo ""
echo "Step 6: Checking service status..."
echo ""
echo "hostapd status:"
sudo systemctl status hostapd --no-pager -l | head -10
echo ""
echo "dnsmasq status:"
sudo systemctl status dnsmasq --no-pager -l | head -10
echo ""

echo "Step 7: Checking wlan0 IP address..."
ip addr show wlan0 | grep "inet "

echo ""
echo "=========================================="
echo "Fix Complete!"
echo "=========================================="
echo ""
echo "If WiFi still doesn't work, try:"
echo "  1. Run: sudo reboot"
echo "  2. Or check logs: sudo journalctl -u hostapd -n 50"

