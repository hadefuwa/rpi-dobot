"""
Direct Model Test - Test your trained YOLOv11n model with a camera frame
This will help us see if the model itself works
"""

import os
import sys
import cv2
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

try:
    from ultralytics import YOLO
except ImportError:
    logger.error("Ultralytics not installed. Run: pip3 install ultralytics")
    sys.exit(1)

# Load model
model_path = os.path.expanduser('~/counter_detector.pt')
logger.info(f"Loading model: {model_path}")

if not os.path.exists(model_path):
    logger.error(f"Model not found at {model_path}")
    sys.exit(1)

model = YOLO(model_path)
logger.info("✓ Model loaded")

# Try to get a frame from camera
logger.info("\nTrying to open camera...")
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    logger.error("✗ Cannot open camera. Make sure camera is connected.")
    sys.exit(1)

logger.info("✓ Camera opened")

# Set camera properties (like camera_service does)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_FPS, 30)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer for faster response

# Warm up camera by reading a few frames first (this helps avoid timeout)
logger.info("Warming up camera...")
for i in range(3):
    ret, _ = cap.read()
    if not ret:
        logger.warning(f"  Warm-up frame {i+1} failed, but continuing...")
    else:
        logger.info(f"  Warm-up frame {i+1} OK")

# Now try to get the actual frame we'll use
logger.info("Reading frame for detection...")
ret, frame = cap.read()
cap.release()

if not ret or frame is None:
    logger.error("✗ Could not read frame from camera")
    logger.info("\nTroubleshooting tips:")
    logger.info("  1. Make sure camera is connected: lsusb")
    logger.info("  2. Check if camera is in use by another process")
    logger.info("  3. Try: sudo chmod 666 /dev/video0")
    logger.info("  4. Try a different camera index (change 0 to 1 or 2)")
    sys.exit(1)

logger.info(f"✓ Got frame: {frame.shape}")

# Test with different confidence levels
logger.info("\n" + "="*60)
logger.info("Testing Detection with Different Confidence Levels")
logger.info("="*60)

for conf_threshold in [0.001, 0.01, 0.1, 0.25]:
    logger.info(f"\nTesting with confidence: {conf_threshold}")
    
    # Run detection on FULL frame (no cropping)
    results = model(frame, conf=conf_threshold, iou=0.45, verbose=False)
    
    detection_count = 0
    for result in results:
        boxes = result.boxes
        detection_count = len(boxes)
        
        # Show first 3 detections
        for i, box in enumerate(boxes[:3]):
            conf = float(box.conf[0])
            cls = int(box.cls[0])
            class_name = result.names[cls]
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
            logger.info(f"  Detection {i+1}: {class_name} (conf: {conf:.3f}) at ({int(x1)},{int(y1)})-({int(x2)},{int(y2)})")
    
    logger.info(f"  Total: {detection_count} counter(s) detected")
    
    if detection_count > 0:
        logger.info(f"\n✓ SUCCESS! Model IS working - found {detection_count} counter(s) at conf={conf_threshold}")
        logger.info("\nIf this works but your app doesn't, the issue is in how the app calls the model.")
        break
else:
    logger.warning("\n⚠ No detections found at any confidence level")
    logger.info("\nPossible issues:")
    logger.info("  1. Camera view doesn't show counters")
    logger.info("  2. Lighting is different from training")
    logger.info("  3. Counters are too small/far away")
    logger.info("  4. Model needs retraining with more diverse images")

logger.info("\n" + "="*60)

