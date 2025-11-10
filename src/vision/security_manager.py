"""
Security Manager - Coordinates camera, face detection, and alerts

The master orchestrator of your PC security babe! 🎯🔒
"""

import logging
import time
from datetime import datetime
from typing import Optional, Dict, List
from pathlib import Path

from src.vision.camera import CameraMonitor
from src.vision.detector import FaceDetector
from src.vision.recognizer import FaceRecognizer
from src.alerts.notifier import AlertNotifier, SecurityAlert, AlertType
from src.actions.system_actions import SystemActions


logger = logging.getLogger(__name__)


class SecurityManager:
    """
    Main security coordinator - brings all AI vision components together.
    
    This is your AI bodyguard running 24/7! 💪🤖
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize security manager.
        
        Args:
            config: Configuration dict with keys:
                    - camera_index: Webcam device index (default: 0)
                    - detection_model: 'hog' (fast) or 'cnn' (accurate)
                    - recognition_tolerance: 0.6 = balanced, lower = stricter
                    - check_interval_seconds: How often to check (default: 10)
                    - alert_cooldown_seconds: Min time between alerts (default: 300)
                    - enable_security: Master enable/disable (default: False)
                    - discord_webhook_url, email config, etc.
        """
        self.config = config or {}
        
        # Initialize components
        self.camera = CameraMonitor(
            camera_index=self.config.get('camera_index', 0),
            snapshot_dir=self.config.get('snapshot_dir', 'logs/security/snapshots')
        )
        
        self.detector = FaceDetector(
            model=self.config.get('detection_model', 'hog')
        )
        
        self.recognizer = FaceRecognizer(
            authorized_faces_file=self.config.get('authorized_faces_file', 'config/faces/authorized.json'),
            tolerance=self.config.get('recognition_tolerance', 0.6)
        )
        
        self.notifier = AlertNotifier(
            alerts_log_file=self.config.get('alerts_log_file', 'logs/security/alerts.jsonl'),
            config=self.config
        )
        
        # System actions (lock, sleep, shutdown)
        self.system_actions = SystemActions()
        
        # State tracking
        self.enabled = self.config.get('enabled', False)  # Fixed: was 'enable_security'
        self.check_interval = self.config.get('check_interval_seconds', 10)
        self.alert_cooldown = self.config.get('alert_cooldown_seconds', 300)
        self.last_check_time: Optional[datetime] = None
        self.total_checks = 0
        self.unauthorized_detections = 0
        
        # Security action settings
        self.auto_lock_on_intruder = self.config.get('auto_lock_on_intruder', True)
        self.auto_sleep_on_intruder = self.config.get('auto_sleep_on_intruder', False)
        self.play_alarm_on_intruder = self.config.get('play_alarm_on_intruder', True)
        
        # Initialize camera immediately for daemon usage
        if self.enabled:
            logger.info("📸 Pre-initializing camera for daemon...")
            self.camera.initialize()
        
        logger.info(f"🛡️ Security manager initialized (enabled: {self.enabled})")
        logger.info(f"   Auto-lock: {self.auto_lock_on_intruder} | Auto-sleep: {self.auto_sleep_on_intruder}")
    
    def enable(self):
        """Enable security monitoring."""
        self.enabled = True
        logger.info("✅ Security monitoring ENABLED")
    
    def disable(self):
        """Disable security monitoring."""
        self.enabled = False
        logger.info("⏸️ Security monitoring DISABLED")
    
    def perform_security_check(self) -> Optional[Dict]:
        """
        Perform a single security check cycle.
        
        Returns:
            Dict with check results, or None if check skipped
        """
        if not self.enabled:
            return None
        
        self.total_checks += 1
        self.last_check_time = datetime.now()
        
        logger.debug("🔍 Performing security check...")
        
        try:
            # Capture frame and save snapshot
            result = self.camera.capture_and_save(prefix="security")
            if result is None:
                logger.warning("⚠️ Camera capture failed")
                return {
                    "status": "error",
                    "error": "Camera capture failed",
                    "timestamp": self.last_check_time.isoformat()
                }
            
            snapshot_path, frame = result
            
            # Detect and encode all faces
            detections = self.detector.detect_and_encode(frame, num_jitters=1)
            
            if not detections:
                logger.debug("👻 No faces detected")
                return {
                    "status": "no_faces",
                    "timestamp": self.last_check_time.isoformat(),
                    "snapshot_path": snapshot_path
                }
            
            logger.debug(f"👥 Detected {len(detections)} face(s)")
            
            # Recognize each detected face
            recognized_faces = []
            unknown_faces = []
            
            for face_location, face_encoding in detections:
                result = self.recognizer.recognize_face(face_encoding)
                
                if result:
                    user_name, confidence = result
                    recognized_faces.append({
                        "name": user_name,
                        "confidence": confidence,
                        "location": face_location
                    })
                    logger.debug(f"✅ Recognized: {user_name} ({confidence:.2f})")
                else:
                    unknown_faces.append({
                        "location": face_location
                    })
                    logger.warning("❌ Unknown face detected!")
            
            # Handle unauthorized access
            if unknown_faces:
                self.unauthorized_detections += 1
                
                logger.critical(f"🚨 INTRUDER DETECTED! {len(unknown_faces)} unauthorized face(s)!")
                
                # 🔐 TAKE IMMEDIATE ACTION AGAINST INTRUDER!
                # Play alarm sound first (non-blocking)
                if self.play_alarm_on_intruder:
                    try:
                        self.system_actions.play_alarm_sound()
                    except Exception as e:
                        logger.error(f"Failed to play alarm: {e}")
                
                # Lock screen to block intruder access
                if self.auto_lock_on_intruder:
                    try:
                        logger.warning("🔒 LOCKING SCREEN TO BLOCK INTRUDER!")
                        lock_success = self.system_actions.lock_screen()
                        if lock_success:
                            logger.info("✅ Screen locked successfully - intruder blocked!")
                        else:
                            logger.error("❌ Failed to lock screen - check permissions!")
                    except Exception as e:
                        logger.error(f"❌ Lock screen failed: {e}")
                
                # Optional: Put computer to sleep (nuclear option)
                if self.auto_sleep_on_intruder:
                    try:
                        logger.warning("😴 PUTTING COMPUTER TO SLEEP!")
                        self.system_actions.sleep_computer()
                    except Exception as e:
                        logger.error(f"❌ Sleep failed: {e}")
                
                # Send alert (if cooldown period passed)
                if self.notifier.should_send_alert(self.alert_cooldown):
                    alert = SecurityAlert(
                        timestamp=self.last_check_time.isoformat(),
                        alert_type=AlertType.UNAUTHORIZED_ACCESS,
                        message=f"⚠️ UNAUTHORIZED ACCESS DETECTED! {len(unknown_faces)} unknown face(s) detected. Screen locked!",
                        snapshot_path=snapshot_path,
                        detected_faces_count=len(detections)
                    )
                    
                    self.notifier.send_alert(alert)
                    logger.warning("� ALERT SENT: Unauthorized access detected!")
            
            return {
                "status": "success",
                "timestamp": self.last_check_time.isoformat(),
                "snapshot_path": snapshot_path,
                "detected_faces_count": len(detections),
                "authorized_faces_count": len(recognized_faces),
                "unknown_faces_count": len(unknown_faces),
                "recognized_faces": recognized_faces,
                "unknown_faces": unknown_faces,
                "alert_sent": len(unknown_faces) > 0 and self.notifier.should_send_alert(0)
            }
            
        except Exception as e:
            logger.error(f"❌ Security check failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def enroll_owner_from_camera(self, user_name: str = "Owner") -> bool:
        """
        Convenience method: capture photo from camera and enroll as owner.
        
        Args:
            user_name: Name for this authorized user
        
        Returns:
            True if enrollment successful
        """
        logger.info(f"📸 Enrolling {user_name} from camera...")
        
        try:
            # Capture frame
            frame = self.camera.capture_frame()
            if frame is None:
                logger.error("❌ Camera capture failed")
                return False
            
            # Detect faces
            detections = self.detector.detect_and_encode(frame, num_jitters=2)
            
            if not detections:
                logger.error("❌ No face detected in frame")
                return False
            
            if len(detections) > 1:
                logger.warning(f"⚠️ Multiple faces detected ({len(detections)}), using first one")
            
            # Use first detected face
            _, face_encoding = detections[0]
            
            # Enroll
            success = self.recognizer.enroll_user(user_name, face_encoding)
            
            if success:
                logger.info(f"✅ {user_name} enrolled successfully!")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Enrollment failed: {e}")
            return False
    
    def enroll_owner_from_file(self, image_path: str, user_name: str = "Owner") -> bool:
        """
        Enroll owner from an image file.
        
        Args:
            image_path: Path to image file
            user_name: Name for this authorized user
        
        Returns:
            True if enrollment successful
        """
        import cv2
        
        logger.info(f"📁 Enrolling {user_name} from {image_path}...")
        
        try:
            # Load image
            frame = cv2.imread(image_path)
            if frame is None:
                logger.error(f"❌ Failed to load image: {image_path}")
                return False
            
            # Detect faces
            detections = self.detector.detect_and_encode(frame, num_jitters=2)
            
            if not detections:
                logger.error("❌ No face detected in image")
                return False
            
            if len(detections) > 1:
                logger.warning(f"⚠️ Multiple faces detected ({len(detections)}), using first one")
            
            # Use first detected face
            _, face_encoding = detections[0]
            
            # Enroll
            success = self.recognizer.enroll_user(user_name, face_encoding)
            
            if success:
                logger.info(f"✅ {user_name} enrolled successfully!")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Enrollment failed: {e}")
            return False
    
    def get_stats(self) -> Dict:
        """Get comprehensive security statistics."""
        return {
            "enabled": self.enabled,
            "total_checks": self.total_checks,
            "unauthorized_detections": self.unauthorized_detections,
            "last_check_time": self.last_check_time.isoformat() if self.last_check_time else None,
            "camera": {
                "initialized": self.camera._is_initialized
            },
            "detector": self.detector.get_stats(),
            "recognizer": self.recognizer.get_stats(),
            "notifier": self.notifier.get_stats()
        }
    
    def cleanup(self):
        """Cleanup resources."""
        self.camera.release()
        logger.info("🧹 Security manager cleaned up")
