"""
Vision Service - Isolated YOLO Detection Service
Runs YOLO in a separate process to prevent crashes from affecting the main Flask app.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import os
import time
import cv2
import numpy as np
import base64
from typing import Dict, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# YOLO model (loaded once at startup)
yolo_model = None
yolo_model_path = None
yolo_lock = None

# Try to import YOLO
try:
    from ultralytics import YOLO
    import threading
    YOLO_AVAILABLE = True
    yolo_lock = threading.Lock()
    logger.info("YOLO (Ultralytics) loaded successfully")
except ImportError:
    YOLO_AVAILABLE = False
    logger.error("YOLO not available - install with: pip install ultralytics")


def load_yolo_model(model_path: str) -> bool:
    """Load YOLO model once at startup"""
    global yolo_model, yolo_model_path
    
    if not YOLO_AVAILABLE:
        logger.error("YOLO library not available")
        return False
    
    try:
        logger.info(f"Loading YOLO model: {model_path}")
        yolo_model = YOLO(model_path)
        yolo_model_path = model_path
        logger.info(f"YOLO model loaded successfully: {model_path}")
        return True
    except Exception as e:
        logger.error(f"Error loading YOLO model: {e}")
        return False


def detect_with_yolo(frame: np.ndarray, params: Dict) -> Dict:
    """
    Detect objects using YOLO - isolated in this process
    
    Args:
        frame: Input image frame (BGR format)
        params: Detection parameters (conf, iou, classes, crop_top_percent, crop_bottom_percent)
    
    Returns:
        Dictionary with detection results
    """
    if not YOLO_AVAILABLE:
        return {
            'objects_found': False,
            'object_count': 0,
            'objects': [],
            'error': 'YOLO library not available'
        }
    
    if yolo_model is None:
        return {
            'objects_found': False,
            'object_count': 0,
            'objects': [],
            'error': 'YOLO model not loaded'
        }
    
    # Use lock to ensure thread safety (only one YOLO call at a time)
    with yolo_lock:
        try:
            # Extract parameters
            conf_threshold = params.get('conf', 0.25)
            iou = params.get('iou', 0.45)
            classes = params.get('classes', None)
            crop_top_percent = params.get('crop_top_percent', 0)
            crop_bottom_percent = params.get('crop_bottom_percent', 0)
            
            # Crop frame if needed
            original_height = frame.shape[0]
            crop_top = int(original_height * crop_top_percent / 100)
            crop_bottom = int(original_height * (100 - crop_bottom_percent) / 100)
            cropped_frame = frame[crop_top:crop_bottom, :]
            
            # Validate frame
            if cropped_frame.size == 0 or cropped_frame.shape[0] == 0 or cropped_frame.shape[1] == 0:
                return {
                    'objects_found': False,
                    'object_count': 0,
                    'objects': [],
                    'error': 'Invalid frame dimensions'
                }
            
            # Run YOLO inference
            logger.debug(f"Running YOLO inference on frame shape: {cropped_frame.shape}")
            results = yolo_model(cropped_frame, conf=conf_threshold, iou=iou, classes=classes, verbose=False)
            
            # Process results
            objects = []
            for result in results:
                try:
                    boxes = result.boxes
                    for box in boxes:
                        try:
                            # Extract box coordinates
                            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                            box_confidence = float(box.conf[0])
                            cls = int(box.cls[0])
                            class_name = result.names[cls]
                            
                            # Adjust coordinates back to original frame
                            x1_original = x1
                            y1_original = y1 + crop_top
                            x2_original = x2
                            y2_original = y2 + crop_top
                            
                            # Calculate dimensions
                            x = int(x1_original)
                            y = int(y1_original)
                            w = int(x2_original - x1_original)
                            h = int(y2_original - y1_original)
                            center_x = int(x1_original + w / 2)
                            center_y = int(y1_original + h / 2)
                            area = w * h
                            
                            objects.append({
                                'type': 'counter',
                                'class': class_name,
                                'class_id': cls,
                                'x': x,
                                'y': y,
                                'width': w,
                                'height': h,
                                'area': float(area),
                                'center': (center_x, center_y),
                                'confidence': round(box_confidence, 2),
                                'method': 'yolo'
                            })
                        except Exception as box_error:
                            logger.warning(f"Error processing YOLO box: {box_error}")
                            continue
                except Exception as result_error:
                    logger.warning(f"Error processing YOLO result: {result_error}")
                    continue
            
            logger.info(f"YOLO detected {len(objects)} objects")
            
            return {
                'objects_found': len(objects) > 0,
                'object_count': len(objects),
                'objects': objects,
                'method': 'yolo',
                'timestamp': time.time()
            }
            
        except Exception as e:
            logger.error(f"YOLO detection error: {e}", exc_info=True)
            return {
                'objects_found': False,
                'object_count': 0,
                'objects': [],
                'error': f'YOLO detection failed: {str(e)}'
            }


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'yolo_available': YOLO_AVAILABLE,
        'model_loaded': yolo_model is not None,
        'model_path': yolo_model_path
    })


@app.route('/detect', methods=['POST'])
def detect():
    """
    Detect objects in an image frame
    
    Expects JSON with:
    - frame_base64: Base64-encoded image (JPEG)
    - params: Detection parameters (conf, iou, classes, crop_top_percent, crop_bottom_percent)
    """
    try:
        data = request.json or {}
        
        # Decode base64 image
        frame_base64 = data.get('frame_base64')
        if not frame_base64:
            return jsonify({'error': 'frame_base64 is required'}), 400
        
        # Remove data URL prefix if present
        if ',' in frame_base64:
            frame_base64 = frame_base64.split(',')[1]
        
        # Decode image
        try:
            image_data = base64.b64decode(frame_base64)
            nparr = np.frombuffer(image_data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if frame is None:
                return jsonify({'error': 'Failed to decode image'}), 400
        except Exception as e:
            logger.error(f"Error decoding image: {e}")
            return jsonify({'error': f'Image decode error: {str(e)}'}), 400
        
        # Get detection parameters
        params = data.get('params', {})
        
        # Run detection
        result = detect_with_yolo(frame, params)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in detect endpoint: {e}", exc_info=True)
        return jsonify({
            'objects_found': False,
            'object_count': 0,
            'objects': [],
            'error': f'Detection service error: {str(e)}'
        }), 500


if __name__ == '__main__':
    # Load YOLO model at startup
    model_path = os.path.expanduser('~/counter_detector.pt')
    if os.path.exists(model_path):
        if load_yolo_model(model_path):
            logger.info("✅ Vision service ready with YOLO model")
        else:
            logger.error("❌ Failed to load YOLO model - service will return errors")
    else:
        logger.warning(f"⚠️ YOLO model not found at {model_path} - service will return errors")
    
    # Start Flask server
    port = int(os.getenv('VISION_PORT', 5001))
    logger.info(f"Starting vision service on port {port}")
    app.run(host='127.0.0.1', port=port, debug=False, threaded=True)

