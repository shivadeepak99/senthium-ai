"""
Failsafe Timer Module
Security mechanism to prevent indefinite system unlock

Tracks how long the system has been kept awake and enforces
a maximum duration limit as a security failsafe.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional


class FailsafeTimer:
    """
    Tracks awake duration and enforces maximum limit
    
    Security feature to prevent bugs or misconfigurations from
    leaving a system unlocked indefinitely. After max_duration,
    the stay-awake lock is forcibly released.
    """
    
    def __init__(self, max_duration_seconds: int = 14400):
        """
        Initialize failsafe timer
        
        Args:
            max_duration_seconds: Maximum time to stay awake (default: 4 hours)
        """
        self.max_duration = max_duration_seconds
        self.awake_since: Optional[datetime] = None
        self.logger = logging.getLogger(__name__)
        self._warning_sent = False
        
        # Warning threshold at 90% of max duration
        self.warning_threshold = max_duration_seconds * 0.9
        
        self.logger.info(f"Failsafe timer initialized (max: {self._format_duration(max_duration_seconds)})")
    
    def start(self):
        """Start tracking awake time"""
        if self.awake_since is None:
            self.awake_since = datetime.now()
            self._warning_sent = False
            self.logger.info(
                f"⏱️  Failsafe timer started. "
                f"Max duration: {self._format_duration(self.max_duration)}"
            )
    
    def reset(self):
        """Reset timer when going back to sleep"""
        if self.awake_since is not None:
            duration = (datetime.now() - self.awake_since).total_seconds()
            self.logger.info(
                f"🛌 Awake session ended. "
                f"Duration: {self._format_duration(duration)}"
            )
            self.awake_since = None
            self._warning_sent = False
    
    def check_exceeded(self) -> bool:
        """
        Check if maximum duration has been exceeded
        
        Returns:
            True if failsafe limit reached, False otherwise
        """
        if self.awake_since is None:
            return False
        
        elapsed = self.get_elapsed_seconds()
        
        # Check for warning threshold
        if not self._warning_sent and elapsed >= self.warning_threshold:
            remaining = self.max_duration - elapsed
            self.logger.warning(
                f"⚠️  Approaching failsafe limit! "
                f"Awake for {self._format_duration(elapsed)}, "
                f"{self._format_duration(remaining)} remaining"
            )
            self._warning_sent = True
        
        # Check for max duration exceeded
        if elapsed >= self.max_duration:
            self.logger.critical(
                f"🚨 FAILSAFE TRIGGERED! "
                f"Awake for {self._format_duration(elapsed)} "
                f"(max: {self._format_duration(self.max_duration)})"
            )
            return True
        
        return False
    
    def get_elapsed_seconds(self) -> float:
        """
        Get elapsed time since timer started
        
        Returns:
            Seconds elapsed, or 0.0 if timer not started
        """
        if self.awake_since is None:
            return 0.0
        
        return (datetime.now() - self.awake_since).total_seconds()
    
    def get_remaining_seconds(self) -> float:
        """
        Get remaining time before failsafe triggers
        
        Returns:
            Seconds remaining, or max_duration if timer not started
        """
        if self.awake_since is None:
            return float(self.max_duration)
        
        remaining = self.max_duration - self.get_elapsed_seconds()
        return max(0.0, remaining)
    
    def get_progress_percent(self) -> float:
        """
        Get progress toward failsafe limit as percentage
        
        Returns:
            Percentage (0-100), or 0.0 if timer not started
        """
        if self.awake_since is None:
            return 0.0
        
        elapsed = self.get_elapsed_seconds()
        progress = (elapsed / self.max_duration) * 100.0
        return min(100.0, progress)
    
    def is_active(self) -> bool:
        """Check if timer is currently running"""
        return self.awake_since is not None
    
    def _format_duration(self, seconds: float) -> str:
        """
        Format duration in human-readable format
        
        Args:
            seconds: Duration in seconds
            
        Returns:
            Formatted string (e.g., "2h 30m", "45m 30s", "30s")
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            if minutes > 0:
                return f"{hours}h {minutes}m"
            else:
                return f"{hours}h"
        elif minutes > 0:
            if secs > 0:
                return f"{minutes}m {secs}s"
            else:
                return f"{minutes}m"
        else:
            return f"{secs}s"
    
    def get_status_dict(self) -> dict:
        """
        Get current timer status as dictionary
        
        Returns:
            Dictionary with timer status information
        """
        return {
            'active': self.is_active(),
            'elapsed_seconds': self.get_elapsed_seconds(),
            'remaining_seconds': self.get_remaining_seconds(),
            'progress_percent': round(self.get_progress_percent(), 1),
            'max_duration_seconds': self.max_duration,
            'started_at': self.awake_since.isoformat() if self.awake_since else None,
        }


# Example usage / testing
if __name__ == '__main__':
    from utils.logger import setup_logger
    import time
    
    # Setup logging
    logger = setup_logger('senthium.failsafe', level='DEBUG')
    
    print("🛡️  Senthium Failsafe Timer Test")
    print("=" * 60)
    
    # Test with short duration for demo (30 seconds)
    timer = FailsafeTimer(max_duration_seconds=30)
    
    print("\n📋 Test 1: Start timer")
    timer.start()
    print(f"  Active: {timer.is_active()}")
    print(f"  Status: {timer.get_status_dict()}")
    
    print("\n📋 Test 2: Check progress over time")
    for i in range(1, 6):
        time.sleep(5)
        elapsed = timer.get_elapsed_seconds()
        remaining = timer.get_remaining_seconds()
        progress = timer.get_progress_percent()
        
        print(f"  After {i*5}s:")
        print(f"    Elapsed: {elapsed:.1f}s")
        print(f"    Remaining: {remaining:.1f}s")
        print(f"    Progress: {progress:.1f}%")
        print(f"    Exceeded: {timer.check_exceeded()}")
    
    print("\n📋 Test 3: Wait for warning threshold (27s)")
    time.sleep(2)
    timer.check_exceeded()
    
    print("\n📋 Test 4: Wait for failsafe trigger (30s)")
    time.sleep(3)
    exceeded = timer.check_exceeded()
    print(f"  Failsafe triggered: {exceeded}")
    
    print("\n📋 Test 5: Reset timer")
    timer.reset()
    print(f"  Active: {timer.is_active()}")
    print(f"  Elapsed: {timer.get_elapsed_seconds():.1f}s")
    
    print("\n✅ Failsafe timer test complete!")
