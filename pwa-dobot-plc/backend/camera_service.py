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
                # Optimized for detecting large circles on blue background
                # Convert to HSV to isolate blue background
                hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

                # Get HSV parameters (tunable via frontend sliders)
                hsv_hue_min = params.get('hsv_hue_min', 90)
                hsv_hue_max = params.get('hsv_hue_max', 130)

                # Define blue color range (adjust these for your specific blue)
                lower_blue = np.array([hsv_hue_min, 50, 50])  # Lower bound of blue in HSV
                upper_blue = np.array([hsv_hue_max, 255, 255])  # Upper bound of blue in HSV

                # Create mask for blue background
                blue_mask = cv2.inRange(hsv, lower_blue, upper_blue)

                # Invert to get objects (non-blue regions)
                object_mask = cv2.bitwise_not(blue_mask)

                # Apply morphological operations to clean up
                kernel_size = params.get('morphological_kernel_size', 7)
                kernel = np.ones((kernel_size, kernel_size), np.uint8)
                object_mask = cv2.morphologyEx(object_mask, cv2.MORPH_CLOSE, kernel)
                object_mask = cv2.morphologyEx(object_mask, cv2.MORPH_OPEN, kernel)

                # Find contours
                contours, _ = cv2.findContours(object_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                for contour in contours:
                    area = cv2.contourArea(contour)
                    if min_object_area < area < max_object_area:
                        # Fit a circle to the contour
                        (x, y), radius = cv2.minEnclosingCircle(contour)

                        # Calculate circularity (how close to a perfect circle)
                        perimeter = cv2.arcLength(contour, True)
                        if perimeter > 0:
                            circularity = 4 * np.pi * area / (perimeter ** 2)
                        else:
                            circularity = 0

                        # Only accept circular objects (circularity close to 1.0)
                        min_circularity = params.get('min_circularity', 0.6)
                        if circularity >= min_circularity:
                            # Get bounding box
                            x_int, y_int, w, h = cv2.boundingRect(contour)

                            # Calculate aspect ratio
                            aspect_ratio = float(w) / h if h > 0 else 0

                            # Check if aspect ratio is close to 1 (circular)
                            if 0.7 < aspect_ratio < 1.3:  # Allow some tolerance
                                # Calculate confidence based on circularity and size
                                size_confidence = min(area / max_object_area, 1.0)
                                confidence = (circularity * 0.7 + size_confidence * 0.3)

                                if confidence >= min_confidence:
                                    objects.append({
                                        'type': 'circle',
                                        'x': int(x_int),
                                        'y': int(y_int),
                                        'width': int(w),
                                        'height': int(h),
                                        'area': float(area),
                                        'center': (int(x), int(y)),
                                        'radius': int(radius),
                                        'circularity': round(circularity, 2),
                                        'confidence': round(confidence, 2),
                                        'method': 'circle',
                                        'aspect_ratio': round(aspect_ratio, 2)
                                    })
                                    object_count += 1

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
    
    def draw_objects(self, frame: np.ndarray, objects: List[Dict], color: Tuple[int, int, int] = (0, 255, 0)) -> np.ndarray:
        """Draw detected objects on frame"""
        annotated = frame.copy()
        
        for obj in objects:
            x, y = obj['x'], obj['y']
            w, h = obj['width'], obj['height']
            
            # Draw bounding box
            cv2.rectangle(annotated, (x, y), (x + w, y + h), color, 2)
            
            # Draw center point
            center = obj['center']
            cv2.circle(annotated, center, 5, color, -1)
            
            # Draw label
            label = f"Object {obj.get('confidence', 0):.2f}"
            cv2.putText(annotated, label, (x, y - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        return annotated
    
    # DEFECT DETECTION COMMENTED OUT - Focus on object/counter detection first
    def detect_defects(self, frame: np.ndarray, method: str = 'blob', params: Optional[Dict] = None) -> Dict:
        """
        Detect defects in an image frame
        
        COMMENTED OUT - Focus on object/counter detection first
        """
        # Return empty results since defect detection is disabled
        return {
            'defects_found': False,
            'defect_count': 0,
            'defects': [],
            'confidence': 0.0,
            'method': method,
            'timestamp': time.time(),
            'note': 'Defect detection is currently disabled'
        }
    
    # Original defect detection code commented out below:
    # """
    #     Detect defects in an image frame
    #     
    #     Args:
    #         frame: Input image frame (BGR format)
    #         method: Detection method ('blob', 'contour', 'edge', 'combined')
    #         params: Optional detection parameters dictionary:
    #             - min_area: Minimum defect area in pixels (default: varies by method)
    #             - max_area: Maximum defect area in pixels (default: varies by method)
    #             - blob_min_area: Blob-specific min area (default: 10)
    #             - blob_max_area: Blob-specific max area (default: 5000)
    #             - contour_min_area: Contour-specific min area (default: 50)
    #             - contour_max_area: Contour-specific max area (default: 10000)
    #             - canny_low: Canny edge detection low threshold (default: 50)
    #             - canny_high: Canny edge detection high threshold (default: 150)
    #             - edge_canny_low: Edge detection Canny low threshold (default: 30)
    #             - edge_canny_high: Edge detection Canny high threshold (default: 100)
    #             - hough_threshold: Hough line transform threshold (default: 50)
    #             - merge_threshold: Distance threshold for merging defects (default: 20)
    #             - gaussian_blur: Gaussian blur kernel size (default: 5)
    #             - adaptive_thresh_block: Adaptive threshold block size (default: 11)
    #             - adaptive_thresh_c: Adaptive threshold constant (default: 2)
    #         
    #     Returns:
    #         Dictionary with detection results
    #     """
    # if frame is None:
    #     return {
    #         'defects_found': False,
    #         'defect_count': 0,
    #         'defects': [],
    #         'confidence': 0.0,
    #         'error': 'No frame provided'
    #     }
    # 
    # # Default parameters
    # if params is None:
    #     params = {}
    # 
    # # Extract parameters with defaults
    # blob_min_area = params.get('blob_min_area', params.get('min_area', 10))
    # blob_max_area = params.get('blob_max_area', params.get('max_area', 5000))
    # contour_min_area = params.get('contour_min_area', params.get('min_area', 50))
    # contour_max_area = params.get('contour_max_area', params.get('max_area', 10000))
    # canny_low = params.get('canny_low', 50)
    # canny_high = params.get('canny_high', 150)
    # edge_canny_low = params.get('edge_canny_low', 30)
    # edge_canny_high = params.get('edge_canny_high', 100)
    # hough_threshold = params.get('hough_threshold', 50)
    # merge_threshold = params.get('merge_threshold', 20)
    # gaussian_blur = params.get('gaussian_blur', 5)
    # adaptive_thresh_block = params.get('adaptive_thresh_block', 11)
    # adaptive_thresh_c = params.get('adaptive_thresh_c', 2)
    # # Edge detection additional parameters
    # min_line_length = params.get('min_line_length', 30)
    # max_line_gap = params.get('max_line_gap', 10)
    # line_grouping_distance = params.get('line_grouping_distance', 30)
    # min_lines_per_defect = params.get('min_lines_per_defect', 2)
    # min_edge_defect_size = params.get('min_edge_defect_size', 10)
    # # Contour detection additional parameters
    # aspect_ratio_min = params.get('aspect_ratio_min', 0.2)
    # aspect_ratio_max = params.get('aspect_ratio_max', 5.0)
    # dilation_iterations = params.get('dilation_iterations', 1)
    # morphological_kernel_size = params.get('morphological_kernel_size', 3)
    # 
    # try:
    #     # Convert to grayscale
    #     gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    #     
    #     # Apply Gaussian blur to reduce noise
    #     blur_size = gaussian_blur if gaussian_blur % 2 == 1 else gaussian_blur + 1
    #     blurred = cv2.GaussianBlur(gray, (blur_size, blur_size), 0)
    #     
    #     defects = []
    #     defect_count = 0
    #     
    #     if method == 'blob' or method == 'combined':
    #         # Blob detection for small defects
    #         blob_defects = self._detect_blobs(blurred, min_area=blob_min_area, max_area=blob_max_area,
    #                                           adaptive_block=adaptive_thresh_block, adaptive_c=adaptive_thresh_c,
    #                                           kernel_size=morphological_kernel_size)
    #         defects.extend(blob_defects)
    #         defect_count += len(blob_defects)
    #     
    #     if method == 'contour' or method == 'combined':
    #         # Contour-based detection for larger defects
    #         contour_defects = self._detect_contours(blurred, min_area=contour_min_area, max_area=contour_max_area,
    #                                                  canny_low=canny_low, canny_high=canny_high,
    #                                                  aspect_ratio_min=aspect_ratio_min, aspect_ratio_max=aspect_ratio_max,
    #                                                  dilation_iterations=dilation_iterations, kernel_size=morphological_kernel_size)
    #         defects.extend(contour_defects)
    #         defect_count += len(contour_defects)
    #     
    #     if method == 'edge' or method == 'combined':
    #         # Edge-based detection
    #         edge_defects = self._detect_edges(blurred, canny_low=edge_canny_low, canny_high=edge_canny_high,
    #                                           hough_threshold=hough_threshold, min_line_length=min_line_length,
    #                                           max_line_gap=max_line_gap, line_grouping_distance=line_grouping_distance,
    #                                           min_lines_per_defect=min_lines_per_defect, min_defect_size=min_edge_defect_size)
    #         defects.extend(edge_defects)
    #         defect_count += len(edge_defects)
    #     
    #     # Remove duplicates if using combined method
    #     if method == 'combined' and len(defects) > 0:
    #         defects = self._merge_nearby_defects(defects, threshold=merge_threshold)
    #         defect_count = len(defects)
    #     
    #     # Calculate confidence based on defect characteristics
    #     confidence = self._calculate_confidence(defects, frame.shape)
    #     
    #     return {
    #         'defects_found': defect_count > 0,
    #         'defect_count': defect_count,
    #         'defects': defects,
    #         'confidence': confidence,
    #         'method': method,
    #         'timestamp': time.time()
    #     }
    #     
    # except Exception as e:
    #     logger.error(f"Error in defect detection: {e}")
    #     return {
    #         'defects_found': False,
    #         'defect_count': 0,
    #         'defects': [],
    #         'confidence': 0.0,
    #         'error': str(e)
    #     }
    
    # DEFECT DETECTION HELPER METHODS COMMENTED OUT
    # def _detect_blobs(self, gray: np.ndarray, min_area: int = 10, max_area: int = 5000,
    #                  adaptive_block: int = 11, adaptive_c: int = 2, kernel_size: int = 3) -> List[Dict]:
    #     """Detect defects using blob detection"""
    #     defects = []
    #     
    #     try:
    #         # Apply adaptive threshold
    #         block_size = adaptive_block if adaptive_block % 2 == 1 else adaptive_block + 1
    #         thresh = cv2.adaptiveThreshold(
    #             gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
    #             cv2.THRESH_BINARY_INV, block_size, adaptive_c
    #         )
    #         
    #         # Morphological operations to clean up
    #         kernel = np.ones((kernel_size, kernel_size), np.uint8)
    #         thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    #         thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
    #         
    #         # Find contours
    #         contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    #         
    #         for contour in contours:
    #             area = cv2.contourArea(contour)
    #             # Filter based on area parameters
    #             if min_area < area < max_area:
    #                 x, y, w, h = cv2.boundingRect(contour)
    #                 defects.append({
    #                     'type': 'blob',
    #                     'x': int(x),
    #                     'y': int(y),
    #                     'width': int(w),
    #                     'height': int(h),
    #                     'area': float(area),
    #                     'center': (int(x + w/2), int(y + h/2))
    #                 })
    #     except Exception as e:
    #         logger.error(f"Error in blob detection: {e}")
    #     
    #     return defects
    
    def _detect_blobs(self, gray: np.ndarray, min_area: int = 10, max_area: int = 5000,
                     adaptive_block: int = 11, adaptive_c: int = 2, kernel_size: int = 3) -> List[Dict]:
        """Stub - defect detection disabled"""
        return []
    
    # def _detect_contours(self, gray: np.ndarray, min_area: int = 50, max_area: int = 10000,
    #                     canny_low: int = 50, canny_high: int = 150, aspect_ratio_min: float = 0.2,
    #                     aspect_ratio_max: float = 5.0, dilation_iterations: int = 1, kernel_size: int = 3) -> List[Dict]:
    #     """Detect defects using contour analysis"""
    #     ... (commented out)
    
    def _detect_contours(self, gray: np.ndarray, min_area: int = 50, max_area: int = 10000,
                        canny_low: int = 50, canny_high: int = 150, aspect_ratio_min: float = 0.2,
                        aspect_ratio_max: float = 5.0, dilation_iterations: int = 1, kernel_size: int = 3) -> List[Dict]:
        """Stub - defect detection disabled"""
        return []
    
    # def _detect_edges(self, gray: np.ndarray, canny_low: int = 30, canny_high: int = 100,
    #                  hough_threshold: int = 50, min_line_length: int = 30, max_line_gap: int = 10,
    #                  line_grouping_distance: int = 30, min_lines_per_defect: int = 2, min_defect_size: int = 10) -> List[Dict]:
    #     """Detect defects using edge detection"""
    #     ... (commented out)
    
    def _detect_edges(self, gray: np.ndarray, canny_low: int = 30, canny_high: int = 100,
                     hough_threshold: int = 50, min_line_length: int = 30, max_line_gap: int = 10,
                     line_grouping_distance: int = 30, min_lines_per_defect: int = 2, min_defect_size: int = 10) -> List[Dict]:
        """Stub - defect detection disabled"""
        return []
    
    # def _merge_nearby_defects(self, defects: List[Dict], threshold: int = 20) -> List[Dict]:
    #     """Merge defects that are close to each other"""
    #     ... (commented out)
    
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

