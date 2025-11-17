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
    
    def detect_objects(self, frame: np.ndarray, method: str = 'contour', params: Optional[Dict] = None) -> Dict:
        """
        Detect objects in an image frame before defect detection
        Uses background subtraction for moving objects on conveyor belts

        Args:
            frame: Input image frame (BGR format)
            method: Detection method ('contour', 'blob', 'combined', 'background', 'circle')
            params: Optional detection parameters:
                - min_object_area: Minimum object area in pixels (default: 2000)
                - max_object_area: Maximum object area in pixels (default: 100000)
                - use_background_subtraction: Use background subtraction (default: True)
                - bg_history: Background history frames (default: 500)
                - bg_threshold: Background threshold (default: 16)
                - bg_learning_rate: Background learning rate (default: 0.001)
                - aspect_ratio_min: Minimum aspect ratio (default: 0.2)
                - aspect_ratio_max: Maximum aspect ratio (default: 5.0)
                - min_confidence: Minimum confidence for detection (default: 0.5)
            
        Returns:
            Dictionary with object detection results
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
        
        # Extract parameters with better defaults for conveyor belt counters
        min_object_area = params.get('min_object_area', 5000)  # Increased to detect only larger objects
        max_object_area = params.get('max_object_area', 100000)  # Increased from 50000
        use_bg_subtraction = params.get('use_background_subtraction', True)
        bg_history = params.get('bg_history', 500)
        bg_threshold = params.get('bg_threshold', 32)  # Increased from 16 to reduce noise
        bg_learning_rate = params.get('bg_learning_rate', 0.001)
        aspect_ratio_min = params.get('aspect_ratio_min', 0.2)
        aspect_ratio_max = params.get('aspect_ratio_max', 5.0)
        min_confidence = params.get('min_confidence', 0.7)  # Increased from 0.5
        
        try:
            objects = []
            object_count = 0
            
            # Use background subtraction for moving objects on conveyor belt
            if use_bg_subtraction or method == 'background':
                # Initialize background subtractor if needed
                if self.bg_subtractor is None:
                    self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
                        history=bg_history,
                        varThreshold=bg_threshold,
                        detectShadows=True
                    )
                    self.bg_initialized = False
                    self.bg_learning_frames = 0
                
                # Convert to grayscale for background subtraction
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                # Apply Gaussian blur to reduce noise
                blurred = cv2.GaussianBlur(gray, (5, 5), 0)
                
                # Apply background subtraction
                fg_mask = self.bg_subtractor.apply(blurred, learningRate=bg_learning_rate)
                
                # Update learning frame count
                if not self.bg_initialized:
                    self.bg_learning_frames += 1
                    if self.bg_learning_frames >= 30:  # Learn background for 30 frames
                        self.bg_initialized = True
                
                # Only detect objects after background is learned
                if self.bg_initialized:
                    # Morphological operations to clean up the mask
                    kernel = np.ones((7, 7), np.uint8)  # Larger kernel to merge small regions
                    fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel)
                    fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)

                    # Dilate to merge nearby regions (reduced iterations)
                    fg_mask = cv2.dilate(fg_mask, kernel, iterations=1)  # Reduced from 2 to 1
                    
                    # Find contours in the foreground mask
                    contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    
                    for contour in contours:
                        area = cv2.contourArea(contour)
                        if min_object_area < area < max_object_area:
                            x, y, w, h = cv2.boundingRect(contour)
                            
                            # Calculate aspect ratio
                            aspect_ratio = float(w) / h if h > 0 else 0
                            if aspect_ratio_min < aspect_ratio < aspect_ratio_max:
                                # Calculate solidity (how convex the shape is)
                                hull = cv2.convexHull(contour)
                                hull_area = cv2.contourArea(hull)
                                solidity = float(area) / hull_area if hull_area > 0 else 0
                                
                                # Calculate confidence based on area and solidity
                                area_confidence = min(area / max_object_area, 1.0)
                                confidence = (area_confidence * 0.6 + solidity * 0.4)
                                
                                if confidence >= min_confidence:
                                    objects.append({
                                        'type': 'object',
                                        'x': int(x),
                                        'y': int(y),
                                        'width': int(w),
                                        'height': int(h),
                                        'area': float(area),
                                        'center': (int(x + w/2), int(y + h/2)),
                                        'confidence': round(confidence, 2),
                                        'method': 'background',
                                        'aspect_ratio': round(aspect_ratio, 2),
                                        'solidity': round(solidity, 2)
                                    })
                                    object_count += 1
            
            # Fallback to traditional methods if background subtraction is disabled
            if not use_bg_subtraction:
                if method == 'contour' or method == 'combined':
                    # Simple contour-based object detection
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
                    
                    # Adaptive threshold to find objects
                    thresh = cv2.adaptiveThreshold(
                        blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                        cv2.THRESH_BINARY_INV, 11, 2
                    )
                    
                    # Morphological operations
                    kernel = np.ones((5, 5), np.uint8)
                    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
                    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
                    
                    # Find contours
                    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    
                    for contour in contours:
                        area = cv2.contourArea(contour)
                        if min_object_area < area < max_object_area:
                            x, y, w, h = cv2.boundingRect(contour)
                            # Calculate aspect ratio
                            aspect_ratio = float(w) / h if h > 0 else 0
                            if aspect_ratio_min < aspect_ratio < aspect_ratio_max:
                                objects.append({
                                    'type': 'object',
                                    'x': int(x),
                                    'y': int(y),
                                    'width': int(w),
                                    'height': int(h),
                                    'area': float(area),
                                    'center': (int(x + w/2), int(y + h/2)),
                                    'confidence': 0.7,
                                    'method': 'contour'
                                })
                                object_count += 1
                
                if method == 'blob' or method == 'combined':
                    # Blob-based object detection
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    blurred = cv2.GaussianBlur(gray, (9, 9), 0)
                    
                    # Simple blob detector
                    params_blob = cv2.SimpleBlobDetector_Params()
                    params_blob.filterByArea = True
                    params_blob.minArea = min_object_area
                    params_blob.maxArea = max_object_area
                    params_blob.filterByCircularity = False
                    params_blob.filterByConvexity = False
                    params_blob.filterByInertia = False
                    
                    detector = cv2.SimpleBlobDetector_create(params_blob)
                    keypoints = detector.detect(blurred)
                    
                    for kp in keypoints:
                        x, y = int(kp.pt[0]), int(kp.pt[1])
                        size = int(kp.size)
                        w = h = size
                        objects.append({
                            'type': 'object',
                            'x': int(x - w/2),
                            'y': int(y - h/2),
                            'width': w,
                            'height': h,
                            'area': float(np.pi * (size/2)**2),
                            'center': (x, y),
                            'confidence': 0.6,
                            'method': 'blob'
                        })
                        object_count += 1

            # Circle detection for circular objects (counters) on colored backgrounds
            if method == 'circle':
                # Try HoughCircles first (grayscale-based detection)
                detected_objects = self._detect_circles_hough(frame, params, min_object_area, max_object_area, min_confidence)
                objects.extend(detected_objects)
                object_count += len(detected_objects)
                
                # Fallback to HSV color-based detection if HoughCircles finds nothing
                if object_count == 0:
                    detected_objects = self._detect_circles_hsv_fallback(frame, params, min_object_area, max_object_area, min_confidence)
                    objects.extend(detected_objects)
                    object_count += len(detected_objects)

            # Remove duplicates if using combined method
            if method == 'combined' and len(objects) > 0:
                objects = self._merge_nearby_objects(objects, threshold=50)  # Increased threshold
                object_count = len(objects)

            # Keep only the most confident detection (since we expect 1 object at a time)
            if len(objects) > 1:
                objects = sorted(objects, key=lambda x: x.get('confidence', 0), reverse=True)
                objects = [objects[0]]  # Keep only the best one
                object_count = 1

            return {
                'objects_found': object_count > 0,
                'object_count': object_count,
                'objects': objects,
                'method': method,
                'bg_initialized': self.bg_initialized,
                'bg_learning_frames': self.bg_learning_frames,
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
        param2 = params.get('hough_circle_threshold', 30)  # Increased from 20 - higher = fewer false positives, more reliable
        min_radius = int(np.sqrt(min_object_area / np.pi))
        max_radius = int(np.sqrt(max_object_area / np.pi))
        
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
            
            for (x, y, r) in circles:
                # Calculate area
                area = np.pi * r * r
                
                # STRICT filtering: Only accept circles within the exact size range
                if area < min_object_area or area > max_object_area:
                    continue  # Skip circles outside size range
                
                # Validate circle is actually circular by checking the ROI
                # Extract a small region around the circle
                y1 = max(0, y - r - 5)  # Add padding
                y2 = min(frame.shape[0], y + r + 5)
                x1 = max(0, x - r - 5)
                x2 = min(frame.shape[1], x + r + 5)
                
                if y2 - y1 < 20 or x2 - x1 < 20:
                    continue  # Skip if ROI is too small
                
                roi_gray = gray[y1:y2, x1:x2]
                if roi_gray.size == 0:
                    continue
                
                # Apply adaptive threshold to find edges
                roi_thresh = cv2.adaptiveThreshold(roi_gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                                   cv2.THRESH_BINARY_INV, 11, 2)
                
                # Create a mask for the expected circle
                mask = np.zeros(roi_thresh.shape, dtype=np.uint8)
                center_x = x - x1
                center_y = y - y1
                cv2.circle(mask, (center_x, center_y), r, 255, -1)
                
                # Find contours in the masked thresholded region
                masked_roi = cv2.bitwise_and(roi_thresh, mask)
                contours, _ = cv2.findContours(masked_roi, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                if len(contours) > 0:
                    # Get the largest contour
                    largest_contour = max(contours, key=cv2.contourArea)
                    contour_area = cv2.contourArea(largest_contour)
                    
                    # Calculate circularity: 4*pi*area / perimeter^2
                    perimeter = cv2.arcLength(largest_contour, True)
                    if perimeter > 0:
                        circularity = 4 * np.pi * contour_area / (perimeter ** 2)
                        
                        # Only accept if circularity is high (close to 1.0 for perfect circle)
                        if circularity < 0.65:  # Require at least 65% circularity
                            continue
                
                # Calculate confidence based on size (normalized to max area)
                # Higher confidence for circles closer to expected size
                size_ratio = area / max_object_area
                size_confidence = min(size_ratio, 1.0)
                
                # Boost confidence for circles in the middle of the size range
                normalized_area = (area - min_object_area) / (max_object_area - min_object_area)
                # Higher confidence for circles in the middle range
                confidence = 0.6 + (normalized_area * 0.4)  # Range: 0.6 to 1.0
                
                # Only add if meets confidence threshold
                if confidence >= min_confidence:
                    obj = self._create_circle_object(x, y, r, area, confidence)
                    objects.append(obj)
        
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
        """Draw detected circles on frame"""
        annotated = frame.copy()
        
        for obj in objects:
            x, y = obj['x'], obj['y']
            w, h = obj['width'], obj['height']
            
            # Draw bounding box
            cv2.rectangle(annotated, (x, y), (x + w, y + h), color, 2)
            
            # Draw center point
            center = obj['center']
            cv2.circle(annotated, center, 5, color, -1)
            
            # Draw simple label with confidence
            confidence = obj.get('confidence', 0)
            label = f"Counter ({confidence*100:.0f}%)"
            
            cv2.putText(annotated, label, (x, y - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
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

