#!/bin/bash
# Migration Script - Switch from pydobot to Official Dobot API
# Run this on the Raspberry Pi after running setup_official_dobot_api.sh

set -e

echo "=================================================="
echo "Migrating to Official Dobot API"
echo "=================================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

BACKEND_DIR="$HOME/rpi-dobot/pwa-dobot-plc/backend"

# Check if we have the new API files
if [ ! -f "$BACKEND_DIR/DobotDLLType.py" ]; then
    echo -e "${RED}❌ DobotDLLType.py not found${NC}"
    echo "Please run setup_official_dobot_api.sh first"
    exit 1
fi

if [ ! -f "$BACKEND_DIR/DobotDll.so" ]; then
    echo -e "${RED}❌ DobotDll.so not found${NC}"
    echo "Please run setup_official_dobot_api.sh first"
    exit 1
fi

echo -e "${GREEN}✅ Official API files found${NC}"
echo ""

# Backup old dobot_client.py
echo -e "${YELLOW}Step 1: Backing up old dobot_client.py...${NC}"
if [ -f "$BACKEND_DIR/dobot_client.py" ]; then
    cp "$BACKEND_DIR/dobot_client.py" "$BACKEND_DIR/dobot_client_pydobot_backup.py"
    echo -e "${GREEN}✅ Backup created: dobot_client_pydobot_backup.py${NC}"
else
    echo -e "${YELLOW}⚠️  No existing dobot_client.py found${NC}"
fi
echo ""

# Replace with official API version
echo -e "${YELLOW}Step 2: Installing new dobot_client.py...${NC}"
if [ -f "$BACKEND_DIR/dobot_client_official.py" ]; then
    cp "$BACKEND_DIR/dobot_client_official.py" "$BACKEND_DIR/dobot_client.py"
    echo -e "${GREEN}✅ New dobot_client.py installed${NC}"
else
    echo -e "${RED}❌ dobot_client_official.py not found${NC}"
    echo "Please ensure you've uploaded all files to the Pi"
    exit 1
fi
echo ""

# Update requirements.txt
echo -e "${YELLOW}Step 3: Updating requirements.txt...${NC}"
cd "$HOME/rpi-dobot/pwa-dobot-plc/backend"

# Remove pydobot from requirements.txt
if grep -q "pydobot" requirements.txt; then
    sed -i '/pydobot/d' requirements.txt
    echo -e "${GREEN}✅ Removed pydobot from requirements.txt${NC}"
else
    echo -e "${YELLOW}⚠️  pydobot not found in requirements.txt${NC}"
fi
echo ""

# No new dependencies needed - we're using the DLL directly
echo "Updated requirements.txt (pydobot removed)"
echo ""

# Test the new implementation
echo -e "${YELLOW}Step 4: Testing new implementation...${NC}"
cd "$HOME/rpi-dobot"

python3 test_official_api_connection.py

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}=================================================="
    echo "✅ Migration Complete!"
    echo "==================================================${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Run: python3 test_official_api_movement.py"
    echo "2. Run: python3 test_official_api_peripherals.py"
    echo "3. Test web application: cd pwa-dobot-plc/backend && python3 app.py"
    echo ""
    echo "To rollback if needed:"
    echo "  cp pwa-dobot-plc/backend/dobot_client_pydobot_backup.py pwa-dobot-plc/backend/dobot_client.py"
else
    echo ""
    echo -e "${RED}❌ Connection test failed${NC}"
    echo "Check the error messages above"
    echo ""
    echo "To rollback:"
    echo "  cp pwa-dobot-plc/backend/dobot_client_pydobot_backup.py pwa-dobot-plc/backend/dobot_client.py"
    exit 1
fi
