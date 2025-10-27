"""
Face Detector - Detects and extracts faces from camera frames

Uses face_recognition library (built on dlib) for reliable face detection! 🔍
"""

import face_recognition
import logging
import numpy as np
from typing import List, Tuple, Optional
import cv2


logger = logging.getLogger(__name__)


class FaceDetector:
    """
    Detects faces in images and extracts face encodings.
    
    This is your AI-powered bouncer babe! 🤖🔒
    """
    
    def __init__(self, model: str = "hog"):
        """
        Initialize face detector.
        
        Args:
            model: Detection model to use
                   'hog' = faster but less accurate (CPU-friendly)
                   'cnn' = slower but more accurate (needs GPU)
        """
        self.model = model
        self.detection_count = 0
        logger.info(f"🔍 Face detector initialized (model: {model})")
    
    def detect_faces(
        self, 
        image: np.ndarray,
        number_of_times_to_upsample: int = 1
    ) -> List[Tuple[int, int, int, int]]:
        """
        Detect all faces in an image.
        
        Args:
            image: BGR image from OpenCV
            number_of_times_to_upsample: How many times to upsample image for detection
                                          (higher = detect smaller faces, but slower)
        
        Returns:
            List of face locations as (top, right, bottom, left) tuples
        """
        try:
            # Convert BGR (OpenCV) to RGB (face_recognition)
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Detect faces
            face_locations = face_recognition.face_locations(
                rgb_image,
                number_of_times_to_upsample=number_of_times_to_upsample,
                model=self.model
            )
            
            self.detection_count += 1
            
            if face_locations:
                logger.debug(f"👤 Detected {len(face_locations)} face(s)")
            
            return face_locations
            
        except Exception as e:
            logger.error(f"❌ Face detection failed: {e}")
            return []
    
    def extract_face_encodings(
        self, 
        image: np.ndarray,
        face_locations: Optional[List[Tuple[int, int, int, int]]] = None,
        num_jitters: int = 1
    ) -> List[np.ndarray]:
        """
        Extract face encodings (128-dimensional vectors) from detected faces.
        
        These encodings are like facial fingerprints babe! 🔢
        
        Args:
            image: BGR image from OpenCV
            face_locations: Pre-detected face locations (or None to auto-detect)
            num_jitters: How many times to re-sample face for encoding
                         (higher = more accurate, but slower)
        
        Returns:
            List of face encoding arrays (128-dim vectors)
        """
        try:
            # Convert BGR to RGB
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Auto-detect faces if not provided
            if face_locations is None:
                face_locations = self.detect_faces(image)
            
            if not face_locations:
                return []
            
            # Extract encodings for each face
            encodings = face_recognition.face_encodings(
                rgb_image,
                known_face_locations=face_locations,
                num_jitters=num_jitters
            )
            
            logger.debug(f"🔢 Extracted {len(encodings)} face encoding(s)")
            return encodings
            
        except Exception as e:
            logger.error(f"❌ Face encoding extraction failed: {e}")
            return []
    
    def detect_and_encode(
        self,
        image: np.ndarray,
        num_jitters: int = 1
    ) -> List[Tuple[Tuple[int, int, int, int], np.ndarray]]:
        """
        One-shot: detect faces AND extract encodings.
        
        Args:
            image: BGR image from OpenCV
            num_jitters: Encoding quality (1=fast, 10=accurate)
        
        Returns:
            List of (face_location, face_encoding) tuples
        """
        # First detect all faces
        face_locations = self.detect_faces(image)
        
        if not face_locations:
            return []
        
        # Then extract encodings
        encodings = self.extract_face_encodings(
            image, 
            face_locations=face_locations,
            num_jitters=num_jitters
        )
        
        # Zip them together
        return list(zip(face_locations, encodings))
    
    def draw_face_boxes(
        self, 
        image: np.ndarray,
        face_locations: List[Tuple[int, int, int, int]],
        labels: Optional[List[str]] = None,
        color: Tuple[int, int, int] = (0, 255, 0)
    ) -> np.ndarray:
        """
        Draw bounding boxes around detected faces.
        
        Perfect for debugging and dashboard display! 📦
        
        Args:
            image: BGR image to draw on (will be copied)
            face_locations: List of (top, right, bottom, left) tuples
            labels: Optional labels for each face (e.g., "Owner", "Unknown")
            color: Box color as (B, G, R) tuple
        
        Returns:
            Image with face boxes drawn
        """
        output = image.copy()
        
        for i, (top, right, bottom, left) in enumerate(face_locations):
            # Draw rectangle
            cv2.rectangle(output, (left, top), (right, bottom), color, 2)
            
            # Add label if provided
            if labels and i < len(labels):
                label = labels[i]
                
                # Draw label background
                label_y = top - 10 if top - 10 > 10 else top + 25
                cv2.rectangle(
                    output, 
                    (left, label_y - 20), 
                    (right, label_y), 
                    color, 
                    cv2.FILLED
                )
                
                # Draw label text
                cv2.putText(
                    output,
                    label,
                    (left + 6, label_y - 6),
                    cv2.FONT_HERSHEY_DUPLEX,
                    0.6,
                    (255, 255, 255),
                    1
                )
        
        return output
    
    def get_stats(self) -> dict:
        """Get detection statistics."""
        return {
            "model": self.model,
            "total_detections": self.detection_count
        }
