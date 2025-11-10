"""
Face Recognizer - Matches detected faces against authorized users

This is your AI security guard babe! Knows friend from foe! 🛡️
"""

import logging
import numpy as np
import json
from pathlib import Path
from typing import List, Optional, Dict, Tuple
from datetime import datetime


logger = logging.getLogger(__name__)


class FaceRecognizer:
    """
    Manages authorized face encodings and recognizes faces in images.
    
    Keeps your PC safe from intruders! 💖🔒
    """
    
    def __init__(
        self,
        authorized_faces_file: str = "config/faces/authorized.json",
        tolerance: float = 10.0  # TEMP: Very high to test if recognition works at all
    ):
        """
        Initialize face recognizer.
        
        Args:
            authorized_faces_file: Path to JSON file storing authorized face encodings
            tolerance: Recognition tolerance (higher = more lenient)
        """
        self.authorized_faces_file = Path(authorized_faces_file)
        self.tolerance = tolerance
        
        print(f"[DEBUG] FaceRecognizer initialized with tolerance={tolerance}")
        self.authorized_encodings: Dict[str, List[np.ndarray]] = {}  # Keep old name for compatibility
        self.recognition_count = 0
        
        # Ensure directory exists
        self.authorized_faces_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing authorized faces
        self._load_authorized_faces()
        
        logger.info(f"🛡️ Face recognizer initialized (tolerance: {tolerance})")
    
    def _load_authorized_faces(self):
        """Load authorized face encodings from disk."""
        if not self.authorized_faces_file.exists():
            logger.info("📋 No authorized faces file found (will create on first enrollment)")
            return
        
        try:
            with open(self.authorized_faces_file, 'r') as f:
                data = json.load(f)
            
            # Convert lists back to numpy arrays
            for name, encodings_list in data.items():
                self.authorized_encodings[name] = [
                    np.array(enc) for enc in encodings_list
                ]
            
            total_faces = sum(len(encs) for encs in self.authorized_encodings.values())
            logger.info(f"✅ Loaded {len(self.authorized_encodings)} authorized user(s) with {total_faces} face(s)")
            
        except Exception as e:
            logger.error(f"❌ Failed to load authorized faces: {e}")
    
    def _save_authorized_faces(self):
        """Save authorized face encodings to disk."""
        try:
            # Convert numpy arrays to lists for JSON serialization
            data = {
                name: [enc.tolist() for enc in encodings]
                for name, encodings in self.authorized_encodings.items()
            }
            
            with open(self.authorized_faces_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.debug("💾 Authorized faces saved to disk")
            
        except Exception as e:
            logger.error(f"❌ Failed to save authorized faces: {e}")
    
    def enroll_user(
        self,
        user_name: str,
        face_encoding: np.ndarray,
        replace: bool = False
    ) -> bool:
        """
        Enroll a new authorized user or add additional face encoding.
        
        Args:
            user_name: Name/identifier for this user (e.g., "Owner", "John")
            face_encoding: 128-dim face encoding vector
            replace: If True, replace all existing encodings for this user
        
        Returns:
            True if enrollment successful
        """
        try:
            if replace or user_name not in self.authorized_encodings:
                self.authorized_encodings[user_name] = []
            
            self.authorized_encodings[user_name].append(face_encoding)
            self._save_authorized_faces()
            
            logger.info(f"✅ Enrolled face for user '{user_name}' ({len(self.authorized_encodings[user_name])} total faces)")
            return True
            
        except Exception as e:
            logger.error(f"❌ Enrollment failed: {e}")
            return False
    
    def remove_user(self, user_name: str) -> bool:
        """
        Remove an authorized user completely.
        
        Args:
            user_name: Name of user to remove
        
        Returns:
            True if user was removed
        """
        if user_name in self.authorized_encodings:
            del self.authorized_encodings[user_name]
            self._save_authorized_faces()
            logger.info(f"🗑️ Removed user '{user_name}'")
            return True
        
        logger.warning(f"⚠️ User '{user_name}' not found")
        return False
    
    def recognize_face(
        self,
        face_encoding: np.ndarray
    ) -> Optional[Tuple[str, float]]:
        """
        Recognize a face encoding against authorized users.
        
        Args:
            face_encoding: 128-dim face encoding to recognize
        
        Returns:
            Tuple of (user_name, confidence) if recognized, None if unknown
            confidence = 1.0 - distance (higher = more confident)
        """
        if not self.authorized_encodings:
            return None
        
        self.recognition_count += 1
        
        best_match_name = None
        best_match_distance = float('inf')
        
        # Compare against all authorized faces
        for user_name, user_encodings in self.authorized_encodings.items():
            for known_encoding in user_encodings:
                # DEBUG: Show encoding details
                print(f"[DEBUG] Known encoding: shape={known_encoding.shape}, first 5={known_encoding[:5]}")
                print(f"[DEBUG] Query encoding: shape={face_encoding.shape}, first 5={face_encoding[:5]}")
                
                # Calculate face distance (lower = more similar) - Euclidean distance
                distance = np.linalg.norm(known_encoding - face_encoding)
                
                print(f"[DEBUG] Comparing to {user_name}: distance={distance:.4f}, tolerance={self.tolerance}")
                
                if distance < best_match_distance:
                    best_match_distance = distance
                    best_match_name = user_name
        
        # Check if best match is within tolerance
        if best_match_distance <= self.tolerance and best_match_name is not None:
            confidence = float(1.0 - best_match_distance)  # Ensure float type
            print(f"[DEBUG] ✅ MATCH FOUND: {best_match_name} (distance={best_match_distance:.4f}, confidence={confidence:.2f})")
            logger.debug(f"✅ Recognized: {best_match_name} (confidence: {confidence:.2f})")
            return (best_match_name, confidence)
        
        print(f"[DEBUG] ❌ NO MATCH: closest={best_match_name}, distance={best_match_distance:.4f} > tolerance={self.tolerance}")
        logger.debug(f"❌ Unknown face (closest: {best_match_name}, distance: {best_match_distance:.2f})")
        return None
    
    def recognize_multiple(
        self,
        face_encodings: List[np.ndarray]
    ) -> List[Optional[Tuple[str, float]]]:
        """
        Recognize multiple faces at once.
        
        Args:
            face_encodings: List of face encodings to recognize
        
        Returns:
            List of recognition results (same order as input)
            Each element is either (user_name, confidence) or None
        """
        return [self.recognize_face(enc) for enc in face_encodings]
    
    def is_authorized(self, face_encoding: np.ndarray) -> bool:
        """
        Quick check: is this face authorized?
        
        Args:
            face_encoding: Face encoding to check
        
        Returns:
            True if face is recognized as authorized user
        """
        result = self.recognize_face(face_encoding)
        return result is not None
    
    def get_authorized_users(self) -> List[str]:
        """Get list of all authorized user names."""
        return list(self.authorized_encodings.keys())
    
    def get_stats(self) -> dict:
        """Get recognition statistics."""
        return {
            "authorized_users": len(self.authorized_encodings),
            "total_faces": sum(len(encs) for encs in self.authorized_encodings.values()),
            "total_recognitions": self.recognition_count,
            "tolerance": self.tolerance
        }
