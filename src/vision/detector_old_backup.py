"""
Face Detector - OpenCV DNN Implementation
Uses OpenCV's DNN module with pre-trained Caffe models
NO dlib dependency! Works on all Python versions! 🚀
"""

import cv2
import logging
import numpy as np
from typing import List, Tuple, Optional
from pathlib import Path
import urllib.request


logger = logging.getLogger(__name__)


class FaceDetector:
    """
    OpenCV DNN-based face detector - Modern, fast, no dlib! 🤖🔒
    """
    
    # Model URLs (will auto-download if not present)
    PROTOTXT_URL = "https://raw.githubusercontent.com/opencv/opencv/master/samples/dnn/face_detector/deploy.prototxt"
    WEIGHTS_URL = "https://raw.githubusercontent.com/opencv/opencv_3rdparty/dnn_samples_face_detector_20170830/res10_300x300_ssd_iter_140000.caffemodel"
    
    def __init__(self, confidence_threshold: float = 0.5):
        """
        Initialize face detector.
        
        Args:
            confidence_threshold: Minimum confidence for detection (0.0-1.0)
        """
        self.confidence_threshold = confidence_threshold
        self.detection_count = 0
        self.net = None
        
        # Model paths
        models_dir = Path("models")
        models_dir.mkdir(exist_ok=True)
        
        self.prototxt_path = models_dir / "deploy.prototxt"
        self.weights_path = models_dir / "res10_300x300_ssd_iter_140000.caffemodel"
        
        # Download models if needed
        self._ensure_models()
        
        # Load DNN model
        try:
            self.net = cv2.dnn.readNetFromCaffe(
                str(self.prototxt_path),
                str(self.weights_path)
            )
            logger.info("✅ OpenCV DNN face detector initialized (no dlib!)")
        except Exception as e:
            logger.error(f"❌ Failed to load DNN model: {e}")
            raise
    
    def _ensure_models(self):
        """Download models if they don't exist."""
        if not self.prototxt_path.exists():
            logger.info("📥 Downloading face detection prototxt...")
            try:
                urllib.request.urlretrieve(self.PROTOTXT_URL, str(self.prototxt_path))
                logger.info("✅ Downloaded prototxt")
            except Exception as e:
                logger.error(f"❌ Failed to download prototxt: {e}")
                raise
        
        if not self.weights_path.exists():
            logger.info("📥 Downloading face detection weights (~10MB)...")
            try:
                urllib.request.urlretrieve(self.WEIGHTS_URL, str(self.weights_path))
                logger.info("✅ Downloaded weights")
            except Exception as e:
                logger.error(f"❌ Failed to download weights: {e}")
                raise
    
    def detect_faces(
        self, 
        image: np.ndarray,
        scalefactor: float = 1.0
    ) -> List[Tuple[int, int, int, int]]:
        """
        Detect all faces in an image.
        
        Args:
            image: BGR image from OpenCV
            scalefactor: Image scale factor for detection (1.0 = original size)
        
        Returns:
            List of face locations as (top, right, bottom, left) tuples
        """
        if self.net is None:
            logger.error("❌ DNN model not loaded")
            return []
        
        try:
            (h, w) = image.shape[:2]
            
            # Prepare blob for DNN
            blob = cv2.dnn.blobFromImage(
                cv2.resize(image, (300, 300)),
                1.0,
                (300, 300),
                (104.0, 177.0, 123.0)
            )
            
            # Run detection
            self.net.setInput(blob)
            detections = self.net.forward()
            
            face_locations = []
            
            # Parse detections
            for i in range(0, detections.shape[2]):
                confidence = detections[0, 0, i, 2]
                
                if confidence > self.confidence_threshold:
                    # Get bounding box
                    box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                    (startX, startY, endX, endY) = box.astype("int")
                    
                    # Convert to (top, right, bottom, left) format
                    face_locations.append((startY, endX, endY, startX))
            
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
        face_locations: Optional[List[Tuple[int, int, int, int]]] = None
    ) -> List[np.ndarray]:
        """
        Extract face encodings using simple feature extraction.
        
        Note: This is a simplified version. For production, use a proper
        face recognition model like FaceNet or ArcFace.
        
        Args:
            image: BGR image from OpenCV
            face_locations: Pre-detected face locations
        
        Returns:
            List of face encoding arrays (simplified 128-dim vectors)
        """
        try:
            if face_locations is None:
                face_locations = self.detect_faces(image)
            
            if not face_locations:
                return []
            
            encodings = []
            
            for (top, right, bottom, left) in face_locations:
                # Extract face region
                face = image[top:bottom, left:right]
                
                if face.size == 0:
                    continue
                
                # Resize to standard size
                face_resized = cv2.resize(face, (128, 128))
                
                # Convert to grayscale and flatten
                face_gray = cv2.cvtColor(face_resized, cv2.COLOR_BGR2GRAY)
                
                # Simple encoding: histogram + DCT coefficients
                hist = cv2.calcHist([face_gray], [0], None, [64], [0, 256])
                hist = cv2.normalize(hist, hist).flatten()
                
                # Get DCT coefficients
                dct = cv2.dct(np.float32(face_gray))
                dct_features = dct[:8, :8].flatten()[:64]
                
                # Combine features to get 128-dim encoding
                encoding = np.concatenate([hist, dct_features])
                encodings.append(encoding)
            
            logger.debug(f"🔢 Extracted {len(encodings)} face encoding(s)")
            return encodings
            
        except Exception as e:
            logger.error(f"❌ Face encoding extraction failed: {e}")
            return []
    
    def detect_and_encode(
        self,
        image: np.ndarray
    ) -> List[Tuple[Tuple[int, int, int, int], np.ndarray]]:
        """
        One-shot: detect faces AND extract encodings.
        
        Args:
            image: BGR image from OpenCV
        
        Returns:
            List of (face_location, face_encoding) tuples
        """
        face_locations = self.detect_faces(image)
        
        if not face_locations:
            return []
        
        encodings = self.extract_face_encodings(image, face_locations=face_locations)
        
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
        
        Args:
            image: BGR image to draw on (will be copied)
            face_locations: List of (top, right, bottom, left) tuples
            labels: Optional labels for each face
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
            "model": "OpenCV DNN (Caffe)",
            "total_detections": self.detection_count,
            "confidence_threshold": self.confidence_threshold
        }
