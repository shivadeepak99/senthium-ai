"""
Camera Monitor - Captures frames from webcam for security monitoring

Handles all the camera hardware interaction like a boss! 📸
"""

import cv2
import logging
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image


logger = logging.getLogger(__name__)


class CameraMonitor:
    """
    Manages webcam access and frame capture for security monitoring.
    
    Your digital eyes babe! Watches who's touching your PC 👀
    """
    
    def __init__(
        self, 
        camera_index: int = 0,
        snapshot_dir: str = "logs/security/snapshots",
        enable_preview: bool = False
    ):
        """
        Initialize camera monitor.
        
        Args:
            camera_index: Camera device index (0 = default webcam)
            snapshot_dir: Directory to save security snapshots
            enable_preview: Show live preview window (for debugging)
        """
        self.camera_index = camera_index
        self.snapshot_dir = Path(snapshot_dir)
        self.enable_preview = enable_preview
        self.camera: Optional[cv2.VideoCapture] = None
        self._is_initialized = False
        
        # Ensure snapshot directory exists
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"📸 Camera monitor initialized (device {camera_index})")
    
    def initialize(self) -> bool:
        """
        Initialize camera hardware.
        
        Returns:
            True if camera initialized successfully, False otherwise
        """
        if self._is_initialized:
            return True
        
        try:
            logger.info("🎥 Opening camera...")
            self.camera = cv2.VideoCapture(self.camera_index)
            
            if not self.camera.isOpened():
                logger.error("❌ Failed to open camera")
                return False
            
            # Set camera properties for better quality
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            
            # Warm up camera (first few frames are often dark)
            for _ in range(5):
                self.camera.read()
            
            self._is_initialized = True
            logger.info("✅ Camera initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Camera initialization failed: {e}")
            return False
    
    def capture_frame(self) -> Optional[np.ndarray]:
        """
        Capture a single frame from camera.
        
        Returns:
            BGR image array (numpy), or None if capture failed
        """
        if not self._is_initialized:
            if not self.initialize():
                return None
        
        # Type guard: camera is guaranteed to be initialized here
        if self.camera is None:
            return None
        
        try:
            ret, frame = self.camera.read()
            
            if not ret or frame is None:
                logger.warning("⚠️ Failed to capture frame")
                return None
            
            return frame
            
        except Exception as e:
            logger.error(f"❌ Frame capture error: {e}")
            return None
    
    def save_frame(self, frame: np.ndarray, prefix: str = "security") -> Optional[str]:
        """
        Save an existing frame to disk with timestamp.
        
        Args:
            frame: BGR image array to save
            prefix: Filename prefix (e.g., 'intruder', 'alert', 'authorized')
            
        Returns:
            Filepath where frame was saved, or None if failed
        """
        if frame is None:
            return None
        
        try:
            # Generate timestamped filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{prefix}_{timestamp}.jpg"
            filepath = self.snapshot_dir / filename
            
            # Save with high quality
            cv2.imwrite(str(filepath), frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            
            logger.debug(f"💾 Snapshot saved: {filename}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"❌ Failed to save snapshot: {e}")
            return None
    
    def capture_and_save(self, prefix: str = "security") -> Optional[Tuple[str, np.ndarray]]:
        """
        Capture frame and save to disk with timestamp.
        
        DEPRECATED: Use capture_frame() + save_frame() for better control!
        
        Args:
            prefix: Filename prefix (e.g., 'security', 'alert', 'authorized')
            
        Returns:
            Tuple of (filepath, frame) or None if failed
        """
        frame = self.capture_frame()
        if frame is None:
            return None
        
        filepath = self.save_frame(frame, prefix)
        if filepath:
            return (filepath, frame)
        return None
    
    def get_latest_snapshot_path(self) -> Optional[str]:
        """
        Get path to most recent snapshot.
        
        Returns:
            Path to latest snapshot, or None if no snapshots exist
        """
        try:
            snapshots = sorted(self.snapshot_dir.glob("*.jpg"), key=lambda p: p.stat().st_mtime)
            if snapshots:
                return str(snapshots[-1])
            return None
        except Exception as e:
            logger.error(f"❌ Error finding latest snapshot: {e}")
            return None
    
    def cleanup_old_snapshots(self, max_age_days: int = 7, max_files: int = 100):
        """
        Delete snapshots older than specified days OR exceeding max file limit.
        
        Keeps your disk happy by rotating old snapshots! 🗑️💕
        
        Args:
            max_age_days: Maximum age in days to keep snapshots
            max_files: Maximum number of snapshot files to keep (newest preserved)
        """
        try:
            from datetime import timedelta
            cutoff = datetime.now() - timedelta(days=max_age_days)
            
            # Get all snapshots sorted by modification time (oldest first)
            all_snapshots = sorted(
                self.snapshot_dir.glob("*.jpg"), 
                key=lambda p: p.stat().st_mtime
            )
            
            deleted_count = 0
            
            # Delete old snapshots (by age)
            for snapshot in all_snapshots[:]:  # Copy list to avoid modification issues
                if datetime.fromtimestamp(snapshot.stat().st_mtime) < cutoff:
                    snapshot.unlink()
                    all_snapshots.remove(snapshot)
                    deleted_count += 1
            
            # Delete excess snapshots (by count) - keep newest ones
            if len(all_snapshots) > max_files:
                excess = len(all_snapshots) - max_files
                for snapshot in all_snapshots[:excess]:  # Delete oldest
                    snapshot.unlink()
                    deleted_count += 1
            
            if deleted_count > 0:
                logger.info(f"🗑️ Cleaned up {deleted_count} old snapshots (age: {max_age_days}d, max: {max_files} files)")
                
        except Exception as e:
            logger.error(f"❌ Snapshot cleanup failed: {e}")
    
    def release(self):
        """Release camera hardware resources."""
        if self.camera is not None:
            self.camera.release()
            self._is_initialized = False
            logger.info("📸 Camera released")
    
    def __del__(self):
        """Cleanup on destruction."""
        self.release()
