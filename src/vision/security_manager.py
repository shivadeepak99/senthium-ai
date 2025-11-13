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
from src.vision.image_annotator import ImageAnnotator
from src.alerts.notifier import AlertNotifier, SecurityAlert, AlertType
from src.actions.system_actions import SystemActions
from src.detection.intruder_patterns import IntruderPatternDetector

# Optional: psutil for critical apps detection
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


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
        
        # Image annotator for visual overlays
        self.annotator = ImageAnnotator(
            logo_path=self.config.get('logo_path', None)
        )
        
        # 🔍 Intruder pattern detector (tracks repeat offenders)
        pattern_config = self.config.get('intruder_patterns', {})
        self.pattern_detector = None
        if pattern_config.get('enabled', False):
            self.pattern_detector = IntruderPatternDetector(
                similarity_threshold=pattern_config.get('similarity_threshold', 0.6),
                alert_threshold=pattern_config.get('alert_threshold', 3),
                time_window_hours=pattern_config.get('time_window_hours', 24)
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
        
        # 🎬 Critical apps protection
        critical_apps_config = self.config.get('critical_apps', {})
        self.critical_apps_enabled = critical_apps_config.get('enabled', False)
        self.critical_app_names = critical_apps_config.get('process_names', [])
        self.critical_apps_behavior = critical_apps_config.get('on_critical_running', {})
        
        # ⏱️ Grace period & lock delay
        self.grace_period = self.config.get('grace_period_seconds', 30)
        self.lock_delay = self.config.get('unauthorized_lock_delay_seconds', 3)
        
        # 🔥 DEBUG: Log the loaded values with their types
        logger.debug(f"🔍 CONFIG DEBUG:")
        logger.debug(f"   grace_period: {self.grace_period} (type: {type(self.grace_period).__name__})")
        logger.debug(f"   lock_delay: {self.lock_delay} (type: {type(self.lock_delay).__name__})")
        logger.debug(f"   Raw config keys: {list(self.config.keys())}")
        
        self.notify_on_state_change_only = self.config.get('notify_on_state_change_only', True)
        
        # State tracking for grace period
        self.current_state = "MONITORING"
        self.state_start_time: Optional[datetime] = None
        self.no_face_start_time: Optional[datetime] = None
        self.unauthorized_start_time: Optional[datetime] = None
        
        logger.info(f"⏱️ Grace period: {self.grace_period}s | Lock delay: {self.lock_delay}s")
        logger.info(f"🎬 Critical apps protection: {self.critical_apps_enabled}")
        if self.critical_apps_enabled:
            logger.info(f"   Watching: {', '.join(self.critical_app_names[:5])}...")
        
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
    
    def _check_critical_apps_running(self) -> Optional[str]:
        """
        Check if any critical apps are running.
        
        Returns:
            Name of critical app if found, None otherwise
        """
        if not self.critical_apps_enabled or not PSUTIL_AVAILABLE:
            return None
        
        try:
            for proc in psutil.process_iter(['name']):
                try:
                    proc_name = proc.info['name']
                    if proc_name and proc_name.lower() in [app.lower() for app in self.critical_app_names]:
                        return proc_name
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            logger.warning(f"⚠️ Failed to check critical apps: {e}")
        
        return None
    
    def _transition_state(self, new_state: str, reason: str = ""):
        """
        Transition to a new state and log it.
        
        Args:
            new_state: New state to transition to
            reason: Reason for transition
        """
        old_state = self.current_state
        if old_state != new_state:
            self.current_state = new_state
            self.state_start_time = datetime.now()
            logger.info(f"🔄 STATE CHANGE: {old_state} → {new_state} {f'({reason})' if reason else ''}")
    
    def _get_state_duration(self) -> float:
        """Get how long we've been in current state (seconds)."""
        if self.state_start_time:
            return (datetime.now() - self.state_start_time).total_seconds()
        return 0.0
    
    def perform_security_check(self) -> Optional[Dict]:
        """
        Perform a single security check cycle.
        
        Returns:
            Dict with check results, or None if check skipped
        """
        if not self.enabled:
            logger.debug("⏸️ Security check skipped (disabled)")
            return None
        
        self.total_checks += 1
        self.last_check_time = datetime.now()
        
        logger.info(f"🔍 Performing security check #{self.total_checks}...")
        
        try:
            # Capture frame (don't save yet - only save on threats!)
            logger.debug("📸 Capturing frame from camera...")
            frame = self.camera.capture_frame()
            if frame is None:
                logger.warning("⚠️ Camera capture failed - no frame returned")
                return {
                    "status": "error",
                    "error": "Camera capture failed",
                    "timestamp": self.last_check_time.isoformat()
                }
            
            logger.debug(f"✅ Frame captured: {frame.shape}")
            
            # Detect and encode all faces
            logger.debug("🔎 Detecting and encoding faces...")
            detections = self.detector.detect_and_encode(frame, num_jitters=1)
            
            if not detections:
                logger.debug("👻 No faces detected in frame")
                return {
                    "status": "no_faces",
                    "timestamp": self.last_check_time.isoformat(),
                    "snapshot_path": None
                }
            
            logger.info(f"👥 Detected {len(detections)} face(s) - analyzing...")
            
            # Recognize each detected face
            recognized_faces = []
            unknown_faces = []
            face_labels = []  # For annotation
            
            for idx, (face_location, face_encoding) in enumerate(detections):
                logger.debug(f"🧠 Recognizing face {idx+1}/{len(detections)}...")
                result = self.recognizer.recognize_face(face_encoding)
                
                if result:
                    user_name, confidence = result
                    recognized_faces.append({
                        "name": user_name,
                        "confidence": confidence,
                        "location": face_location
                    })
                    face_labels.append({
                        "name": user_name,
                        "distance": confidence,
                        "is_authorized": True
                    })
                    logger.info(f"✅ Recognized: {user_name} (confidence: {confidence:.2f})")
                else:
                    unknown_faces.append({
                        "location": face_location,
                        "encoding": face_encoding  # Store for pattern detection
                    })
                    face_labels.append({
                        "name": "UNKNOWN",
                        "distance": 99.99,  # High distance = not recognized
                        "is_authorized": False
                    })
                    logger.warning(f"❌ Unknown face #{idx+1} detected!")
            
            # ⚠️ ONLY SAVE SNAPSHOT IF THREAT DETECTED!
            snapshot_path = None
            annotated_snapshot_path = None
            
            if unknown_faces:
                # 🚨 INTRUDER! Save snapshot NOW
                logger.warning(f"🚨 INTRUDER ALERT! Saving snapshot - {len(unknown_faces)} unauthorized face(s)!")
                snapshot_path = self.camera.save_frame(frame, prefix="intruder")
                logger.info(f"📸 Snapshot saved: {snapshot_path}")
                
                # 🗑️ Auto-cleanup old snapshots (keep max 100, 7 days)
                cleaned = self.camera.cleanup_old_snapshots(max_age_days=7, max_files=100)
                if cleaned > 0:
                    logger.debug(f"🗑️ Cleaned up {cleaned} old snapshot(s)")
                
                # Record intruder pattern
                for unknown in unknown_faces:
                    if self.pattern_detector:
                        is_repeat, pattern = self.pattern_detector.record_intruder(
                            unknown['encoding'],
                            timestamp=self.last_check_time.isoformat(),
                            snapshot_path=snapshot_path
                        )
                        
                        if is_repeat and pattern:
                            logger.warning(f"🚨 REPEAT OFFENDER! Pattern: {pattern.pattern_id}")
                            logger.warning(f"   Occurrences: {pattern.count}, Threat: {pattern.get_threat_level()}")
            
            # 📸 CREATE ANNOTATED SNAPSHOT (only if we saved one)
            if snapshot_path:
                try:
                    # Extract just the locations for annotation
                    face_locations_list = [d[0] for d in detections]
                    
                    # Determine alert type for color coding
                    if unknown_faces:
                        alert_type = "UNAUTHORIZED"
                    elif len(recognized_faces) > 1:
                        alert_type = "MULTIPLE_FACES"
                    else:
                        alert_type = "AUTHORIZED"
                    
                    # Create annotated version
                    annotated_snapshot_path = self.annotator.create_annotated_snapshot(
                        original_snapshot_path=snapshot_path,
                        face_locations=face_locations_list,
                        face_labels=face_labels,
                        alert_type=alert_type
                    )
                    
                    if annotated_snapshot_path:
                        logger.debug(f"🎨 Annotated snapshot created: {annotated_snapshot_path}")
                    
                except Exception as e:
                    logger.warning(f"⚠️ Failed to create annotated snapshot: {e}")
                    # Continue anyway - annotation is optional
            
            # 🧠 SMART STATE MACHINE LOGIC
            previous_state = self.current_state
            action_taken = []
            
            # === SCENARIO 1: AUTHORIZED USER PRESENT ===
            if recognized_faces and not unknown_faces:
                self._transition_state("AUTHORIZED", f"{len(recognized_faces)} authorized")
                self.no_face_start_time = None
                self.unauthorized_start_time = None
                
                # Only notify on state change (reduce spam)
                if self.notify_on_state_change_only and previous_state != "AUTHORIZED":
                    logger.info(f"🟢 AUTHORIZED: {', '.join([f['name'] for f in recognized_faces])}")
                
                return {
                    "status": "success",
                    "state": self.current_state,
                    "timestamp": self.last_check_time.isoformat(),
                    "snapshot_path": snapshot_path,
                    "detected_faces_count": len(detections),
                    "authorized_faces_count": len(recognized_faces),
                    "unknown_faces_count": 0,
                    "recognized_faces": recognized_faces,
                    "action_taken": action_taken
                }
            
            # === SCENARIO 2: NO FACE DETECTED ===
            if not detections:
                # Start grace timer if not already started
                if self.no_face_start_time is None:
                    self.no_face_start_time = datetime.now()
                    self._transition_state("NO_FACE", "starting grace period")
                    logger.warning(f"👻 NO FACE: Grace period started ({self.grace_period}s)")
                
                # Check if grace period exceeded
                no_face_duration = (datetime.now() - self.no_face_start_time).total_seconds()
                
                if no_face_duration < self.grace_period:
                    # Still in grace
                    self._transition_state("GRACE", f"{no_face_duration:.0f}s / {self.grace_period}s")
                    logger.debug(f"⏳ GRACE: {no_face_duration:.0f}s / {self.grace_period}s elapsed")
                else:
                    # Grace exceeded - send warning
                    if previous_state != "NO_FACE":
                        logger.warning(f"⚠️ NO FACE: Grace period exceeded ({no_face_duration:.0f}s)")
                        
                        # Send desktop notification (soft warning)
                        if self.notifier.should_send_alert(self.alert_cooldown):
                            alert = SecurityAlert(
                                timestamp=self.last_check_time.isoformat(),
                                alert_type=AlertType.NO_FACE,
                                message=f"⚠️ No face detected for {no_face_duration:.0f} seconds. Are you still there?",
                                snapshot_path=snapshot_path,
                                detected_faces_count=0
                            )
                            self.notifier.send_alert(alert)
                            action_taken.append("desktop_notification")
                
                return {
                    "status": "no_faces",
                    "state": self.current_state,
                    "grace_remaining": max(0, self.grace_period - no_face_duration),
                    "timestamp": self.last_check_time.isoformat(),
                    "snapshot_path": snapshot_path,
                    "action_taken": action_taken
                }
            
            # === SCENARIO 3: INTRUDER DETECTED ===
            if unknown_faces:
                self.unauthorized_detections += 1
                self.no_face_start_time = None  # Reset grace timer
                
                logger.critical(f"🚨 INTRUDER DETECTED! {len(unknown_faces)} unauthorized face(s)!")
                
                # Start unauthorized timer if not already started
                if self.unauthorized_start_time is None:
                    self.unauthorized_start_time = datetime.now()
                    self._transition_state("UNAUTHORIZED", f"{len(unknown_faces)} intruder(s)")
                    logger.warning(f"🔴 UNAUTHORIZED: Lock delay started ({self.lock_delay}s)")
                
                # Check lock delay
                unauthorized_duration = (datetime.now() - self.unauthorized_start_time).total_seconds()
                
                # 🎬 CHECK FOR CRITICAL APPS BEFORE TAKING ACTION!
                critical_app_running = self._check_critical_apps_running()
                
                if critical_app_running:
                    logger.warning(f"🎬 CRITICAL APP RUNNING: {critical_app_running}")
                    logger.warning(f"⚠️ Suppressing lock action to protect ongoing work!")
                    self._transition_state("UNAUTHORIZED", f"critical app: {critical_app_running}")
                    
                    # Still send SILENT alert (email/Discord only, no lock)
                    if self.notifier.should_send_alert(self.alert_cooldown):
                        alert = SecurityAlert(
                            timestamp=self.last_check_time.isoformat(),
                            alert_type=AlertType.UNAUTHORIZED_ACCESS,
                            message=f"⚠️ INTRUDER DETECTED (but {critical_app_running} is running)\n🎬 Screen lock suppressed to protect critical task.\n{len(unknown_faces)} unknown face(s) detected.",
                            snapshot_path=snapshot_path,
                            detected_faces_count=len(detections)
                        )
                        
                        self.notifier.send_alert(alert)
                        action_taken.append("silent_alert")
                        logger.warning("📧 SILENT ALERT SENT: Intruder detected, but critical app protected!")
                    
                    return {
                        "status": "success",
                        "state": self.current_state,
                        "critical_app_running": critical_app_running,
                        "action_suppressed": True,
                        "timestamp": self.last_check_time.isoformat(),
                        "snapshot_path": snapshot_path,
                        "detected_faces_count": len(detections),
                        "authorized_faces_count": len(recognized_faces),
                        "unknown_faces_count": len(unknown_faces),
                        "recognized_faces": recognized_faces,
                        "unknown_faces": unknown_faces,
                        "action_taken": action_taken,
                        "alert_sent": True
                    }
                
                # === TIER 1: Short unauthorized duration (< lock_delay) ===
                if unauthorized_duration < self.lock_delay:
                    logger.warning(f"⏱️ TIER 1: Intruder detected, waiting {self.lock_delay - unauthorized_duration:.1f}s before locking...")
                    
                    # Take screenshot + send email (no lock yet)
                    if self.notifier.should_send_alert(self.alert_cooldown):
                        alert = SecurityAlert(
                            timestamp=self.last_check_time.isoformat(),
                            alert_type=AlertType.UNAUTHORIZED_ACCESS,
                            message=f"⚠️ Intruder detected! Lock in {self.lock_delay - unauthorized_duration:.0f}s...\n{len(unknown_faces)} unknown face(s) detected.",
                            snapshot_path=snapshot_path,
                            detected_faces_count=len(detections)
                        )
                        
                        self.notifier.send_alert(alert)
                        action_taken.append("screenshot")
                        action_taken.append("email_alert")
                    
                    return {
                        "status": "success",
                        "state": self.current_state,
                        "lock_in": self.lock_delay - unauthorized_duration,
                        "timestamp": self.last_check_time.isoformat(),
                        "snapshot_path": snapshot_path,
                        "detected_faces_count": len(detections),
                        "unknown_faces_count": len(unknown_faces),
                        "action_taken": action_taken
                    }
                
                # === TIER 2: Lock delay exceeded - FULL LOCKDOWN ===
                logger.critical(f"🔒 TIER 2: Lock delay exceeded ({unauthorized_duration:.1f}s) - LOCKING NOW!")
                self._transition_state("LOCKED", "intruder lock initiated")
                
                # 🔐 TAKE IMMEDIATE ACTION AGAINST INTRUDER!
                # Play alarm sound first (non-blocking)
                if self.play_alarm_on_intruder:
                    try:
                        self.system_actions.play_alarm_sound()
                        action_taken.append("alarm")
                    except Exception as e:
                        logger.error(f"Failed to play alarm: {e}")
                
                # Lock screen to block intruder access
                if self.auto_lock_on_intruder:
                    try:
                        logger.warning("🔒 LOCKING SCREEN TO BLOCK INTRUDER!")
                        lock_success = self.system_actions.lock_screen()
                        if lock_success:
                            logger.info("✅ Screen locked successfully - intruder blocked!")
                            action_taken.append("screen_lock")
                        else:
                            logger.error("❌ Failed to lock screen - check permissions!")
                    except Exception as e:
                        logger.error(f"❌ Lock screen failed: {e}")
                
                # Optional: Put computer to sleep (nuclear option)
                if self.auto_sleep_on_intruder:
                    try:
                        logger.warning("😴 PUTTING COMPUTER TO SLEEP!")
                        self.system_actions.sleep_computer()
                        action_taken.append("sleep")
                    except Exception as e:
                        logger.error(f"❌ Sleep failed: {e}")
                
                # Send alert (if cooldown period passed)
                if self.notifier.should_send_alert(self.alert_cooldown):
                    alert = SecurityAlert(
                        timestamp=self.last_check_time.isoformat(),
                        alert_type=AlertType.UNAUTHORIZED_ACCESS,
                        message=f"🚨 LOCKDOWN! {len(unknown_faces)} intruder(s) detected!\nScreen locked after {unauthorized_duration:.0f}s delay.",
                        snapshot_path=snapshot_path,
                        detected_faces_count=len(detections)
                    )
                    
                    self.notifier.send_alert(alert)
                    action_taken.append("email_alert")
                    logger.warning("📧 ALERT SENT: Unauthorized access - system locked!")
                
                return {
                    "status": "success",
                    "state": self.current_state,
                    "timestamp": self.last_check_time.isoformat(),
                    "snapshot_path": snapshot_path,
                    "detected_faces_count": len(detections),
                    "authorized_faces_count": len(recognized_faces),
                    "unknown_faces_count": len(unknown_faces),
                    "recognized_faces": recognized_faces,
                    "unknown_faces": unknown_faces,
                    "action_taken": action_taken,
                    "alert_sent": True
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
    
    def enroll_owner_from_file(self, image_path: str, user_name: str = "Owner", replace_existing: bool = False) -> bool:
        """
        Enroll owner from an image file.
        
        Args:
            image_path: Path to image file
            user_name: Name for this authorized user
            replace_existing: If True, replace all existing encodings for this user
        
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
            
            # Enroll (pass replace parameter to recognizer)
            success = self.recognizer.enroll_user(user_name, face_encoding, replace=replace_existing)
            
            if success:
                logger.info(f"✅ {user_name} enrolled successfully!")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Enrollment failed: {e}")
            return False
    
    def get_stats(self) -> Dict:
        """Get comprehensive security statistics."""
        stats = {
            "enabled": self.enabled,
            "current_state": self.current_state,  # Added for dashboard
            "total_checks": self.total_checks,
            "unauthorized_detections": self.unauthorized_detections,
            "threats_detected": self.unauthorized_detections,  # Alias for compatibility
            "authorized_users_count": len(self.recognizer.get_authorized_users()),  # Added for dashboard
            "last_check_time": self.last_check_time.isoformat() if self.last_check_time else None,
            "camera": {
                "initialized": self.camera._is_initialized
            },
            "detector": self.detector.get_stats(),
            "recognizer": self.recognizer.get_stats(),
            "notifier": self.notifier.get_stats()
        }
        
        # Add pattern detection stats if enabled
        if self.pattern_detector:
            stats["intruder_patterns"] = self.pattern_detector.get_stats()
        
        return stats
    
    def cleanup(self):
        """Cleanup resources."""
        self.camera.release()
        logger.info("🧹 Security manager cleaned up")
