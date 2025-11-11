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
                
                # Warm up camera
                for _ in range(5):
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
    
    def detect_defects(self, frame: np.ndarray, method: str = 'blob', params: Optional[Dict] = None) -> Dict:
        """
        Detect defects in an image frame
        
        Args:
            frame: Input image frame (BGR format)
            method: Detection method ('blob', 'contour', 'edge', 'combined')
            params: Optional detection parameters dictionary:
                - min_area: Minimum defect area in pixels (default: varies by method)
                - max_area: Maximum defect area in pixels (default: varies by method)
                - blob_min_area: Blob-specific min area (default: 10)
                - blob_max_area: Blob-specific max area (default: 5000)
                - contour_min_area: Contour-specific min area (default: 50)
                - contour_max_area: Contour-specific max area (default: 10000)
                - canny_low: Canny edge detection low threshold (default: 50)
                - canny_high: Canny edge detection high threshold (default: 150)
                - edge_canny_low: Edge detection Canny low threshold (default: 30)
                - edge_canny_high: Edge detection Canny high threshold (default: 100)
                - hough_threshold: Hough line transform threshold (default: 50)
                - merge_threshold: Distance threshold for merging defects (default: 20)
                - gaussian_blur: Gaussian blur kernel size (default: 5)
                - adaptive_thresh_block: Adaptive threshold block size (default: 11)
                - adaptive_thresh_c: Adaptive threshold constant (default: 2)
            
        Returns:
            Dictionary with detection results
        """
        if frame is None:
            return {
                'defects_found': False,
                'defect_count': 0,
                'defects': [],
                'confidence': 0.0,
                'error': 'No frame provided'
            }
        
        # Default parameters
        if params is None:
            params = {}
        
        # Extract parameters with defaults
        blob_min_area = params.get('blob_min_area', params.get('min_area', 10))
        blob_max_area = params.get('blob_max_area', params.get('max_area', 5000))
        contour_min_area = params.get('contour_min_area', params.get('min_area', 50))
        contour_max_area = params.get('contour_max_area', params.get('max_area', 10000))
        canny_low = params.get('canny_low', 50)
        canny_high = params.get('canny_high', 150)
        edge_canny_low = params.get('edge_canny_low', 30)
        edge_canny_high = params.get('edge_canny_high', 100)
        hough_threshold = params.get('hough_threshold', 50)
        merge_threshold = params.get('merge_threshold', 20)
        gaussian_blur = params.get('gaussian_blur', 5)
        adaptive_thresh_block = params.get('adaptive_thresh_block', 11)
        adaptive_thresh_c = params.get('adaptive_thresh_c', 2)
        # Edge detection additional parameters
        min_line_length = params.get('min_line_length', 30)
        max_line_gap = params.get('max_line_gap', 10)
        line_grouping_distance = params.get('line_grouping_distance', 30)
        min_lines_per_defect = params.get('min_lines_per_defect', 2)
        min_edge_defect_size = params.get('min_edge_defect_size', 10)
        # Contour detection additional parameters
        aspect_ratio_min = params.get('aspect_ratio_min', 0.2)
        aspect_ratio_max = params.get('aspect_ratio_max', 5.0)
        dilation_iterations = params.get('dilation_iterations', 1)
        morphological_kernel_size = params.get('morphological_kernel_size', 3)
        
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Apply Gaussian blur to reduce noise
            blur_size = gaussian_blur if gaussian_blur % 2 == 1 else gaussian_blur + 1
            blurred = cv2.GaussianBlur(gray, (blur_size, blur_size), 0)
            
            defects = []
            defect_count = 0
            
            if method == 'blob' or method == 'combined':
                # Blob detection for small defects
                blob_defects = self._detect_blobs(blurred, min_area=blob_min_area, max_area=blob_max_area,
                                                  adaptive_block=adaptive_thresh_block, adaptive_c=adaptive_thresh_c,
                                                  kernel_size=morphological_kernel_size)
                defects.extend(blob_defects)
                defect_count += len(blob_defects)
            
            if method == 'contour' or method == 'combined':
                # Contour-based detection for larger defects
                contour_defects = self._detect_contours(blurred, min_area=contour_min_area, max_area=contour_max_area,
                                                         canny_low=canny_low, canny_high=canny_high,
                                                         aspect_ratio_min=aspect_ratio_min, aspect_ratio_max=aspect_ratio_max,
                                                         dilation_iterations=dilation_iterations, kernel_size=morphological_kernel_size)
                defects.extend(contour_defects)
                defect_count += len(contour_defects)
            
            if method == 'edge' or method == 'combined':
                # Edge-based detection
                edge_defects = self._detect_edges(blurred, canny_low=edge_canny_low, canny_high=edge_canny_high,
                                                  hough_threshold=hough_threshold, min_line_length=min_line_length,
                                                  max_line_gap=max_line_gap, line_grouping_distance=line_grouping_distance,
                                                  min_lines_per_defect=min_lines_per_defect, min_defect_size=min_edge_defect_size)
                defects.extend(edge_defects)
                defect_count += len(edge_defects)
            
            # Remove duplicates if using combined method
            if method == 'combined' and len(defects) > 0:
                defects = self._merge_nearby_defects(defects, threshold=merge_threshold)
                defect_count = len(defects)
            
            # Calculate confidence based on defect characteristics
            confidence = self._calculate_confidence(defects, frame.shape)
            
            return {
                'defects_found': defect_count > 0,
                'defect_count': defect_count,
                'defects': defects,
                'confidence': confidence,
                'method': method,
                'timestamp': time.time()
            }
            
        except Exception as e:
            logger.error(f"Error in defect detection: {e}")
            return {
                'defects_found': False,
                'defect_count': 0,
                'defects': [],
                'confidence': 0.0,
                'error': str(e)
            }
    
    def _detect_blobs(self, gray: np.ndarray, min_area: int = 10, max_area: int = 5000,
                     adaptive_block: int = 11, adaptive_c: int = 2, kernel_size: int = 3) -> List[Dict]:
        """Detect defects using blob detection"""
        defects = []
        
        try:
            # Apply adaptive threshold
            block_size = adaptive_block if adaptive_block % 2 == 1 else adaptive_block + 1
            thresh = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY_INV, block_size, adaptive_c
            )
            
            # Morphological operations to clean up
            kernel = np.ones((kernel_size, kernel_size), np.uint8)
            thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
            
            # Find contours
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                # Filter based on area parameters
                if min_area < area < max_area:
                    x, y, w, h = cv2.boundingRect(contour)
                    defects.append({
                        'type': 'blob',
                        'x': int(x),
                        'y': int(y),
                        'width': int(w),
                        'height': int(h),
                        'area': float(area),
                        'center': (int(x + w/2), int(y + h/2))
                    })
        except Exception as e:
            logger.error(f"Error in blob detection: {e}")
        
        return defects
    
    def _detect_contours(self, gray: np.ndarray, min_area: int = 50, max_area: int = 10000,
                        canny_low: int = 50, canny_high: int = 150, aspect_ratio_min: float = 0.2,
                        aspect_ratio_max: float = 5.0, dilation_iterations: int = 1, kernel_size: int = 3) -> List[Dict]:
        """Detect defects using contour analysis"""
        defects = []
        
        try:
            # Apply Canny edge detection
            edges = cv2.Canny(gray, canny_low, canny_high)
            
            # Dilate edges to connect nearby edges
            kernel = np.ones((kernel_size, kernel_size), np.uint8)
            dilated = cv2.dilate(edges, kernel, iterations=dilation_iterations)
            
            # Find contours
            contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                # Filter based on area parameters
                if min_area < area < max_area:
                    x, y, w, h = cv2.boundingRect(contour)
                    # Calculate aspect ratio to filter elongated defects
                    aspect_ratio = float(w) / h if h > 0 else 0
                    if aspect_ratio_min < aspect_ratio < aspect_ratio_max:
                        defects.append({
                            'type': 'contour',
                            'x': int(x),
                            'y': int(y),
                            'width': int(w),
                            'height': int(h),
                            'area': float(area),
                            'center': (int(x + w/2), int(y + h/2)),
                            'aspect_ratio': aspect_ratio
                        })
        except Exception as e:
            logger.error(f"Error in contour detection: {e}")
        
        return defects
    
    def _detect_edges(self, gray: np.ndarray, canny_low: int = 30, canny_high: int = 100,
                     hough_threshold: int = 50, min_line_length: int = 30, max_line_gap: int = 10,
                     line_grouping_distance: int = 30, min_lines_per_defect: int = 2, min_defect_size: int = 10) -> List[Dict]:
        """Detect defects using edge detection"""
        defects = []
        
        try:
            # Apply Canny edge detection with different thresholds
            edges = cv2.Canny(gray, canny_low, canny_high)
            
            # Find lines using HoughLinesP
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=hough_threshold, 
                                   minLineLength=min_line_length, maxLineGap=max_line_gap)
            
            if lines is not None:
                # Group nearby lines
                line_groups = []
                for line in lines:
                    x1, y1, x2, y2 = line[0]
                    # Check if line is near any existing group
                    grouped = False
                    for group in line_groups:
                        for gx1, gy1, gx2, gy2 in group:
                            dist = min(
                                np.sqrt((x1-gx1)**2 + (y1-gy1)**2),
                                np.sqrt((x1-gx2)**2 + (y1-gy2)**2),
                                np.sqrt((x2-gx1)**2 + (y2-gy1)**2),
                                np.sqrt((x2-gx2)**2 + (y2-gy2)**2)
                            )
                            if dist < line_grouping_distance:
                                group.append((x1, y1, x2, y2))
                                grouped = True
                                break
                        if grouped:
                            break
                    
                    if not grouped:
                        line_groups.append([(x1, y1, x2, y2)])
                
                # Convert line groups to defect regions
                for group in line_groups:
                    if len(group) >= min_lines_per_defect:  # Configurable minimum lines
                        xs = [x for line in group for x in [line[0], line[2]]]
                        ys = [y for line in group for y in [line[1], line[3]]]
                        x, y = min(xs), min(ys)
                        w, h = max(xs) - x, max(ys) - y
                        
                        if w > min_defect_size and h > min_defect_size:
                            defects.append({
                                'type': 'edge',
                                'x': int(x),
                                'y': int(y),
                                'width': int(w),
                                'height': int(h),
                                'area': float(w * h),
                                'center': (int(x + w/2), int(y + h/2))
                            })
        except Exception as e:
            logger.error(f"Error in edge detection: {e}")
        
        return defects
    
    def _merge_nearby_defects(self, defects: List[Dict], threshold: int = 20) -> List[Dict]:
        """Merge defects that are close to each other"""
        if len(defects) == 0:
            return []
        
        merged = []
        used = set()
        
        for i, defect in enumerate(defects):
            if i in used:
                continue
            
            center = defect['center']
            group = [defect]
            used.add(i)
            
            # Find nearby defects
            for j, other in enumerate(defects):
                if j in used or i == j:
                    continue
                
                other_center = other['center']
                distance = np.sqrt(
                    (center[0] - other_center[0])**2 + 
                    (center[1] - other_center[1])**2
                )
                
                if distance < threshold:
                    group.append(other)
                    used.add(j)
            
            # Merge group into single defect
            if len(group) > 1:
                xs = [d['x'] for d in group]
                ys = [d['y'] for d in group]
                widths = [d['width'] for d in group]
                heights = [d['height'] for d in group]
                
                x = min(xs)
                y = min(ys)
                w = max(x + w for x, w in zip(xs, widths)) - x
                h = max(y + h for y, h in zip(ys, heights)) - y
                
                merged.append({
                    'type': 'merged',
                    'x': int(x),
                    'y': int(y),
                    'width': int(w),
                    'height': int(h),
                    'area': sum(d['area'] for d in group),
                    'center': (int(x + w/2), int(y + h/2)),
                    'count': len(group)
                })
            else:
                merged.append(defect)
        
        return merged
    
    def _calculate_confidence(self, defects: List[Dict], frame_shape: Tuple[int, int, int]) -> float:
        """Calculate confidence score for defect detection"""
        if len(defects) == 0:
            return 0.0
        
        total_area = frame_shape[0] * frame_shape[1]
        defect_area = sum(d['area'] for d in defects)
        
        # Confidence based on defect coverage and count
        coverage_ratio = defect_area / total_area
        count_factor = min(len(defects) / 10.0, 1.0)  # Normalize to max 10 defects
        
        # Combine factors
        confidence = min(coverage_ratio * 100 + count_factor * 20, 100.0)
        
        return round(confidence, 2)
    
    def draw_defects(self, frame: np.ndarray, defects: List[Dict]) -> np.ndarray:
        """
        Draw defect annotations on frame
        
        Args:
            frame: Input frame
            defects: List of defect dictionaries
            
        Returns:
            Frame with defect annotations
        """
        annotated = frame.copy()
        
        for defect in defects:
            x = defect['x']
            y = defect['y']
            w = defect['width']
            h = defect['height']
            center = defect['center']
            
            # Draw bounding box
            cv2.rectangle(annotated, (x, y), (x + w, y + h), (0, 0, 255), 2)
            
            # Draw center point
            cv2.circle(annotated, center, 5, (0, 255, 0), -1)
            
            # Draw label
            label = f"{defect.get('type', 'defect')}"
            if 'area' in defect:
                label += f" {defect['area']:.0f}"
            
            cv2.putText(annotated, label, (x, y - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        
        return annotated

