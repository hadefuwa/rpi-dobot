"""
Backend Diagnostic Script
Checks if backend is configured correctly for YOLO detection
"""

import os
import sys
import json

print("="*60)
print("Backend YOLO Detection Diagnostic")
print("="*60)
print()

# Check 1: Model file exists
print("[1/5] Checking model file...")
model_path = os.path.expanduser('~/counter_detector.pt')
if os.path.exists(model_path):
    size_mb = os.path.getsize(model_path) / (1024 * 1024)
    print(f"  ✓ Model found: {model_path} ({size_mb:.2f} MB)")
else:
    print(f"  ✗ Model NOT found at: {model_path}")
    print("  Expected location: ~/counter_detector.pt")
print()

# Check 2: Ultralytics installed
print("[2/5] Checking Ultralytics library...")
try:
    from ultralytics import YOLO
    print("  ✓ Ultralytics is installed")
except ImportError:
    print("  ✗ Ultralytics NOT installed")
    print("  Install with: pip3 install ultralytics")
    sys.exit(1)
print()

# Check 3: Can load model
print("[3/5] Testing model loading...")
try:
    model = YOLO(model_path)
    print("  ✓ Model loads successfully")
    
    # Check model classes
    if hasattr(model, 'names'):
        print(f"  ✓ Model classes: {model.names}")
        if 0 in model.names:
            print(f"  ✓ Class 0 (counter) is available: '{model.names[0]}'")
except Exception as e:
    print(f"  ✗ Failed to load model: {e}")
    sys.exit(1)
print()

# Check 4: Config file
print("[4/5] Checking config.json...")
config_path = os.path.join(os.path.dirname(__file__), 'config.json')
if os.path.exists(config_path):
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        print("  ✓ config.json exists and is valid JSON")
        if 'camera' in config:
            print(f"  ✓ Camera config found: {config['camera']}")
        else:
            print("  ⚠ Camera config not found (will use defaults)")
    except Exception as e:
        print(f"  ✗ Error reading config: {e}")
else:
    print("  ⚠ config.json not found (will use defaults)")
print()

# Check 5: Backend code
print("[5/5] Checking backend code...")
app_path = os.path.join(os.path.dirname(__file__), 'app.py')
if os.path.exists(app_path):
    with open(app_path, 'r') as f:
        content = f.read()
        if 'counter_detector.pt' in content:
            print("  ✓ app.py references counter_detector.pt")
        if 'load_yolo_model' in content:
            print("  ✓ app.py has load_yolo_model function")
        if "object_method = data.get('object_method', 'yolo')" in content:
            print("  ✓ app.py defaults to 'yolo' method")
        else:
            print("  ⚠ app.py might not default to 'yolo' method")
else:
    print("  ✗ app.py not found")
print()

print("="*60)
print("Diagnostic Complete")
print("="*60)
print()
print("Next steps:")
print("  1. Start your backend: python3 app.py")
print("  2. Look for log message: 'YOLO model loaded: ~/counter_detector.pt'")
print("  3. In vision-system.html, try confidence threshold: 0.001")
print("  4. Check Serial Monitor in browser for detection logs")
print("  5. Verify camera is connected and showing counters")
print()

