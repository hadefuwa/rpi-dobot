#!/bin/bash

# Simple script to set up Raspberry Pi as WiFi Access Point
# This will allow your phone to connect to the Pi and access the web server
# SSH will be available at pi@rpi with password: 1

echo "=========================================="
echo "Raspberry Pi WiFi Access Point Setup"
echo "=========================================="
echo ""
echo "This script will:"
echo "1. Install required packages (hostapd, dnsmasq)"
echo "2. Configure WiFi access point"
echo "3. Set up DHCP server"
echo "4. Enable SSH"
echo "5. Configure network settings"
echo ""
echo "Press Enter to continue or Ctrl+C to cancel..."
read

# Step 1: Update system packages
echo ""
echo "Step 1: Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Step 2: Install required packages
echo ""
echo "Step 2: Installing hostapd and dnsmasq..."
sudo apt-get install -y hostapd dnsmasq

# Step 3: Stop services before configuration
echo ""
echo "Step 3: Stopping services..."
sudo systemctl stop hostapd
sudo systemctl stop dnsmasq

# Step 4: Configure static IP for wlan0
echo ""
echo "Step 4: Configuring static IP address..."
sudo cp /etc/dhcpcd.conf /etc/dhcpcd.conf.backup

# Add static IP configuration to dhcpcd.conf
if ! grep -q "interface wlan0" /etc/dhcpcd.conf; then
    echo "" | sudo tee -a /etc/dhcpcd.conf
    echo "# WiFi Access Point Configuration" | sudo tee -a /etc/dhcpcd.conf
    echo "interface wlan0" | sudo tee -a /etc/dhcpcd.conf
    echo "static ip_address=192.168.4.1/24" | sudo tee -a /etc/dhcpcd.conf
    echo "nohook wpa_supplicant" | sudo tee -a /etc/dhcpcd.conf
fi

# Step 5: Configure hostapd (WiFi Access Point)
echo ""
echo "Step 5: Configuring WiFi Access Point..."
sudo tee /etc/hostapd/hostapd.conf > /dev/null <<EOF
# WiFi Access Point Configuration
interface=wlan0
driver=nl80211

# WiFi Network Name (SSID)
ssid=SmartFactory

# WiFi Mode (g = 2.4GHz)
hw_mode=g

# WiFi Channel (use channel 6 for best compatibility)
channel=6

# Enable WiFi Protected Access
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0

# WiFi Security (WPA2)
wpa=2
wpa_passphrase=matrix123
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
EOF

# Tell hostapd where to find the config file
sudo tee /etc/default/hostapd > /dev/null <<EOF
DAEMON_CONF="/etc/hostapd/hostapd.conf"
EOF

# Step 6: Configure dnsmasq (DHCP Server)
echo ""
echo "Step 6: Configuring DHCP server..."
sudo cp /etc/dnsmasq.conf /etc/dnsmasq.conf.backup

sudo tee /etc/dnsmasq.conf > /dev/null <<EOF
# DHCP Server Configuration for WiFi Access Point
interface=wlan0
dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h
EOF

# Step 7: Enable IP forwarding (for internet sharing if needed later)
echo ""
echo "Step 7: Enabling IP forwarding..."
sudo sed -i 's/#net.ipv4.ip_forward=1/net.ipv4.ip_forward=1/' /etc/sysctl.conf
sudo sysctl -p

# Step 8: Enable SSH
echo ""
echo "Step 8: Enabling SSH..."
sudo systemctl enable ssh
sudo systemctl start ssh

# Step 9: Set hostname to 'rpi'
echo ""
echo "Step 9: Setting hostname to 'rpi'..."
sudo hostnamectl set-hostname rpi
if ! grep -q "127.0.1.1.*rpi" /etc/hosts; then
    echo "127.0.1.1    rpi" | sudo tee -a /etc/hosts
fi

# Step 10: Set password for pi user (if not already set)
echo ""
echo "Step 10: Setting password for pi user..."
echo "pi:1" | sudo chpasswd

# Step 11: Start services
echo ""
echo "Step 11: Starting services..."
sudo systemctl unmask hostapd
sudo systemctl enable hostapd
sudo systemctl enable dnsmasq
sudo systemctl start hostapd
sudo systemctl start dnsmasq

# Step 12: Display information
echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "WiFi Network Details:"
echo "  Network Name (SSID): SmartFactory"
echo "  Password: matrix123"
echo "  IP Address: 192.168.4.1"
echo ""
echo "Connection Information:"
echo "  SSH: ssh pi@rpi (or ssh pi@192.168.4.1)"
echo "  Password: 1"
echo "  Web Server: http://192.168.4.1:8080"
echo ""
echo "To connect from your phone:"
echo "  1. Go to WiFi settings"
echo "  2. Look for network 'SmartFactory'"
echo "  3. Enter password: matrix123"
echo "  4. Open browser and go to: http://192.168.4.1:8080"
echo ""
echo "Note: You may need to reboot for all changes to take effect."
echo "      Run: sudo reboot"
echo ""

