#!/bin/bash
# Complete Deployment Script for Official Dobot API Migration
# Run this from your Windows PC to deploy everything to the Raspberry Pi

set -e

echo "=================================================="
echo "Official Dobot API - Complete Deployment"
echo "=================================================="
echo ""

# Configuration
PI_USER="pi"
PI_HOST="rpi"
PI_PASS="1"
PROJECT_DIR="rpi-dobot"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}This script will:${NC}"
echo "1. Transfer all migration files to Raspberry Pi"
echo "2. Run setup script to install official Dobot API"
echo "3. Run migration script to switch from pydobot"
echo "4. Run tests to verify everything works"
echo ""
read -p "Press Enter to continue or Ctrl+C to abort..."
echo ""

# Step 1: Transfer files
echo -e "${YELLOW}Step 1: Transferring files to Raspberry Pi...${NC}"

sshpass -p "$PI_PASS" scp setup_official_dobot_api.sh ${PI_USER}@${PI_HOST}:~/${PROJECT_DIR}/ || exit 1
sshpass -p "$PI_PASS" scp migrate_to_official_api.sh ${PI_USER}@${PI_HOST}:~/${PROJECT_DIR}/ || exit 1
sshpass -p "$PI_PASS" scp test_official_api_connection.py ${PI_USER}@${PI_HOST}:~/${PROJECT_DIR}/ || exit 1
sshpass -p "$PI_PASS" scp test_official_api_movement.py ${PI_USER}@${PI_HOST}:~/${PROJECT_DIR}/ || exit 1
sshpass -p "$PI_PASS" scp test_official_api_peripherals.py ${PI_USER}@${PI_HOST}:~/${PROJECT_DIR}/ || exit 1
sshpass -p "$PI_PASS" scp pwa-dobot-plc/backend/dobot_client_official.py ${PI_USER}@${PI_HOST}:~/${PROJECT_DIR}/pwa-dobot-plc/backend/ || exit 1
sshpass -p "$PI_PASS" scp pwa-dobot-plc/backend/requirements_official_api.txt ${PI_USER}@${PI_HOST}:~/${PROJECT_DIR}/pwa-dobot-plc/backend/ || exit 1

echo -e "${GREEN}✅ Files transferred${NC}"
echo ""

# Step 2: Check for DobotDemoV2.0.zip
echo -e "${YELLOW}Step 2: Checking for DobotDemoV2.0.zip...${NC}"
echo ""
echo "You need to download DobotDemoV2.0.zip from:"
echo "https://www.dobot.cc/downloadcenter/dobot-magician.html"
echo ""
echo "Options:"
echo "A) I already have it on the Pi"
echo "B) I need to transfer it from Windows"
echo "C) I'll download it directly on the Pi"
echo ""
read -p "Choose option (A/B/C): " choice

case $choice in
    [Bb])
        echo ""
        read -p "Enter path to DobotDemoV2.0.zip on Windows: " zip_path
        if [ -f "$zip_path" ]; then
            echo "Transferring DobotDemoV2.0.zip..."
            sshpass -p "$PI_PASS" scp "$zip_path" ${PI_USER}@${PI_HOST}:~/ || exit 1
            echo -e "${GREEN}✅ File transferred${NC}"
        else
            echo -e "${RED}❌ File not found: $zip_path${NC}"
            exit 1
        fi
        ;;
    [Aa])
        echo -e "${GREEN}✅ Using existing file on Pi${NC}"
        ;;
    [Cc])
        echo -e "${YELLOW}⚠️  You'll need to download it manually on the Pi${NC}"
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac
echo ""

# Step 3: Run setup on Pi
echo -e "${YELLOW}Step 3: Running setup script on Raspberry Pi...${NC}"
echo ""

sshpass -p "$PI_PASS" ssh ${PI_USER}@${PI_HOST} << 'ENDSSH'
cd ~/rpi-dobot
chmod +x setup_official_dobot_api.sh
bash setup_official_dobot_api.sh
ENDSSH

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Setup failed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Setup completed${NC}"
echo ""

# Step 4: Run migration
echo -e "${YELLOW}Step 4: Running migration script...${NC}"
echo ""

sshpass -p "$PI_PASS" ssh ${PI_USER}@${PI_HOST} << 'ENDSSH'
cd ~/rpi-dobot
chmod +x migrate_to_official_api.sh
bash migrate_to_official_api.sh
ENDSSH

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Migration failed${NC}"
    echo ""
    echo "Rollback command (run on Pi):"
    echo "  cp ~/rpi-dobot/pwa-dobot-plc/backend/dobot_client_pydobot_backup.py ~/rpi-dobot/pwa-dobot-plc/backend/dobot_client.py"
    exit 1
fi

echo -e "${GREEN}✅ Migration completed${NC}"
echo ""

# Step 5: Run tests
echo -e "${YELLOW}Step 5: Running tests...${NC}"
echo ""

echo "Running connection test..."
sshpass -p "$PI_PASS" ssh ${PI_USER}@${PI_HOST} "cd ~/rpi-dobot && python3 test_official_api_connection.py"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Connection test passed${NC}"
    echo ""

    echo -e "${YELLOW}⚠️  MOVEMENT TEST - Ensure robot has clear space!${NC}"
    read -p "Press Enter to run movement test or Ctrl+C to skip..."

    sshpass -p "$PI_PASS" ssh ${PI_USER}@${PI_HOST} "cd ~/rpi-dobot && python3 test_official_api_movement.py"

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Movement test passed${NC}"
        echo ""
        echo -e "${GREEN}=================================================="
        echo "🎉 DEPLOYMENT SUCCESSFUL!"
        echo "==================================================${NC}"
        echo ""
        echo "The robot is now using the official Dobot API and should move correctly!"
        echo ""
        echo "Next steps:"
        echo "1. Test web application: ssh to Pi and run 'cd ~/rpi-dobot/pwa-dobot-plc/backend && python3 app.py'"
        echo "2. Open browser to: http://rpi:8080"
        echo "3. Test all functionality through web interface"
        echo ""
        echo "Enjoy your working Dobot! 🤖"
    else
        echo -e "${RED}❌ Movement test failed${NC}"
        echo "Check the logs above for errors"
    fi
else
    echo -e "${RED}❌ Connection test failed${NC}"
    echo "Check the logs above for errors"
    exit 1
fi
