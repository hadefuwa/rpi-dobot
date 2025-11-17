"""
Camera Service for USB Camera Access and Defect Detection
Uses OpenCV for camera capture and image processing
"""

import cv2
import numpy as np
import logging
import threading
import time
from typing import Optional, Dict, List, Tuple
import io
import os

logger = logging.getLogger(__name__)

class CameraService:
    """Service for managing USB camera and defect detection"""
    
    def __init__(self, camera_index: int = 0, width: int = 640, height: int = 480):
        """
        Initialize camera service
        
        Args:
            camera_index: Camera device index (usually 0 for first USB camera)
            width: Frame width
            height: Frame height
        """
        self.camera_index = camera_index
        self.width = width
        self.height = height
        self.camera: Optional[cv2.VideoCapture] = None
        self.is_streaming = False
        self.lock = threading.Lock()
        self.last_frame = None
        self.frame_time = 0
        # Object detection model
        self.object_net = None
        self.object_classes = []
        self.object_detection_enabled = False
        # Background subtractor for moving object detection
        self.bg_subtractor: Optional[cv2.BackgroundSubtractor] = None
        self.bg_learning_frames = 0
        self.bg_initialized = False
        
    def initialize_camera(self) -> bool:
        """Initialize and open camera"""
        try:
            with self.lock:
                if self.camera is not None:
                    self.camera.release()
                
                self.camera = cv2.VideoCapture(self.camera_index)
                
                if not self.camera.isOpened():
                    logger.error(f"Failed to open camera at index {self.camera_index}")
                    return False
                
                # Set camera properties
                self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
                self.camera.set(cv2.CAP_PROP_FPS, 30)
                self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer for faster response

                # Quick warm up camera (reduced from 5 to 2 frames)
                for _ in range(2):
                    ret, _ = self.camera.read()
                    if not ret:
                        break
                
                logger.info(f"Camera initialized successfully at index {self.camera_index}")
                return True
                
        except Exception as e:
            logger.error(f"Error initializing camera: {e}")
            return False
    
    def release_camera(self):
        """Release camera resources"""
        with self.lock:
            if self.camera is not None:
                self.camera.release()
                self.camera = None
                logger.info("Camera released")
            # Reset background subtractor
            if self.bg_subtractor is not None:
                self.bg_subtractor = None
                self.bg_initialized = False
                self.bg_learning_frames = 0
                logger.info("Background subtractor reset")
    
    def read_frame(self) -> Optional[np.ndarray]:
        """Read a single frame from camera"""
        try:
            with self.lock:
                if self.camera is None or not self.camera.isOpened():
                    return None
                
                ret, frame = self.camera.read()
                if ret:
                    self.last_frame = frame.copy()
                    self.frame_time = time.time()
                    return frame
                return None
                
        except Exception as e:
            logger.error(f"Error reading frame: {e}")
            return None
    
    def get_frame_jpeg(self, quality: int = 85) -> Optional[bytes]:
        """
        Get current frame as JPEG bytes
        
        Args:
            quality: JPEG quality (0-100)
            
        Returns:
            JPEG bytes or None if frame not available
        """
        frame = self.read_frame()
        if frame is None:
            return None
        
        try:
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
            ret, buffer = cv2.imencode('.jpg', frame, encode_param)
            if ret:
                return buffer.tobytes()
        except Exception as e:
            logger.error(f"Error encoding frame: {e}")
        
        return None
    
    def detect_objects(self, frame: np.ndarray, method: str = 'blob', params: Optional[Dict] = None) -> Dict:
        """
        Detect circular counters on conveyor belt using SimpleBlobDetector.
        Works in changing lighting conditions by detecting round blob shapes.

        Args:
            frame: Input image frame (BGR format)
            method: Detection method ('blob' for SimpleBlobDetector)
            params: Optional detection parameters:
                - min_area: Minimum counter area in pixels (default: 500)
                - max_area: Maximum counter area in pixels (default: 50000)
                - min_circularity: Minimum circularity (0-1, default: 0.6)
                - min_convexity: Minimum convexity (0-1, default: 0.7)
                - min_inertia_ratio: Minimum inertia ratio (0-1, default: 0.3)

        Returns:
            Dictionary with counter detection results
        """
        if frame is None:
            return {
                'objects_found': False,
                'object_count': 0,
                'objects': [],
                'error': 'No frame provided'
            }

        if params is None:
            params = {}

        # Extract parameters
        min_area = params.get('min_area', 500)
        max_area = params.get('max_area', 50000)
        min_circularity = params.get('min_circularity', 0.6)
        min_convexity = params.get('min_convexity', 0.7)
        min_inertia_ratio = params.get('min_inertia_ratio', 0.3)

        try:
            # Step 1: Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Step 2: Apply Gaussian blur to reduce noise and reflections
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)

            # Step 3: Setup SimpleBlobDetector parameters
            blob_params = cv2.SimpleBlobDetector_Params()

            # Filter by Area
            blob_params.filterByArea = True
            blob_params.minArea = min_area
            blob_params.maxArea = max_area

            # Filter by Circularity (how round the blob is)
            blob_params.filterByCircularity = True
            blob_params.minCircularity = min_circularity

            # Filter by Convexity (how convex the contour is)
            blob_params.filterByConvexity = True
            blob_params.minConvexity = min_convexity

            # Filter by Inertia (how elongated the blob is)
            blob_params.filterByInertia = True
            blob_params.minInertiaRatio = min_inertia_ratio

            # Filter by Color (detect dark and light blobs)
            blob_params.filterByColor = False

            # Step 4: Create detector and detect blobs
            detector = cv2.SimpleBlobDetector_create(blob_params)
            keypoints = detector.detect(blurred)

            objects = []

            # Step 5: Extract blob information
            for kp in keypoints:
                x, y = kp.pt
                size = kp.size
                radius = size / 2
                area = np.pi * radius * radius

                # Calculate bounding box
                x_int = int(x - radius)
                y_int = int(y - radius)
                w = h = int(size)

                objects.append({
                    'type': 'counter',
                    'x': x_int,
                    'y': y_int,
                    'width': w,
                    'height': h,
                    'area': float(area),
                    'center': (int(x), int(y)),
                    'radius': int(radius),
                    'circularity': 1.0,  # SimpleBlobDetector filters by circularity already
                    'confidence': 0.9,  # High confidence for blob detection
                    'method': 'blob'
                })

            return {
                'objects_found': len(objects) > 0,
                'object_count': len(objects),
                'objects': objects,
                'method': method,
                'timestamp': time.time()
            }

        except Exception as e:
            logger.error(f"Error in object detection: {e}")
            return {
                'objects_found': False,
                'object_count': 0,
                'objects': [],
                'error': str(e)
            }
    
    def _merge_nearby_objects(self, objects: List[Dict], threshold: int = 30) -> List[Dict]:
        """Merge objects that are close to each other"""
        if len(objects) == 0:
            return []
        
        merged = []
        used = set()
        
        for i, obj in enumerate(objects):
            if i in used:
                continue
            
            center = obj['center']
            group = [obj]
            used.add(i)
            
            for j, other_obj in enumerate(objects):
                if j in used or j == i:
                    continue
                
                other_center = other_obj['center']
                dist = np.sqrt((center[0] - other_center[0])**2 + (center[1] - other_center[1])**2)
                
                if dist < threshold:
                    group.append(other_obj)
                    used.add(j)
            
            # Merge group into single object
            if len(group) > 1:
                xs = [o['x'] for o in group]
                ys = [o['y'] for o in group]
                ws = [o['width'] for o in group]
                hs = [o['height'] for o in group]
                
                x, y = min(xs), min(ys)
                w = max(x + w for x, w in zip(xs, ws)) - x
                h = max(y + h for y, h in zip(ys, hs)) - y
                
                merged.append({
                    'type': 'object',
                    'x': x,
                    'y': y,
                    'width': w,
                    'height': h,
                    'area': sum(o['area'] for o in group),
                    'center': (x + w//2, y + h//2),
                    'confidence': max(o['confidence'] for o in group),
                    'method': 'merged'
                })
            else:
                merged.append(obj)
        
        return merged
    
    def _extract_circle_roi(self, frame: np.ndarray, x: int, y: int, radius: int) -> Optional[np.ndarray]:
        """
        Extract region of interest around a circle for classification
        
        Args:
            frame: Full image frame
            x: Circle center X coordinate
            y: Circle center Y coordinate
            radius: Circle radius
            
        Returns:
            ROI image or None if extraction fails
        """
        y1 = max(0, y - radius)
        y2 = min(frame.shape[0], y + radius)
        x1 = max(0, x - radius)
        x2 = min(frame.shape[1], x + radius)
        
        roi = frame[y1:y2, x1:x2]
        return roi if roi.size > 0 else None
    
    def _create_circle_object(self, x: int, y: int, radius: int, area: float, 
                             confidence: float) -> Dict:
        """
        Create a standardized circle object dictionary
        
        Args:
            x: Circle center X coordinate
            y: Circle center Y coordinate
            radius: Circle radius
            area: Circle area
            confidence: Detection confidence (0-1)
            
        Returns:
            Object dictionary
        """
        return {
            'type': 'circle',
            'x': int(x - radius),
            'y': int(y - radius),
            'width': int(2 * radius),
            'height': int(2 * radius),
            'area': float(area),
            'center': (int(x), int(y)),
            'radius': int(radius),
            'circularity': 1.0,
            'confidence': round(confidence, 2),
            'method': 'circle',
            'aspect_ratio': 1.0
        }
    
    def classify_disc(self, roi: np.ndarray) -> str:
        """
        Classify a disc (counter) as white, black, silver, or grey
        Uses color analysis in HSV space
        
        Args:
            roi: Region of interest (the disc area) in BGR format
            
        Returns:
            Classification string: 'white', 'black', 'silver', or 'grey'
        """
        if roi is None or roi.size == 0:
            return 'unknown'
        
        try:
            # Convert to HSV for color analysis
            hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
            
            # Calculate mean HSV values
            mean_hsv = hsv.mean(axis=(0, 1))  # H, S, V mean values
            H, S, V = mean_hsv
            
            # Calculate variance in BGR space for silver vs grey detection
            grey_var = np.var(roi)
            
            # Classification logic based on brightness, saturation, and variance
            if V > 180 and S < 40:
                return 'white'
            elif V < 60:
                return 'black'
            elif grey_var > 200:
                return 'silver'
            else:
                return 'grey'
                
        except Exception as e:
            logger.error(f"Error classifying disc: {e}")
            return 'unknown'
    
    def _detect_circles_hough(self, frame: np.ndarray, params: Dict, 
                              min_object_area: int, max_object_area: int, 
                              min_confidence: float) -> List[Dict]:
        """
        Detect circles using HoughCircles on grayscale image
        
        Args:
            frame: Input frame in BGR format
            params: Detection parameters
            min_object_area: Minimum object area
            max_object_area: Maximum object area
            min_confidence: Minimum confidence threshold
            
        Returns:
            List of detected circle objects
        """
        objects = []
        
        # Convert to grayscale for circle detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur to reduce noise (larger kernel for better smoothing)
        blurred = cv2.GaussianBlur(gray, (11, 11), 2)
        
        # HoughCircles parameters - optimized for ultra-reliable circle detection
        dp = 1  # Inverse ratio of accumulator resolution
        min_dist = params.get('min_dist_between_circles', 50)
        param1 = 100  # Upper threshold for edge detection (higher = better edge detection)
        param2 = params.get('hough_circle_threshold', 30)  # Higher = fewer false positives, more reliable
        min_radius = max(5, int(np.sqrt(min_object_area / np.pi)))  # Ensure minimum radius is at least 5 pixels
        max_radius = int(np.sqrt(max_object_area / np.pi))
        
        logger.info(f"Circle detection params: min_area={min_object_area}, max_area={max_object_area}, "
                   f"min_radius={min_radius}, max_radius={max_radius}, param2={param2}")
        
        # Detect circles using HoughCircles
        circles = cv2.HoughCircles(
            blurred,
            cv2.HOUGH_GRADIENT,
            dp=dp,
            minDist=min_dist,
            param1=param1,
            param2=param2,
            minRadius=min_radius,
            maxRadius=max_radius
        )
        
        if circles is not None:
            circles = np.round(circles[0, :]).astype("int")
            logger.info(f"HoughCircles found {len(circles)} potential circles")
            
            for (x, y, r) in circles:
                # Calculate area
                area = np.pi * r * r
                
                logger.debug(f"Circle candidate: center=({x},{y}), radius={r}, area={area:.0f}")
                
                # Basic area filtering: Only accept circles within the size range
                if area < min_object_area:
                    logger.debug(f"  Rejected: area {area:.0f} < min {min_object_area}")
                    continue
                if area > max_object_area:
                    logger.debug(f"  Rejected: area {area:.0f} > max {max_object_area}")
                    continue
                
                # Simple confidence calculation based on size
                # Normalize area to 0-1 range within min/max bounds
                if max_object_area > min_object_area:
                    normalized_area = (area - min_object_area) / (max_object_area - min_object_area)
                    # Higher confidence for circles in the middle range
                    confidence = 0.5 + (normalized_area * 0.5)  # Range: 0.5 to 1.0
                else:
                    confidence = 0.7  # Default confidence
                
                # Only add if meets confidence threshold
                if confidence >= min_confidence:
                    logger.info(f"  Accepted circle: center=({x},{y}), radius={r}, area={area:.0f}, confidence={confidence:.2f}")
                    obj = self._create_circle_object(x, y, r, area, confidence)
                    objects.append(obj)
                else:
                    logger.debug(f"  Rejected: confidence {confidence:.2f} < min {min_confidence}")
        
        logger.info(f"Total circles detected after filtering: {len(objects)}")
        
        return objects
    
    def _detect_circles_hsv_fallback(self, frame: np.ndarray, params: Dict,
                                     min_object_area: int, max_object_area: int,
                                     min_confidence: float) -> List[Dict]:
        """
        Fallback circle detection using HSV color masking (for when HoughCircles fails)
        
        Args:
            frame: Input frame in BGR format
            params: Detection parameters
            min_object_area: Minimum object area
            max_object_area: Maximum object area
            min_confidence: Minimum confidence threshold
            
        Returns:
            List of detected circle objects
        """
        objects = []
        
        # Convert to HSV for color-based detection
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        hsv_hue_min = params.get('hsv_hue_min', 90)
        hsv_hue_max = params.get('hsv_hue_max', 130)
        
        # Create blue background mask
        lower_blue = np.array([hsv_hue_min, 50, 50])
        upper_blue = np.array([hsv_hue_max, 255, 255])
        blue_mask = cv2.inRange(hsv, lower_blue, upper_blue)
        object_mask = cv2.bitwise_not(blue_mask)
        
        # Clean up mask
        kernel_size = params.get('morphological_kernel_size', 7)
        kernel = np.ones((kernel_size, kernel_size), np.uint8)
        object_mask = cv2.morphologyEx(object_mask, cv2.MORPH_CLOSE, kernel)
        object_mask = cv2.morphologyEx(object_mask, cv2.MORPH_OPEN, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(object_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if min_object_area < area < max_object_area:
                (x, y), radius = cv2.minEnclosingCircle(contour)
                
                # Calculate circularity
                perimeter = cv2.arcLength(contour, True)
                circularity = 4 * np.pi * area / (perimeter ** 2) if perimeter > 0 else 0
                
                min_circularity = params.get('min_circularity', 0.6)
                if circularity >= min_circularity:
                    x_int, y_int, w, h = cv2.boundingRect(contour)
                    aspect_ratio = float(w) / h if h > 0 else 0
                    
                    if 0.7 < aspect_ratio < 1.3:
                        # Calculate confidence based on circularity and size
                        size_confidence = min(area / max_object_area, 1.0)
                        confidence = (circularity * 0.7 + size_confidence * 0.3)
                        
                        if confidence >= min_confidence:
                            obj = self._create_circle_object(int(x), int(y), int(radius), area, confidence)
                            obj['circularity'] = round(circularity, 2)
                            obj['aspect_ratio'] = round(aspect_ratio, 2)
                            objects.append(obj)
        
        return objects
    
    def draw_objects(self, frame: np.ndarray, objects: List[Dict], color: Tuple[int, int, int] = (0, 255, 0)) -> np.ndarray:
        """
        Draw detected counters on frame with bounding box and info overlay.

        Args:
            frame: Input frame
            objects: List of detected counter objects
            color: Color for annotations (default: green)

        Returns:
            Annotated frame with visual overlays
        """
        annotated = frame.copy()

        for obj in objects:
            x, y = obj['x'], obj['y']
            w, h = obj['width'], obj['height']
            center = obj['center']

            # Draw bounding box
            cv2.rectangle(annotated, (x, y), (x + w, y + h), color, 2)

            # Draw center point
            cv2.circle(annotated, center, 5, color, -1)

            # Draw circle around center for visual emphasis
            radius = max(w, h) // 2
            cv2.circle(annotated, center, radius, color, 2)

            # Draw label with counter info
            confidence = obj.get('confidence', 0)
            circularity = obj.get('circularity', 0)
            label = f"Counter ({confidence*100:.0f}%, C:{circularity:.2f})"

            cv2.putText(annotated, label, (x, y - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        return annotated
    
    def detect_defects(self, frame: np.ndarray, method: str = 'blob', params: Optional[Dict] = None) -> Dict:
        """
        Detect defects in an image frame
        
        Note: Defect detection is currently disabled - focus on object/counter detection first
        """
        return {
            'defects_found': False,
            'defect_count': 0,
            'defects': [],
            'confidence': 0.0,
            'method': method,
            'timestamp': time.time(),
            'note': 'Defect detection is currently disabled'
        }
    def _detect_blobs(self, gray: np.ndarray, min_area: int = 10, max_area: int = 5000,
                     adaptive_block: int = 11, adaptive_c: int = 2, kernel_size: int = 3) -> List[Dict]:
        """Stub - defect detection disabled"""
        return []
    
    def _detect_contours(self, gray: np.ndarray, min_area: int = 50, max_area: int = 10000,
                        canny_low: int = 50, canny_high: int = 150, aspect_ratio_min: float = 0.2,
                        aspect_ratio_max: float = 5.0, dilation_iterations: int = 1, kernel_size: int = 3) -> List[Dict]:
        """Stub - defect detection disabled"""
        return []
    
    def _detect_edges(self, gray: np.ndarray, canny_low: int = 30, canny_high: int = 100,
                     hough_threshold: int = 50, min_line_length: int = 30, max_line_gap: int = 10,
                     line_grouping_distance: int = 30, min_lines_per_defect: int = 2, min_defect_size: int = 10) -> List[Dict]:
        """Stub - defect detection disabled"""
        return []
    
    def _merge_nearby_defects(self, defects: List[Dict], threshold: int = 20) -> List[Dict]:
        """Stub - defect detection disabled"""
        return defects if defects else []
    
    def _calculate_confidence(self, defects: List[Dict], frame_shape: Tuple[int, int, int]) -> float:
        """Stub - defect detection disabled, always returns 0.0"""
        return 0.0
    
    def draw_defects(self, frame: np.ndarray, defects: List[Dict]) -> np.ndarray:
        """
        Stub - defect detection disabled, returns frame unchanged
        """
        # Defect detection is disabled, just return the frame as-is
        return frame.copy()

