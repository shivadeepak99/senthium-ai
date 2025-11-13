"""
AI Training Module - Fine-tune face recognition with 1-minute video capture

This module handles the "training" component where users record a 1-minute
video session to collect multiple face angles/lighting conditions for improved
recognition accuracy.

Demonstrates: Transfer learning, temporal face analysis, data augmentation
"""

import cv2
import numpy as np
import face_recognition
from pathlib import Path
import json
import time
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class FaceTrainer:
    """
    AI Training module for collecting and processing face data.
    
    Features:
    - 1-minute video capture with real-time face tracking
    - Multi-angle face collection (user moves head)
    - Automatic quality filtering
    - Embedding generation and averaging
    - Training progress tracking
    """
    
    def __init__(self, user_name: str, output_dir: str = "data/training"):
        """
        Initialize trainer for a user.
        
        Args:
            user_name: Name of person being trained
            output_dir: Directory to save training data
        """
        self.user_name = user_name
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Training session data
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = self.output_dir / f"{user_name}_{self.session_id}"
        self.session_dir.mkdir(exist_ok=True)
        
        # Collected data
        self.frames: List[np.ndarray] = []
        self.face_locations: List[Tuple] = []
        self.face_encodings: List[np.ndarray] = []
        self.timestamps: List[float] = []
        
        # Training metrics
        self.total_frames = 0
        self.valid_frames = 0
        self.quality_scores: List[float] = []
        
        logger.info(f"🎓 Trainer initialized for {user_name}")
    
    def capture_training_video(
        self, 
        duration_seconds: int = 60,
        fps_target: int = 10,
        on_progress=None
    ) -> Dict:
        """
        Capture 1-minute training video with real-time face detection.
        
        Args:
            duration_seconds: Length of training session (default 60s)
            fps_target: Target frames per second to capture
            on_progress: Callback function(progress_pct, frame, faces) for UI updates
        
        Returns:
            Training session statistics
        """
        logger.info(f"📹 Starting {duration_seconds}s training capture...")
        
        # Open webcam
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            raise RuntimeError("❌ Could not open webcam!")
        
        # Set resolution
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        start_time = time.time()
        frame_interval = 1.0 / fps_target
        last_capture = 0
        
        try:
            while True:
                current_time = time.time()
                elapsed = current_time - start_time
                
                # Check if training complete
                if elapsed >= duration_seconds:
                    logger.info("✅ Training duration completed!")
                    break
                
                # Read frame
                ret, frame = cap.read()
                if not ret:
                    logger.warning("⚠️ Failed to read frame")
                    continue
                
                self.total_frames += 1
                
                # Capture frame at target FPS
                if current_time - last_capture >= frame_interval:
                    last_capture = current_time
                    
                    # Convert BGR to RGB
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    
                    # Detect faces
                    face_locations = face_recognition.face_locations(rgb_frame, model='hog')
                    
                    # Process if face detected
                    if len(face_locations) > 0:
                        # Get first face
                        face_location = face_locations[0]
                        
                        # Generate encoding
                        face_encodings = face_recognition.face_encodings(rgb_frame, [face_location])
                        
                        if len(face_encodings) > 0:
                            face_encoding = face_encodings[0]
                            
                            # Calculate quality score (based on face size)
                            top, right, bottom, left = face_location
                            face_width = right - left
                            face_height = bottom - top
                            face_area = face_width * face_height
                            
                            # Normalize by frame size (higher is better)
                            quality = face_area / (frame.shape[0] * frame.shape[1])
                            
                            # Store data
                            self.frames.append(rgb_frame.copy())
                            self.face_locations.append(face_location)
                            self.face_encodings.append(face_encoding)
                            self.timestamps.append(elapsed)
                            self.quality_scores.append(quality)
                            self.valid_frames += 1
                    
                    # Call progress callback for UI update
                    if on_progress:
                        progress_pct = (elapsed / duration_seconds) * 100
                        on_progress(progress_pct, frame, face_locations)
        
        finally:
            cap.release()
        
        # Calculate statistics
        stats = self._calculate_training_stats()
        
        logger.info(f"📊 Training complete: {self.valid_frames} valid frames captured")
        
        return stats
    
    def _calculate_training_stats(self) -> Dict:
        """Calculate training session statistics."""
        
        if len(self.quality_scores) == 0:
            return {
                'total_frames': self.total_frames,
                'valid_frames': 0,
                'success': False,
                'error': 'No faces detected during training'
            }
        
        stats = {
            'total_frames': self.total_frames,
            'valid_frames': self.valid_frames,
            'capture_rate': (self.valid_frames / self.total_frames * 100) if self.total_frames > 0 else 0,
            'avg_quality': float(np.mean(self.quality_scores)),
            'min_quality': float(np.min(self.quality_scores)),
            'max_quality': float(np.max(self.quality_scores)),
            'duration': self.timestamps[-1] if self.timestamps else 0,
            'fps': len(self.timestamps) / self.timestamps[-1] if self.timestamps and self.timestamps[-1] > 0 else 0,
            'success': True
        }
        
        return stats
    
    def generate_averaged_encoding(self, top_n: int = 30) -> np.ndarray:
        """
        Generate final encoding by averaging top-quality frames.
        
        This is the "training" step - we create a robust embedding by
        averaging multiple high-quality face encodings.
        
        Args:
            top_n: Number of best frames to average
        
        Returns:
            Final 128-dimensional face encoding
        """
        logger.info(f"🧠 Generating averaged encoding from top {top_n} frames...")
        
        if len(self.face_encodings) == 0:
            raise ValueError("No face encodings collected!")
        
        # Sort by quality score
        sorted_indices = np.argsort(self.quality_scores)[::-1]  # Descending
        
        # Take top N frames
        top_indices = sorted_indices[:min(top_n, len(sorted_indices))]
        top_encodings = [self.face_encodings[i] for i in top_indices]
        
        # Average encodings (this is the fine-tuning!)
        averaged_encoding = np.mean(top_encodings, axis=0)
        
        logger.info(f"✅ Averaged {len(top_encodings)} high-quality encodings")
        
        return averaged_encoding
    
    def save_training_data(self, final_encoding: np.ndarray, save_frames: bool = True) -> str:
        """
        Save training data to disk.
        
        Args:
            final_encoding: Final averaged face encoding
            save_frames: Whether to save captured frames (for visualization)
        
        Returns:
            Path to saved encoding file
        """
        logger.info("💾 Saving training data...")
        
        # Save encoding
        encoding_file = self.session_dir / "encoding.json"
        encoding_data = {
            'user_name': self.user_name,
            'session_id': self.session_id,
            'encoding': final_encoding.tolist(),
            'trained_at': datetime.now().isoformat(),
            'num_frames': len(self.frames),
            'avg_quality': float(np.mean(self.quality_scores)) if self.quality_scores else 0
        }
        
        with open(encoding_file, 'w') as f:
            json.dump(encoding_data, f, indent=2)
        
        logger.info(f"✅ Encoding saved: {encoding_file}")
        
        # Save sample frames (every 10th frame)
        if save_frames:
            frames_dir = self.session_dir / "frames"
            frames_dir.mkdir(exist_ok=True)
            
            for i, (frame, location) in enumerate(zip(self.frames, self.face_locations)):
                if i % 10 == 0:  # Save every 10th frame
                    # Draw bounding box
                    top, right, bottom, left = location
                    cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                    
                    # Save frame
                    frame_file = frames_dir / f"frame_{i:04d}.jpg"
                    cv2.imwrite(str(frame_file), cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
            
            logger.info(f"✅ Sample frames saved: {frames_dir}")
        
        return str(encoding_file)
    
    def get_training_report(self, stats: Dict, final_encoding: np.ndarray) -> Dict:
        """
        Generate comprehensive training report.
        
        Returns:
            Training report with metrics and recommendations
        """
        report = {
            'user_name': self.user_name,
            'session_id': self.session_id,
            'timestamp': datetime.now().isoformat(),
            'statistics': stats,
            'encoding_shape': final_encoding.shape,
            'encoding_mean': float(np.mean(final_encoding)),
            'encoding_std': float(np.std(final_encoding)),
            'quality_assessment': self._assess_training_quality(stats)
        }
        
        return report
    
    def _assess_training_quality(self, stats: Dict) -> str:
        """Assess training quality and provide recommendation."""
        
        if not stats.get('success'):
            return "❌ FAILED - No faces detected. Please try again."
        
        valid_frames = stats.get('valid_frames', 0)
        avg_quality = stats.get('avg_quality', 0)
        
        if valid_frames >= 400 and avg_quality >= 0.15:
            return "✅ EXCELLENT - High-quality training data collected!"
        elif valid_frames >= 200 and avg_quality >= 0.10:
            return "🟢 GOOD - Sufficient data for accurate recognition"
        elif valid_frames >= 100 and avg_quality >= 0.05:
            return "🟡 FAIR - May need retraining for better accuracy"
        else:
            return "🔴 POOR - Recommend capturing again with better lighting/positioning"


def train_user(user_name: str, duration: int = 60) -> Dict:
    """
    Convenience function to train a user.
    
    Args:
        user_name: Name of person to train
        duration: Training duration in seconds
    
    Returns:
        Training report
    """
    trainer = FaceTrainer(user_name)
    
    # Capture video
    stats = trainer.capture_training_video(duration_seconds=duration)
    
    if not stats['success']:
        return {'success': False, 'error': stats.get('error', 'Training failed')}
    
    # Generate final encoding
    final_encoding = trainer.generate_averaged_encoding()
    
    # Save data
    encoding_file = trainer.save_training_data(final_encoding)
    
    # Generate report
    report = trainer.get_training_report(stats, final_encoding)
    report['encoding_file'] = encoding_file
    
    return report
