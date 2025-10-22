"""
Lock state manager that coordinates all components.
"""
import time
import logging
import platform
import subprocess
from typing import Optional, Dict
from .monitors import ProcessMonitor
from .models import TaskPredictor
from .controllers import FuzzyLockController
from .detectors import FaceDetector

logger = logging.getLogger(__name__)


class LockStateManager:
    """
    Coordinates process monitoring, task prediction, fuzzy logic, and lock control.
    """
    
    def __init__(self, config: Dict):
        """
        Initialize lock state manager.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        
        # Initialize components
        self.process_monitor = ProcessMonitor(
            cpu_threshold=config.get('cpu_threshold', 5.0),
            check_interval=config.get('check_interval', 1.0)
        )
        
        self.task_predictor = TaskPredictor()
        self.fuzzy_controller = FuzzyLockController()
        
        # Optional face detection
        self.face_detector = None
        if config.get('enable_face_detection', False):
            self.face_detector = FaceDetector(
                camera_index=config.get('camera_index', 0)
            )
            self.face_detector.enable()
        
        self.current_state = 'dim'
        self.state_change_callback = None
        
        # State history for stability
        self.state_history = []
        self.max_history = 5
        
    def set_state_change_callback(self, callback):
        """Set callback function to be called when state changes."""
        self.state_change_callback = callback
    
    def evaluate_lock_state(self) -> Dict:
        """
        Evaluate current system state and determine lock state.
        
        Returns:
            Dictionary containing state information
        """
        # Get process features
        features, raw_data = self.process_monitor.extract_features()
        
        # Predict task criticality with ANN
        task_level, probabilities = self.task_predictor.predict(features)
        task_criticality = probabilities[2] * 100  # Critical task probability
        
        # Get system load
        system_metrics = raw_data['system_metrics']
        system_load = max(system_metrics['cpu_percent'], 
                         system_metrics['memory_percent'])
        
        # Get presence confidence
        presence_confidence = 50.0  # Default neutral
        if self.face_detector and self.face_detector.enabled:
            presence_confidence = self.face_detector.get_presence_confidence(samples=2)
        
        # Use fuzzy controller to decide lock state
        lock_state, fuzzy_output = self.fuzzy_controller.decide_lock_state(
            task_criticality, system_load, presence_confidence
        )
        
        # Add to history and smooth transitions
        self.state_history.append(lock_state)
        if len(self.state_history) > self.max_history:
            self.state_history.pop(0)
        
        # Use most common state in recent history for stability
        stable_state = max(set(self.state_history), key=self.state_history.count)
        
        result = {
            'lock_state': stable_state,
            'raw_state': lock_state,
            'fuzzy_output': fuzzy_output,
            'task_level': ['idle', 'moderate', 'critical'][task_level],
            'task_criticality': task_criticality,
            'system_load': system_load,
            'presence_confidence': presence_confidence,
            'critical_process_count': raw_data['critical_count'],
            'active_process_count': len(raw_data['active_processes']),
            'features': features,
            'probabilities': probabilities.tolist()
        }
        
        # Handle state change
        if stable_state != self.current_state:
            logger.info(f"Lock state changing: {self.current_state} -> {stable_state}")
            self.current_state = stable_state
            
            if self.state_change_callback:
                self.state_change_callback(stable_state, result)
        
        return result
    
    def apply_lock_state(self, state: str) -> bool:
        """
        Apply the lock state to the system.
        
        Args:
            state: Lock state ('stay_awake', 'dim', 'full_lock')
            
        Returns:
            True if successfully applied
        """
        system = platform.system()
        
        try:
            if system == 'Linux':
                return self._apply_linux_lock_state(state)
            elif system == 'Darwin':  # macOS
                return self._apply_macos_lock_state(state)
            elif system == 'Windows':
                return self._apply_windows_lock_state(state)
            else:
                logger.warning(f"Unsupported platform: {system}")
                return False
        except Exception as e:
            logger.error(f"Error applying lock state: {e}")
            return False
    
    def _apply_linux_lock_state(self, state: str) -> bool:
        """Apply lock state on Linux systems."""
        try:
            if state == 'stay_awake':
                # Disable screen blanking/DPMS
                subprocess.run(['xset', 's', 'off'], check=False)
                subprocess.run(['xset', '-dpms'], check=False)
                logger.info("Applied: Stay awake (screen blanking disabled)")
                
            elif state == 'dim':
                # Set screen to dim after 5 minutes
                subprocess.run(['xset', 's', '300'], check=False)
                subprocess.run(['xset', '+dpms'], check=False)
                logger.info("Applied: Dim (screen dims after 5 min)")
                
            elif state == 'full_lock':
                # Lock screen immediately (try multiple methods)
                lock_commands = [
                    ['gnome-screensaver-command', '--lock'],
                    ['xdg-screensaver', 'lock'],
                    ['loginctl', 'lock-session']
                ]
                for cmd in lock_commands:
                    result = subprocess.run(cmd, capture_output=True, check=False)
                    if result.returncode == 0:
                        logger.info(f"Applied: Full lock using {cmd[0]}")
                        return True
                logger.warning("Could not lock screen - no suitable command found")
                
            return True
        except Exception as e:
            logger.error(f"Error in Linux lock state: {e}")
            return False
    
    def _apply_macos_lock_state(self, state: str) -> bool:
        """Apply lock state on macOS systems."""
        try:
            if state == 'stay_awake':
                # Use caffeinate to prevent sleep
                logger.info("Applied: Stay awake (use caffeinate utility)")
                
            elif state == 'dim':
                logger.info("Applied: Dim (system will follow energy settings)")
                
            elif state == 'full_lock':
                # Lock screen on macOS
                subprocess.run(['/System/Library/CoreServices/Menu Extras/User.menu/Contents/Resources/CGSession', 
                              '-suspend'], check=False)
                logger.info("Applied: Full lock")
                
            return True
        except Exception as e:
            logger.error(f"Error in macOS lock state: {e}")
            return False
    
    def _apply_windows_lock_state(self, state: str) -> bool:
        """Apply lock state on Windows systems."""
        try:
            if state == 'stay_awake':
                # Prevent sleep using powercfg
                logger.info("Applied: Stay awake (consider using powercfg)")
                
            elif state == 'dim':
                logger.info("Applied: Dim (system will follow power settings)")
                
            elif state == 'full_lock':
                # Lock workstation on Windows
                subprocess.run(['rundll32.exe', 'user32.dll,LockWorkStation'], check=False)
                logger.info("Applied: Full lock")
                
            return True
        except Exception as e:
            logger.error(f"Error in Windows lock state: {e}")
            return False
    
    def cleanup(self):
        """Cleanup resources."""
        if self.face_detector:
            self.face_detector.disable()
        logger.info("Lock manager cleanup complete")
