"""
Test Counter Detection - Diagnostic Script
This script tests if YOLO detection is working with your trained model
"""

import os
import sys
import logging
import cv2
import numpy as np

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Check if ultralytics is available
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    logger.error("✗ Ultralytics YOLO library is NOT installed")
    logger.error("  Install with: pip install ultralytics")
    sys.exit(1)

# Load model
model_path = os.path.expanduser('~/counter_detector.pt')
logger.info(f"Loading model from: {model_path}")

if not os.path.exists(model_path):
    logger.error(f"✗ Model file NOT found at {model_path}")
    sys.exit(1)

try:
    model = YOLO(model_path)
    logger.info("✓ Model loaded successfully!")
except Exception as e:
    logger.error(f"✗ Failed to load model: {e}")
    sys.exit(1)

# Test with different confidence thresholds
logger.info("\n" + "="*50)
logger.info("Testing Detection with Different Confidence Levels")
logger.info("="*50)

# Try to get a frame from camera (if available)
try:
    cap = cv2.VideoCapture(0)
    if cap.isOpened():
        ret, frame = cap.read()
        cap.release()
        
        if ret and frame is not None:
            logger.info(f"✓ Got test frame from camera: {frame.shape}")
            
            # Test with different confidence levels
            for conf_threshold in [0.01, 0.1, 0.25, 0.5]:
                logger.info(f"\nTesting with confidence threshold: {conf_threshold}")
                
                # Crop frame (same as backend does)
                original_height = frame.shape[0]
                crop_top = int(original_height * 25 / 100)
                crop_bottom = int(original_height * (100 - 25) / 100)
                cropped_frame = frame[crop_top:crop_bottom, :]
                
                # Run detection
                results = model(cropped_frame, conf=conf_threshold, iou=0.45, verbose=False)
                
                # Count detections
                detection_count = 0
                for result in results:
                    boxes = result.boxes
                    detection_count += len(boxes)
                    
                    # Show details of first few detections
                    for i, box in enumerate(boxes[:3]):
                        conf = float(box.conf[0])
                        cls = int(box.cls[0])
                        class_name = result.names[cls]
                        logger.info(f"  Detection {i+1}: {class_name} (confidence: {conf:.3f})")
                
                logger.info(f"  Total detections: {detection_count}")
                
                if detection_count > 0:
                    logger.info(f"  ✓ SUCCESS! Found {detection_count} counter(s) with conf={conf_threshold}")
                    break
            else:
                logger.warning("  ⚠ No detections found at any confidence level")
                logger.info("  Try:")
                logger.info("    - Lowering confidence threshold further (try 0.001)")
                logger.info("    - Checking camera view - are counters visible?")
                logger.info("    - Adjusting crop settings if counters are in cropped areas")
        else:
            logger.warning("✗ Could not read frame from camera")
    else:
        logger.warning("✗ Camera not available for testing")
except Exception as e:
    logger.warning(f"✗ Camera test failed: {e}")

logger.info("\n" + "="*50)
logger.info("Detection Test Complete")
logger.info("="*50)
logger.info("\nIf no detections were found:")
logger.info("  1. Check that counters are visible in camera view")
logger.info("  2. Try lowering confidence to 0.001 in vision-system.html")
logger.info("  3. Check backend logs when running detection")
logger.info("  4. Verify camera is working and focused on counters")

