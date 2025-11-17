# WiFi Access Point Setup Guide

This guide will help you set up your Raspberry Pi as a WiFi access point so you can connect your phone to it and access the web server.

## What This Does

After setup, your Raspberry Pi will:
- Create a WiFi network called "DobotPi"
- Allow your phone to connect to it
- Give your phone an IP address automatically
- Let you access the web server from your phone
- Allow SSH access using `pi@rpi` with password `1`

## Quick Setup (Automatic)

1. **Copy the setup script to your Raspberry Pi** (if you haven't already):
   ```bash
   # If you're on your computer, copy the script to your Pi
   # Or if you're already on the Pi, the script should be in:
   cd ~/rpi-dobot/scripts
   ```

2. **Make the script executable**:
   ```bash
   chmod +x setup_wifi_access_point.sh
   ```

3. **Run the setup script**:
   ```bash
   sudo ./setup_wifi_access_point.sh
   ```

4. **Reboot your Raspberry Pi**:
   ```bash
   sudo reboot
   ```

5. **After reboot, connect your phone**:
   - Go to WiFi settings on your phone
   - Look for network "SmartFactory"
   - Enter password: `matrix123`
   - Open browser and go to: `http://192.168.4.1:8080`

## Manual Setup (Step by Step)

If you prefer to do it manually or the script doesn't work:

### Step 1: Install Required Packages

```bash
sudo apt-get update
sudo apt-get install -y hostapd dnsmasq
```

### Step 2: Stop Services

```bash
sudo systemctl stop hostapd
sudo systemctl stop dnsmasq
```

### Step 3: Configure Static IP Address

Edit the file `/etc/dhcpcd.conf`:
```bash
sudo nano /etc/dhcpcd.conf
```

Add these lines at the end:
```
interface wlan0
static ip_address=192.168.4.1/24
nohook wpa_supplicant
```

Save with `Ctrl+X`, then `Y`, then `Enter`.

### Step 4: Configure WiFi Access Point

Create/edit the file `/etc/hostapd/hostapd.conf`:
```bash
sudo nano /etc/hostapd/hostapd.conf
```

Add this content:
```
interface=wlan0
driver=nl80211
ssid=SmartFactory
hw_mode=g
channel=6
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=matrix123
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
```

Save with `Ctrl+X`, then `Y`, then `Enter`.

### Step 5: Tell hostapd Where Config File Is

Edit `/etc/default/hostapd`:
```bash
sudo nano /etc/default/hostapd
```

Find the line `#DAEMON_CONF=""` and change it to:
```
DAEMON_CONF="/etc/hostapd/hostapd.conf"
```

Save with `Ctrl+X`, then `Y`, then `Enter`.

### Step 6: Configure DHCP Server

Edit `/etc/dnsmasq.conf`:
```bash
sudo nano /etc/dnsmasq.conf
```

Add these lines at the end:
```
interface=wlan0
dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h
```

Save with `Ctrl+X`, then `Y`, then `Enter`.

### Step 7: Enable SSH

```bash
sudo systemctl enable ssh
sudo systemctl start ssh
```

### Step 8: Set Hostname to 'rpi'

```bash
sudo hostnamectl set-hostname rpi
```

Edit `/etc/hosts`:
```bash
sudo nano /etc/hosts
```

Add this line:
```
127.0.1.1    rpi
```

Save with `Ctrl+X`, then `Y`, then `Enter`.

### Step 9: Set Password for pi User

```bash
echo "pi:1" | sudo chpasswd
```

### Step 10: Start Services

```bash
sudo systemctl unmask hostapd
sudo systemctl enable hostapd
sudo systemctl enable dnsmasq
sudo systemctl start hostapd
sudo systemctl start dnsmasq
```

### Step 11: Reboot

```bash
sudo reboot
```

## After Setup

### Connect Your Phone

1. On your phone, go to WiFi settings
2. Look for network "SmartFactory"
3. Enter password: `matrix123`
4. Connect

### Access the Web Server

Open your phone's browser and go to:
```
http://192.168.4.1:8080
```

### SSH Access

From your computer (if on same network) or from your phone (using an SSH app):
```bash
ssh pi@rpi
# or
ssh pi@192.168.4.1
```

Password: `1`

## Troubleshooting

### WiFi Network Not Showing Up

1. Check if hostapd is running:
   ```bash
   sudo systemctl status hostapd
   ```

2. Check hostapd logs:
   ```bash
   sudo journalctl -u hostapd -n 50
   ```

3. Restart hostapd:
   ```bash
   sudo systemctl restart hostapd
   ```

### Can't Connect to Web Server

1. Make sure your Flask app is running:
   ```bash
   cd ~/rpi-dobot/pwa-dobot-plc/backend
   source venv/bin/activate
   python app.py
   ```

2. Check if port 8080 is accessible:
   ```bash
   sudo netstat -tlnp | grep 8080
   ```

### Can't SSH

1. Check if SSH is running:
   ```bash
   sudo systemctl status ssh
   ```

2. Make sure you're using the correct password: `1`

## Network Information

- **WiFi Network Name**: SmartFactory
- **WiFi Password**: matrix123
- **Pi IP Address**: 192.168.4.1
- **Phone IP Range**: 192.168.4.2 - 192.168.4.20
- **Web Server**: http://192.168.4.1:8080
- **SSH**: pi@rpi (password: 1)

