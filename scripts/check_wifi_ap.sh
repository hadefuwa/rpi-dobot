#!/bin/bash

echo "=========================================="
echo "WiFi Access Point Diagnostic Tool"
echo "=========================================="
echo ""

echo "1. Checking hostapd service status..."
sudo systemctl status hostapd --no-pager -l
echo ""

echo "2. Checking dnsmasq service status..."
sudo systemctl status dnsmasq --no-pager -l
echo ""

echo "3. Checking wlan0 interface..."
ip addr show wlan0
echo ""

echo "4. Checking if hostapd config exists..."
if [ -f /etc/hostapd/hostapd.conf ]; then
    echo "✅ Config file exists"
    echo "First few lines:"
    head -10 /etc/hostapd/hostapd.conf
else
    echo "❌ Config file NOT found!"
fi
echo ""

echo "5. Checking /etc/default/hostapd..."
if grep -q "DAEMON_CONF" /etc/default/hostapd; then
    echo "✅ DAEMON_CONF is set:"
    grep DAEMON_CONF /etc/default/hostapd
else
    echo "❌ DAEMON_CONF not configured!"
fi
echo ""

echo "6. Checking dnsmasq config..."
if grep -q "interface=wlan0" /etc/dnsmasq.conf; then
    echo "✅ dnsmasq configured for wlan0"
    grep -A 1 "interface=wlan0" /etc/dnsmasq.conf
else
    echo "❌ dnsmasq not configured for wlan0!"
fi
echo ""

echo "7. Checking dhcpcd.conf for static IP..."
if grep -q "interface wlan0" /etc/dhcpcd.conf; then
    echo "✅ Static IP configured:"
    grep -A 2 "interface wlan0" /etc/dhcpcd.conf
else
    echo "❌ Static IP not configured!"
fi
echo ""

echo "8. Checking for connected devices..."
if [ -f /var/lib/misc/dnsmasq.leases ]; then
    echo "Connected devices:"
    sudo cat /var/lib/misc/dnsmasq.leases
else
    echo "No leases file found (no devices connected yet)"
fi
echo ""

echo "9. Checking if hostapd process is running..."
if pgrep -x hostapd > /dev/null; then
    echo "✅ hostapd process is running"
    ps aux | grep hostapd | grep -v grep
else
    echo "❌ hostapd process is NOT running!"
fi
echo ""

echo "10. Checking if dnsmasq process is running..."
if pgrep -x dnsmasq > /dev/null; then
    echo "✅ dnsmasq process is running"
    ps aux | grep dnsmasq | grep -v grep
else
    echo "❌ dnsmasq process is NOT running!"
fi
echo ""

echo "=========================================="
echo "Diagnostic Complete"
echo "=========================================="

