"""
Intruder Pattern Detection - Track and identify repeat intruders

Smart detection of persistent unauthorized access attempts! 🔍🚨
"""

import logging
import json
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from collections import defaultdict

logger = logging.getLogger(__name__)


class IntruderPattern:
    """
    Represents a detected intruder pattern (repeat offender).
    """
    def __init__(self, pattern_id: str, first_seen: str, count: int = 1):
        self.pattern_id = pattern_id
        self.first_seen = first_seen
        self.last_seen = first_seen
        self.count = count
        self.face_encodings: List[np.ndarray] = []
        self.timestamps: List[str] = [first_seen]
        self.snapshot_paths: List[str] = []
    
    def add_occurrence(self, timestamp: str, encoding: Optional[np.ndarray] = None, snapshot: Optional[str] = None):
        """Add another occurrence of this intruder."""
        self.count += 1
        self.last_seen = timestamp
        self.timestamps.append(timestamp)
        
        if encoding is not None:
            self.face_encodings.append(encoding)
        
        if snapshot:
            self.snapshot_paths.append(snapshot)
    
    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "pattern_id": self.pattern_id,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "count": self.count,
            "timestamps": self.timestamps,
            "snapshot_paths": self.snapshot_paths,
            "threat_level": self.get_threat_level()
        }
    
    def get_threat_level(self) -> str:
        """Calculate threat level based on count and recency."""
        if self.count >= 10:
            return "CRITICAL"
        elif self.count >= 5:
            return "HIGH"
        elif self.count >= 3:
            return "MEDIUM"
        else:
            return "LOW"


