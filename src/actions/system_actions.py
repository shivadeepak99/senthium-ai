"""
System Actions - Lock screen, sleep, shutdown, etc.

Your bodyguard's enforcement tools! 🔐💪
"""

import ctypes
import logging
import platform
from typing import Optional


logger = logging.getLogger(__name__)


class SystemActions:
    """
    Handles system-level actions for security enforcement.
    
    When alerts aren't enough, this babe TAKES ACTION! 🚨🔒
    """
    
    def __init__(self):
        """Initialize system actions handler."""
        self.os_type = platform.system()
        logger.info(f"🖥️ System actions initialized for {self.os_type}")
    
    def lock_screen(self) -> bool:
        """
        Lock the computer screen immediately.
        
        Returns:
            True if lock successful, False otherwise
        """
        try:
            if self.os_type == "Windows":
                # Use Windows API to lock workstation
                # LockWorkStation() from user32.dll
                ctypes.windll.user32.LockWorkStation()
                logger.info("🔒 Screen LOCKED! Intruder blocked!")
                return True
            
            elif self.os_type == "Darwin":  # macOS
                import subprocess
                subprocess.call(["/System/Library/CoreServices/Menu Extras/User.menu/Contents/Resources/CGSession", "-suspend"])
                logger.info("🔒 Screen LOCKED! (macOS)")
                return True
            
            elif self.os_type == "Linux":
                import subprocess
                # Try multiple lock commands (depends on DE)
                for cmd in ["gnome-screensaver-command -l", "xdg-screensaver lock", "loginctl lock-session"]:
                    try:
                        subprocess.call(cmd.split())
                        logger.info("🔒 Screen LOCKED! (Linux)")
                        return True
                    except:
                        continue
                
                logger.warning("⚠️ Could not find screen lock command on Linux")
                return False
            
            else:
                logger.warning(f"⚠️ Screen lock not supported on {self.os_type}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to lock screen: {e}")
            return False
    
    def sleep_computer(self) -> bool:
        """
        Put the computer to sleep immediately.
        
        Returns:
            True if sleep successful, False otherwise
        """
        try:
            if self.os_type == "Windows":
                # Suspend system (sleep mode)
                ctypes.windll.powrprof.SetSuspendState(0, 1, 0)
                logger.info("😴 Computer put to SLEEP!")
                return True
            
            elif self.os_type == "Darwin":  # macOS
                import subprocess
                subprocess.call(["pmset", "sleepnow"])
                logger.info("😴 Computer put to SLEEP! (macOS)")
                return True
            
            elif self.os_type == "Linux":
                import subprocess
                subprocess.call(["systemctl", "suspend"])
                logger.info("😴 Computer put to SLEEP! (Linux)")
                return True
            
            else:
                logger.warning(f"⚠️ Sleep not supported on {self.os_type}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to sleep computer: {e}")
            return False
    
    def shutdown_computer(self, delay_seconds: int = 30) -> bool:
        """
        Shutdown the computer after a delay.
        
        Args:
            delay_seconds: Seconds to wait before shutdown
            
        Returns:
            True if shutdown initiated, False otherwise
        """
        try:
            if self.os_type == "Windows":
                import subprocess
                # /s = shutdown, /t = time in seconds
                subprocess.Popen(["shutdown", "/s", "/t", str(delay_seconds)])
                logger.warning(f"🚨 SHUTDOWN initiated in {delay_seconds}s!")
                return True
            
            elif self.os_type == "Darwin":  # macOS
                import subprocess
                subprocess.Popen(["sudo", "shutdown", "-h", f"+{delay_seconds // 60}"])
                logger.warning(f"🚨 SHUTDOWN initiated in {delay_seconds}s! (macOS)")
                return True
            
            elif self.os_type == "Linux":
                import subprocess
                subprocess.Popen(["shutdown", "-h", f"+{delay_seconds // 60}"])
                logger.warning(f"🚨 SHUTDOWN initiated in {delay_seconds}s! (Linux)")
                return True
            
            else:
                logger.warning(f"⚠️ Shutdown not supported on {self.os_type}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to shutdown computer: {e}")
            return False
    
    def cancel_shutdown(self) -> bool:
        """
        Cancel a pending shutdown.
        
        Returns:
            True if cancellation successful, False otherwise
        """
        try:
            if self.os_type == "Windows":
                import subprocess
                subprocess.call(["shutdown", "/a"])
                logger.info("✅ Shutdown cancelled")
                return True
            
            elif self.os_type in ["Darwin", "Linux"]:
                import subprocess
                subprocess.call(["shutdown", "-c"])
                logger.info("✅ Shutdown cancelled")
                return True
            
            else:
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to cancel shutdown: {e}")
            return False
    
    def play_alarm_sound(self, duration_seconds: float = 2.0) -> bool:
        """
        Play an alarm sound to alert user.
        
        Args:
            duration_seconds: How long to play alarm
            
        Returns:
            True if sound played, False otherwise
        """
        try:
            if self.os_type == "Windows":
                import winsound
                # Play system exclamation sound
                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
                logger.info("🔔 Alarm sound played!")
                return True
            
            else:
                # Fallback: system beep
                print("\a" * 5)  # ASCII bell character
                logger.info("🔔 Alarm beep sent!")
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to play alarm: {e}")
            return False
    
    def get_available_actions(self) -> list:
        """
        Get list of available actions on this OS.
        
        Returns:
            List of action names (strings)
        """
        return ["lock_screen", "sleep_computer", "shutdown_computer", "play_alarm_sound"]
