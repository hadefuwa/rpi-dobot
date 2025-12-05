# Manual IP Configuration Guide - 192.168.7.5

If the automated script doesn't work, here's how to manually configure the Pi IP address.

## Method 1: Using dhcpcd.conf (Recommended for Raspberry Pi)

### Step 1: Edit dhcpcd.conf

```bash
sudo nano /etc/dhcpcd.conf
```

### Step 2: Add Configuration

Scroll to the bottom and add:

```bash
# Static IP for PLC subnet
interface eth0
static ip_address=192.168.7.5/24
```

**Note:** Replace `eth0` with `eth1` if you're using a USB Ethernet adapter.

### Step 3: Save and Exit

- Press `Ctrl+X`
- Press `Y` to confirm
- Press `Enter` to save

### Step 4: Restart Network Service

```bash
sudo systemctl restart dhcpcd
```

### Step 5: Verify

```bash
hostname -I
```

You should see `192.168.7.5` in the output.

### Step 6: Test PLC Connection

```bash
ping 192.168.7.2
```

If ping works, the configuration is successful!

---

## Method 2: Using ip command (Temporary - until reboot)

This sets the IP immediately but won't persist after reboot:

```bash
# Remove current IP
sudo ip addr flush dev eth0

# Add new IP
sudo ip addr add 192.168.7.5/24 dev eth0

# Bring interface up
sudo ip link set eth0 up

# Verify
ip addr show eth0
```

---

## Method 3: Using netplan (if using Ubuntu/Debian with netplan)

```bash
sudo nano /etc/netplan/50-cloud-init.yaml
```

Add or modify:

```yaml
network:
  version: 2
  ethernets:
    eth0:
      addresses:
        - 192.168.7.5/24
```

Then apply:

```bash
sudo netplan apply
```

---

## Troubleshooting

### If IP doesn't change:

1. **Check which interface is active:**
   ```bash
   ip addr show
   ```

2. **Check dhcpcd status:**
   ```bash
   sudo systemctl status dhcpcd
   ```

3. **Check for conflicts:**
   ```bash
   sudo journalctl -u dhcpcd -n 50
   ```

4. **Try rebooting:**
   ```bash
   sudo reboot
   ```

### If you lose SSH connection:

1. Connect via physical console (HDMI + keyboard)
2. Or restore backup:
   ```bash
   sudo cp /etc/dhcpcd.conf.backup.* /etc/dhcpcd.conf
   sudo systemctl restart dhcpcd
   ```

### Verify Configuration:

```bash
# Check IP
hostname -I

# Check routing
ip route show

# Test PLC
ping -c 3 192.168.7.2
```

---

## Reverting Changes

To go back to DHCP (automatic IP):

```bash
# Remove static IP lines from dhcpcd.conf
sudo nano /etc/dhcpcd.conf
# Delete or comment out the interface eth0 section

# Restart service
sudo systemctl restart dhcpcd
```

Or restore from backup:

```bash
sudo cp /etc/dhcpcd.conf.backup.* /etc/dhcpcd.conf
sudo systemctl restart dhcpcd
```

