# Quick Start - Run on Raspberry Pi

## Step 1: Pull from GitHub

```bash
ssh pi@rpi
cd ~/rpi-dobot
git pull origin main
```

## Step 2: Download DobotDemoV2.0

You need to get the official Dobot API files. Choose one option:

### Option A: Download on Windows and Transfer
1. Download from: https://www.dobot.cc/downloadcenter/dobot-magician.html
2. Look for "DobotDemoV2.0" or "Dobot Demo for Python"
3. Transfer to Pi:
   ```bash
   # From Windows
   sshpass -p "1" scp DobotDemoV2.0.zip pi@rpi:~/
   ```

### Option B: Download Directly on Pi
```bash
# On Pi
cd ~
# You'll need to manually download from the Dobot website
# Or use wget if you have a direct link
```

### Option C: Skip Download (Manual Setup)
If you can't download it, I can help you create the files manually.

## Step 3: Run Setup Script

```bash
cd ~/rpi-dobot
chmod +x setup_official_dobot_api.sh
bash setup_official_dobot_api.sh
```

**What to expect:**
- Script will extract DobotDemoV2.0.zip
- Copy DobotDLLType.py and DobotDll.so to backend
- Test that DLL loads correctly
- You should see: "✅ Official Dobot API is ready to use!"

## Step 4: Run Migration Script

```bash
chmod +x migrate_to_official_api.sh
bash migrate_to_official_api.sh
```

**What happens:**
- Backs up old dobot_client.py
- Installs new official API version
- Removes pydobot from requirements.txt
- Runs connection test automatically

## Step 5: Test Movement (THE IMPORTANT ONE!)

⚠️ Make sure robot has clear space to move!

```bash
python3 test_official_api_connection.py
python3 test_official_api_movement.py
```

**Success looks like:**
```
✅ Robot MOVED! Total position change: 45.23mm
🎉 MOVEMENT TEST PASSED!
```

## Step 6: Test Web App

```bash
cd ~/rpi-dobot/pwa-dobot-plc/backend
python3 app.py
```

Open browser to: http://rpi:8080

---

## If You Get Stuck

### Problem: Can't download DobotDemoV2.0.zip

Let me know and I can help you get the files another way.

### Problem: Setup script fails

Check what error it shows and let me know.

### Problem: Connection test fails

```bash
# Check USB
ls -la /dev/ttyACM* /dev/ttyUSB*

# Check permissions
sudo usermod -a -G dialout $USER
# Then logout and login again
```

### Problem: Movement test fails

Send me the full output and I'll help debug.

---

## Rollback (if needed)

```bash
cd ~/rpi-dobot/pwa-dobot-plc/backend
cp dobot_client_pydobot_backup.py dobot_client.py
```

---

**Ready? Start with Step 1!** 🚀
