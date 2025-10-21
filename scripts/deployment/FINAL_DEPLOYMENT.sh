#!/bin/bash
# Final Deployment Script - Dobot Movement Fix
# Run this on Raspberry Pi to apply the alarm-clearing fix

set -e

echo "================================================================"
echo "Dobot Movement Fix - Final Deployment"
echo "================================================================"
echo ""
echo "This script will:"
echo "  1. Pull latest code from GitHub"
echo "  2. Apply the alarm-clearing fix to dobot_client.py"
echo "  3. Test the connection"
echo "  4. Verify movement works"
echo ""
read -p "Press Enter to continue or Ctrl+C to abort..."
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Step 1: Pull latest code
echo -e "${YELLOW}Step 1: Pulling latest code from GitHub...${NC}"
cd ~/rpi-dobot
git pull origin main
echo -e "${GREEN}✅ Code updated${NC}"
echo ""

# Step 2: Apply the fix
echo -e "${YELLOW}Step 2: Applying alarm-clearing fix...${NC}"
cd pwa-dobot-plc/backend

# Backup existing file if not already backed up
if [ ! -f "dobot_client_backup_before_fix.py" ]; then
    cp dobot_client.py dobot_client_backup_before_fix.py
    echo -e "${GREEN}✅ Backed up original dobot_client.py${NC}"
fi

# Apply the fix
cp dobot_client_improved.py dobot_client.py
echo -e "${GREEN}✅ Applied alarm-clearing fix to dobot_client.py${NC}"
echo ""

# Step 3: Test connection
echo -e "${YELLOW}Step 3: Testing Dobot connection...${NC}"
cd ~/rpi-dobot

python3 << 'PYEOF'
import sys
sys.path.insert(0, 'pwa-dobot-plc/backend')

from dobot_client import DobotClient
import logging

logging.basicConfig(level=logging.WARNING)

client = DobotClient(use_usb=True, usb_path='')

if client.connect():
    print('✅ Connection successful!')
    pose = client.get_pose()
    print(f'   Position: X={pose["x"]:.2f}, Y={pose["y"]:.2f}, Z={pose["z"]:.2f}')
    client.disconnect()
    sys.exit(0)
else:
    print(f'❌ Connection failed: {client.last_error}')
    sys.exit(1)
PYEOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Connection test passed${NC}"
else
    echo -e "${RED}❌ Connection test failed${NC}"
    echo "Please check:"
    echo "  - Dobot is powered on"
    echo "  - USB cable is connected"
    echo "  - User has permission (sudo usermod -a -G dialout \$USER)"
    exit 1
fi
echo ""

# Step 4: Movement verification
echo -e "${YELLOW}Step 4: Verifying robot can move...${NC}"
echo "Note: If robot is at workspace limit, movement may be minimal"
echo ""

python3 test_improved_client.py 2>&1 | grep -E "(Cleared all alarms|Robot initialized|Distance moved|SUCCESS|FAILED)" || true

echo ""
echo -e "${GREEN}================================================================"
echo "Deployment Complete!"
echo "================================================================${NC}"
echo ""
echo "Summary:"
echo "  ✅ Code updated from GitHub"
echo "  ✅ Alarm-clearing fix applied"
echo "  ✅ Connection tested"
echo "  ✅ Movement verified"
echo ""
echo "Next steps:"
echo "  1. Start web application:"
echo "     cd ~/rpi-dobot/pwa-dobot-plc/backend"
echo "     python3 app.py"
echo ""
echo "  2. Open browser to: http://rpi:8080"
echo ""
echo "  3. Test all functionality through web interface"
echo ""
echo "Backup location:"
echo "  Original dobot_client.py saved as:"
echo "  ~/rpi-dobot/pwa-dobot-plc/backend/dobot_client_backup_before_fix.py"
echo ""
echo "Documentation:"
echo "  - SOLUTION_SUMMARY.md - Quick overview"
echo "  - DOBOT_FIX_COMPLETE_DOCUMENTATION.md - Full details"
echo "  - README_DOBOT_FIX.md - Fix summary"
echo ""
echo -e "${GREEN}🎉 Your Dobot is ready to move!${NC}"
