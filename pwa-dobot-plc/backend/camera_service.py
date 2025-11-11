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
    
    def detect_defects(self, frame: np.ndarray, method: str = 'blob') -> Dict:
        """
        Detect defects in an image frame
        
        Args:
            frame: Input image frame (BGR format)
            method: Detection method ('blob', 'contour', 'edge', 'combined')
            
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
        
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Apply Gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            defects = []
            defect_count = 0
            
            if method == 'blob' or method == 'combined':
                # Blob detection for small defects
                blob_defects = self._detect_blobs(blurred)
                defects.extend(blob_defects)
                defect_count += len(blob_defects)
            
            if method == 'contour' or method == 'combined':
                # Contour-based detection for larger defects
                contour_defects = self._detect_contours(blurred)
                defects.extend(contour_defects)
                defect_count += len(contour_defects)
            
            if method == 'edge' or method == 'combined':
                # Edge-based detection
                edge_defects = self._detect_edges(blurred)
                defects.extend(edge_defects)
                defect_count += len(edge_defects)
            
            # Remove duplicates if using combined method
            if method == 'combined' and len(defects) > 0:
                defects = self._merge_nearby_defects(defects, threshold=20)
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
    
    def _detect_blobs(self, gray: np.ndarray) -> List[Dict]:
        """Detect defects using blob detection"""
        defects = []
        
        try:
            # Apply adaptive threshold
            thresh = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY_INV, 11, 2
            )
            
            # Morphological operations to clean up
            kernel = np.ones((3, 3), np.uint8)
            thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
            
            # Find contours
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                # Filter small noise
                if 10 < area < 5000:
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
    
    def _detect_contours(self, gray: np.ndarray) -> List[Dict]:
        """Detect defects using contour analysis"""
        defects = []
        
        try:
            # Apply Canny edge detection
            edges = cv2.Canny(gray, 50, 150)
            
            # Dilate edges to connect nearby edges
            kernel = np.ones((3, 3), np.uint8)
            dilated = cv2.dilate(edges, kernel, iterations=1)
            
            # Find contours
            contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                # Filter based on area
                if 50 < area < 10000:
                    x, y, w, h = cv2.boundingRect(contour)
                    # Calculate aspect ratio to filter elongated defects
                    aspect_ratio = float(w) / h if h > 0 else 0
                    if 0.2 < aspect_ratio < 5.0:  # Reasonable aspect ratio
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
    
    def _detect_edges(self, gray: np.ndarray) -> List[Dict]:
        """Detect defects using edge detection"""
        defects = []
        
        try:
            # Apply Canny edge detection with different thresholds
            edges = cv2.Canny(gray, 30, 100)
            
            # Find lines using HoughLinesP
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=50, 
                                   minLineLength=30, maxLineGap=10)
            
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
                            if dist < 30:
                                group.append((x1, y1, x2, y2))
                                grouped = True
                                break
                        if grouped:
                            break
                    
                    if not grouped:
                        line_groups.append([(x1, y1, x2, y2)])
                
                # Convert line groups to defect regions
                for group in line_groups:
                    if len(group) >= 2:  # At least 2 lines to form a defect
                        xs = [x for line in group for x in [line[0], line[2]]]
                        ys = [y for line in group for y in [line[1], line[3]]]
                        x, y = min(xs), min(ys)
                        w, h = max(xs) - x, max(ys) - y
                        
                        if w > 10 and h > 10:
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