class IntruderPatternDetector:
    """
    Detect and track repeat intruders.
    
    Features:
    - 🔍 Face embedding clustering to identify same person
    - 📊 Track occurrence count and timestamps
    - 🚨 Alert on repeat offenders (3+ detections in 24h)
    - 💾 Persist patterns to disk
    
    Your security system has a memory! 🧠
    """
    
    def __init__(
        self,
        patterns_file: str = "logs/security/intruder_patterns.json",
        similarity_threshold: float = 0.6,
        alert_threshold: int = 3,
        time_window_hours: int = 24
    ):
        """
        Initialize pattern detector.
        
        Args:
            patterns_file: Where to store detected patterns
            similarity_threshold: Face distance threshold for same person (lower = stricter)
            alert_threshold: Number of detections before alerting
            time_window_hours: Time window for counting detections
        """
        self.patterns_file = Path(patterns_file)
        self.patterns_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.similarity_threshold = similarity_threshold
        self.alert_threshold = alert_threshold
        self.time_window = timedelta(hours=time_window_hours)
        
        # Load existing patterns
        self.patterns: Dict[str, IntruderPattern] = {}
        self._load_patterns()
        
        logger.info(f"🔍 Intruder pattern detector initialized ({len(self.patterns)} known patterns)")
    
    def _load_patterns(self):
        """Load patterns from disk."""
        if not self.patterns_file.exists():
            return
        
        try:
            with open(self.patterns_file, 'r') as f:
                data = json.load(f)
            
            # Reconstruct pattern objects
            for pattern_id, pattern_data in data.items():
                pattern = IntruderPattern(
                    pattern_id=pattern_id,
                    first_seen=pattern_data['first_seen'],
                    count=pattern_data['count']
                )
                pattern.last_seen = pattern_data['last_seen']
                pattern.timestamps = pattern_data['timestamps']
                pattern.snapshot_paths = pattern_data.get('snapshot_paths', [])
                
                self.patterns[pattern_id] = pattern
            
            logger.debug(f"📂 Loaded {len(self.patterns)} intruder patterns")
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to load patterns: {e}")
    
    def _save_patterns(self):
        """Save patterns to disk."""
        try:
            # Convert to JSON-serializable format
            data = {
                pattern_id: pattern.to_dict()
                for pattern_id, pattern in self.patterns.items()
            }
            
            with open(self.patterns_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.debug(f"💾 Saved {len(self.patterns)} intruder patterns")
            
        except Exception as e:
            logger.error(f"❌ Failed to save patterns: {e}")
    
    def record_intruder(
        self,
        face_encoding: np.ndarray,
        timestamp: Optional[str] = None,
        snapshot_path: Optional[str] = None
    ) -> Tuple[bool, Optional[IntruderPattern]]:
        """
        Record an intruder detection and check for patterns.
        
        Args:
            face_encoding: Face encoding of intruder
            timestamp: Detection timestamp (ISO format)
            snapshot_path: Path to snapshot photo
        
        Returns:
            Tuple of (is_repeat_offender, pattern_object)
        """
        if timestamp is None:
            timestamp = datetime.now().isoformat()
        
        # Find matching pattern (same face)
        matching_pattern = self._find_matching_pattern(face_encoding)
        
        if matching_pattern:
            # Add to existing pattern
            matching_pattern.add_occurrence(timestamp, face_encoding, snapshot_path)
            logger.info(f"🔍 Repeat intruder detected! Pattern: {matching_pattern.pattern_id}, Count: {matching_pattern.count}")
            
            # Check if threshold reached
            recent_count = self._count_recent_occurrences(matching_pattern)
            is_repeat = recent_count >= self.alert_threshold
            
            if is_repeat:
                logger.warning(f"🚨 REPEAT OFFENDER! {recent_count} detections in last {self.time_window.total_seconds()/3600:.0f}h")
            
        else:
            # Create new pattern
            pattern_id = f"intruder_{len(self.patterns) + 1}_{datetime.now().strftime('%Y%m%d')}"
            matching_pattern = IntruderPattern(pattern_id, timestamp)
            matching_pattern.add_occurrence(timestamp, face_encoding, snapshot_path)
            
            self.patterns[pattern_id] = matching_pattern
            logger.info(f"🆕 New intruder pattern created: {pattern_id}")
            
            is_repeat = False
        
        # Save patterns
        self._save_patterns()
        
        return (is_repeat, matching_pattern)
    
    def _find_matching_pattern(self, face_encoding: np.ndarray) -> Optional[IntruderPattern]:
        """
        Find existing pattern that matches this face.
        
        Args:
            face_encoding: Face encoding to match
        
        Returns:
            Matching pattern or None
        """
        for pattern in self.patterns.values():
            if not pattern.face_encodings:
                continue
            
            # Compare against all stored encodings for this pattern
            for stored_encoding in pattern.face_encodings:
                distance = np.linalg.norm(face_encoding - stored_encoding)
                
                if distance <= self.similarity_threshold:
                    logger.debug(f"✅ Match found: {pattern.pattern_id} (distance: {distance:.3f})")
                    return pattern
        
        return None
    
    def _count_recent_occurrences(self, pattern: IntruderPattern) -> int:
        """
        Count occurrences within time window.
        
        Args:
            pattern: Pattern to check
        
        Returns:
            Count of recent occurrences
        """
        now = datetime.now()
        cutoff = now - self.time_window
        
        recent_count = 0
        for timestamp_str in pattern.timestamps:
            try:
                timestamp = datetime.fromisoformat(timestamp_str)
                if timestamp >= cutoff:
                    recent_count += 1
            except:
                pass
        
        return recent_count
    
    def get_active_patterns(self, time_window_hours: Optional[int] = None) -> List[IntruderPattern]:
        """
        Get patterns with recent activity.
        
        Args:
            time_window_hours: Time window (default: use configured window)
        
        Returns:
            List of active patterns
        """
        window = timedelta(hours=time_window_hours) if time_window_hours else self.time_window
        cutoff = datetime.now() - window
        
        active = []
        for pattern in self.patterns.values():
            try:
                last_seen = datetime.fromisoformat(pattern.last_seen)
                if last_seen >= cutoff:
                    active.append(pattern)
            except:
                pass
        
        return sorted(active, key=lambda p: p.count, reverse=True)
    
    def get_top_threats(self, limit: int = 5) -> List[IntruderPattern]:
        """
        Get top threat patterns by count.
        
        Args:
            limit: Max number to return
        
        Returns:
            List of top threat patterns
        """
        return sorted(
            self.patterns.values(),
            key=lambda p: p.count,
            reverse=True
        )[:limit]
    
    def get_stats(self) -> dict:
        """Get pattern detection statistics."""
        total_patterns = len(self.patterns)
        total_detections = sum(p.count for p in self.patterns.values())
        active_patterns = len(self.get_active_patterns())
        
        return {
            "total_patterns": total_patterns,
            "total_detections": total_detections,
            "active_patterns_24h": active_patterns,
            "alert_threshold": self.alert_threshold,
            "time_window_hours": self.time_window.total_seconds() / 3600
        }
    
    def clear_old_patterns(self, days: int = 30):
        """
        Remove patterns older than specified days.
        
        Args:
            days: Age threshold in days
        """
        cutoff = datetime.now() - timedelta(days=days)
        
        removed_count = 0
        patterns_to_remove = []
        
        for pattern_id, pattern in self.patterns.items():
            try:
                last_seen = datetime.fromisoformat(pattern.last_seen)
                if last_seen < cutoff:
                    patterns_to_remove.append(pattern_id)
            except:
                pass
        
        for pattern_id in patterns_to_remove:
            del self.patterns[pattern_id]
            removed_count += 1
        
        if removed_count > 0:
            self._save_patterns()
            logger.info(f"🗑️ Removed {removed_count} old patterns (>{days} days)")
        
        return removed_count
