"""
Face detection module for optional presence verification.
"""
import cv2
import numpy as np
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class FaceDetector:
    """
    Face-based presence verification using OpenCV.
    Detects faces via camera to determine user presence.
    """
    
    def __init__(self, camera_index: int = 0, cascade_path: Optional[str] = None):
        """
        Initialize face detector.
        
        Args:
            camera_index: Index of camera device to use
            cascade_path: Path to Haar cascade XML file (uses default if None)
        """
        self.camera_index = camera_index
        self.camera = None
        self.enabled = False
        
        # Load Haar cascade for face detection
        if cascade_path:
            self.face_cascade = cv2.CascadeClassifier(cascade_path)
        else:
            # Use default OpenCV cascade
            cascade_file = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            self.face_cascade = cv2.CascadeClassifier(cascade_file)
            
        if self.face_cascade.empty():
            logger.warning("Failed to load face cascade classifier")
            self.enabled = False
        else:
            logger.info("Face detector initialized successfully")
            
    def enable(self) -> bool:
        """
        Enable face detection by opening camera.
        
        Returns:
            True if camera opened successfully
        """
        if self.camera is not None:
            return True
            
        try:
            self.camera = cv2.VideoCapture(self.camera_index)
            if self.camera.isOpened():
                self.enabled = True
                logger.info(f"Camera {self.camera_index} opened successfully")
                return True
            else:
                logger.warning(f"Failed to open camera {self.camera_index}")
                self.enabled = False
                return False
        except Exception as e:
            logger.error(f"Error enabling camera: {e}")
            self.enabled = False
            return False
    
    def disable(self):
        """Disable face detection and release camera."""
        if self.camera is not None:
            self.camera.release()
            self.camera = None
        self.enabled = False
        logger.info("Face detector disabled")
    
    def detect_presence(self, timeout: float = 2.0) -> Tuple[bool, float]:
        """
        Detect user presence via face detection.
        
        Args:
            timeout: Maximum time to attempt detection (seconds)
            
        Returns:
            Tuple of (presence detected, confidence score 0-100)
        """
        if not self.enabled or self.camera is None:
            # If detector is disabled, return neutral confidence
            return False, 50.0
        
        try:
            # Capture frame
            ret, frame = self.camera.read()
            if not ret or frame is None:
                logger.warning("Failed to capture frame from camera")
                return False, 0.0
            
            # Convert to grayscale for detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30)
            )
            
            if len(faces) > 0:
                # Calculate confidence based on face size and count
                largest_face = max(faces, key=lambda f: f[2] * f[3])
                face_area = largest_face[2] * largest_face[3]
                frame_area = frame.shape[0] * frame.shape[1]
                area_ratio = face_area / frame_area
                
                # Confidence increases with face size (up to reasonable limit)
                confidence = min(100.0, area_ratio * 5000)
                confidence = max(60.0, confidence)  # Minimum confidence if face detected
                
                logger.debug(f"Face detected: {len(faces)} face(s), confidence: {confidence:.1f}")
                return True, confidence
            else:
                logger.debug("No face detected")
                return False, 0.0
                
        except Exception as e:
            logger.error(f"Error during face detection: {e}")
            return False, 0.0
    
    def get_presence_confidence(self, samples: int = 3) -> float:
        """
        Get average presence confidence over multiple samples.
        
        Args:
            samples: Number of detection samples to average
            
        Returns:
            Average confidence score (0-100)
        """
        if not self.enabled:
            return 50.0  # Neutral confidence when disabled
        
        confidences = []
        for _ in range(samples):
            present, confidence = self.detect_presence()
            confidences.append(confidence)
        
        avg_confidence = sum(confidences) / len(confidences) if confidences else 50.0
        logger.debug(f"Average presence confidence: {avg_confidence:.1f}")
        return avg_confidence
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        self.disable()
