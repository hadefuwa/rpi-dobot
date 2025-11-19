"""
Test script to verify YOLOv11n counter_detector.pt model is loaded and working
Run this to check if your AI model is being used correctly
"""

import os
import sys
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Check if ultralytics is available
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
    logger.info("✓ Ultralytics YOLO library is installed")
except ImportError:
    YOLO_AVAILABLE = False
    logger.error("✗ Ultralytics YOLO library is NOT installed")
    logger.error("  Install with: pip install ultralytics")
    sys.exit(1)

# Check model file location
model_path = os.path.expanduser('~/counter_detector.pt')
logger.info(f"\nChecking for model at: {model_path}")

if os.path.exists(model_path):
    file_size = os.path.getsize(model_path) / (1024 * 1024)  # Size in MB
    logger.info(f"✓ Model file found! Size: {file_size:.2f} MB")
else:
    logger.error(f"✗ Model file NOT found at {model_path}")
    logger.error("  Expected location: ~/counter_detector.pt")
    logger.error("  On Windows: C:\\Users\\YourUsername\\counter_detector.pt")
    logger.error("  On Linux/Mac: /home/username/counter_detector.pt")
    sys.exit(1)

# Try to load the model
logger.info("\nAttempting to load YOLO model...")
try:
    model = YOLO(model_path)
    logger.info("✓ Model loaded successfully!")
    
    # Get model info
    logger.info(f"\nModel Information:")
    logger.info(f"  - Model type: {type(model).__name__}")
    
    # Try to get model metadata
    if hasattr(model, 'model'):
        logger.info(f"  - Model architecture loaded")
    
    logger.info("\n✓ Your YOLOv11n counter_detector.pt model is ready to use!")
    logger.info("\nTo verify it's working in your app:")
    logger.info("  1. Check backend logs when starting the server")
    logger.info("  2. Look for: 'YOLO model loaded: ~/counter_detector.pt'")
    logger.info("  3. When detecting, check logs for: 'YOLO detected X objects'")
    
except Exception as e:
    logger.error(f"✗ Failed to load model: {e}")
    logger.error("  This might indicate:")
    logger.error("  - Model file is corrupted")
    logger.error("  - Wrong model format")
    logger.error("  - Missing dependencies")
    sys.exit(1)

