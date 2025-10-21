#!/bin/bash
# Official Dobot DLL API Setup Script
# This script downloads and installs the official Dobot API on Raspberry Pi

set -e  # Exit on error

echo "=================================================="
echo "Official Dobot DLL API Setup"
echo "=================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -d "pwa-dobot-plc" ]; then
    echo -e "${RED}❌ Error: pwa-dobot-plc directory not found${NC}"
    echo "Please run this script from the rpi-dobot directory"
    exit 1
fi

echo -e "${YELLOW}Step 1: Downloading DobotDemoV2.0...${NC}"
cd ~
if [ ! -f "DobotDemoV2.0.zip" ]; then
    # Note: This URL might need to be updated - check https://www.dobot.cc/downloadcenter/dobot-magician.html
    # Alternative: User may need to download manually
    echo -e "${YELLOW}Please download DobotDemoV2.0.zip manually from:${NC}"
    echo "https://www.dobot.cc/downloadcenter/dobot-magician.html?sub_cat=72#sub-download"
    echo ""
    echo "Or if you have it on your PC, transfer it using:"
    echo "scp DobotDemoV2.0.zip pi@rpi:~/"
    echo ""
    read -p "Press Enter once you have downloaded the file to ~/DobotDemoV2.0.zip..."

    if [ ! -f "DobotDemoV2.0.zip" ]; then
        echo -e "${RED}❌ DobotDemoV2.0.zip still not found in home directory${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ DobotDemoV2.0.zip already downloaded${NC}"
fi

echo ""
echo -e "${YELLOW}Step 2: Extracting DobotDemoV2.0...${NC}"
if [ -d "DobotDemoV2.0" ]; then
    echo -e "${YELLOW}⚠️  DobotDemoV2.0 directory already exists, removing...${NC}"
    rm -rf DobotDemoV2.0
fi
unzip -q DobotDemoV2.0.zip
echo -e "${GREEN}✅ Extracted successfully${NC}"

echo ""
echo -e "${YELLOW}Step 3: Locating Python API files...${NC}"

# Find the Python demo directory
PYTHON_API_DIR=""
if [ -d "DobotDemoV2.0/DobotDemoForPython" ]; then
    PYTHON_API_DIR="DobotDemoV2.0/DobotDemoForPython"
elif [ -d "DobotDemoV2.0/Python" ]; then
    PYTHON_API_DIR="DobotDemoV2.0/Python"
else
    # Search for it
    PYTHON_API_DIR=$(find DobotDemoV2.0 -type d -name "*Python*" | head -1)
fi

if [ -z "$PYTHON_API_DIR" ]; then
    echo -e "${RED}❌ Could not find Python API directory${NC}"
    echo "Available directories:"
    ls -la DobotDemoV2.0/
    exit 1
fi

echo -e "${GREEN}✅ Found Python API at: $PYTHON_API_DIR${NC}"

echo ""
echo -e "${YELLOW}Step 4: Checking for required files...${NC}"

# Check for DobotDLLType.py
if [ ! -f "$PYTHON_API_DIR/DobotDLLType.py" ]; then
    echo -e "${RED}❌ DobotDLLType.py not found${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Found DobotDLLType.py${NC}"

# Check for Linux ARM DLL
DLL_FILE=""
if [ -f "$PYTHON_API_DIR/DobotDll.so" ]; then
    DLL_FILE="$PYTHON_API_DIR/DobotDll.so"
elif [ -f "$PYTHON_API_DIR/api/linux/arm/libDobotDll.so" ]; then
    DLL_FILE="$PYTHON_API_DIR/api/linux/arm/libDobotDll.so"
elif [ -f "$PYTHON_API_DIR/api/DobotDll.so" ]; then
    DLL_FILE="$PYTHON_API_DIR/api/DobotDll.so"
else
    # Search for any .so file
    DLL_FILE=$(find "$PYTHON_API_DIR" -name "*.so" -o -name "*DobotDll*" | grep -i "arm\|linux" | head -1)
fi

if [ -z "$DLL_FILE" ]; then
    echo -e "${RED}❌ Could not find DobotDll.so for Linux ARM${NC}"
    echo "Searching for available library files:"
    find "$PYTHON_API_DIR" -name "*.so" -o -name "*Dobot*"
    exit 1
fi
echo -e "${GREEN}✅ Found Dobot DLL at: $DLL_FILE${NC}"

echo ""
echo -e "${YELLOW}Step 5: Copying files to backend...${NC}"

BACKEND_DIR="$HOME/rpi-dobot/pwa-dobot-plc/backend"

# Copy DobotDLLType.py
cp "$PYTHON_API_DIR/DobotDLLType.py" "$BACKEND_DIR/"
echo -e "${GREEN}✅ Copied DobotDLLType.py${NC}"

# Copy DLL
cp "$DLL_FILE" "$BACKEND_DIR/DobotDll.so"
echo -e "${GREEN}✅ Copied DobotDll.so${NC}"

# Make DLL executable
chmod +x "$BACKEND_DIR/DobotDll.so"

echo ""
echo -e "${YELLOW}Step 6: Testing DLL loading...${NC}"
cd "$BACKEND_DIR"

python3 << 'PYEOF'
try:
    import DobotDLLType as dType
    print("✅ DobotDLLType imported successfully!")

    # Try to load the DLL
    api = dType.load()
    print("✅ DLL loaded successfully!")
    print(f"API object: {api}")
    print("")
    print("🎉 Official Dobot API is ready to use!")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
PYEOF

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}=================================================="
    echo "✅ Installation Complete!"
    echo "==================================================${NC}"
    echo ""
    echo "Next steps:"
    echo "1. The new dobot_client.py will use the official API"
    echo "2. Run test scripts to verify movement works"
    echo "3. Test the web application"
    echo ""
    echo "Files installed:"
    echo "  - $BACKEND_DIR/DobotDLLType.py"
    echo "  - $BACKEND_DIR/DobotDll.so"
else
    echo -e "${RED}❌ Installation failed during DLL test${NC}"
    exit 1
fi
