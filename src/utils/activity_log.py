"""
Activity logger - tracks what kept the system awake.
Provides analytics and insights into power management decisions.

This module logs every stay-awake session with details about:
- What triggered it (rule match vs wrapper lock)
- How long it lasted
- System metrics at the time
- Process/command information

Logs are stored as JSONL (JSON Lines) files, one per day.
"""

import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict


@dataclass
class ActivitySession:
    """Represents a period when system was kept awake"""
    start_time: datetime
    end_time: Optional[datetime]
    duration_seconds: float
    trigger_reason: str  # 'rule_match' or 'wrapper_lock'
    rule_name: Optional[str]  # Which rule matched (if applicable)
    process_name: Optional[str]  # Wrapper command (if applicable)
    metrics_snapshot: Dict  # CPU, disk, network at start
    
    def to_dict(self) -> Dict:
        """Convert to dictionary with datetime serialization"""
        data = asdict(self)
        data['start_time'] = self.start_time.isoformat()
        if self.end_time:
            data['end_time'] = self.end_time.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ActivitySession':
        """Create from dictionary with datetime deserialization"""
        data['start_time'] = datetime.fromisoformat(data['start_time'])
        if data.get('end_time'):
            data['end_time'] = datetime.fromisoformat(data['end_time'])
        return cls(**data)


class ActivityLogger:
    """Logs and analyzes stay-awake sessions"""
    
    def __init__(self, log_dir: Optional[Path] = None):
        """
        Initialize activity logger.
        
        Args:
            log_dir: Directory for activity logs (default: logs/activity/)
        """
        if log_dir is None:
            log_dir = Path(__file__).parent.parent.parent / 'logs' / 'activity'
        
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.current_session: Optional[ActivitySession] = None
        self.logger = logging.getLogger(__name__)
    
    def start_session(
        self,
        reason: str,
        rule_name: Optional[str] = None,
        process_name: Optional[str] = None,
        metrics: Optional[Dict] = None
    ):
        """
        Start new activity session.
        
        Args:
            reason: Trigger reason ('rule_match' or 'wrapper_lock')
            rule_name: Name of matching rule (if applicable)
            process_name: Wrapper command (if applicable)
            metrics: System metrics snapshot
        """
        if self.current_session and self.current_session.end_time is None:
            # End previous session first
            self.logger.warning("Starting new session without ending previous one")
            self.end_session()
        
        self.current_session = ActivitySession(
            start_time=datetime.now(),
            end_time=None,
            duration_seconds=0.0,
            trigger_reason=reason,
            rule_name=rule_name,
            process_name=process_name,
            metrics_snapshot=metrics or {}
        )
        
        self.logger.info(f"Activity session started: {reason} ({rule_name or process_name or 'unknown'})")
    
    def end_session(self):
        """End current activity session and save to log"""
        if not self.current_session:
            self.logger.warning("No active session to end")
            return
        
        self.current_session.end_time = datetime.now()
        self.current_session.duration_seconds = (
            self.current_session.end_time - self.current_session.start_time
        ).total_seconds()
        
        # Save to file
        self._save_session(self.current_session)
        
        duration_str = str(timedelta(seconds=int(self.current_session.duration_seconds)))
        self.logger.info(
            f"Activity session ended: {self.current_session.trigger_reason} "
            f"(duration: {duration_str})"
        )
        
        self.current_session = None
    
    def _save_session(self, session: ActivitySession):
        """Save session to daily log file (JSONL format)"""
        date_str = session.start_time.strftime('%Y-%m-%d')
        log_file = self.log_dir / f'activity_{date_str}.jsonl'
        
        # Convert to JSON
        session_dict = session.to_dict()
        
        # Append to JSONL file (one JSON per line)
        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(session_dict) + '\n')
        except Exception as e:
            self.logger.error(f"Failed to save activity session: {e}")
    
    def get_daily_summary(self, date: Optional[datetime] = None) -> Dict:
        """
        Get summary of activity for a specific day.
        
        Args:
            date: Date to summarize (default: today)
            
        Returns:
            Dictionary with summary statistics
        """
        if date is None:
            date = datetime.now()
        
        date_str = date.strftime('%Y-%m-%d')
        log_file = self.log_dir / f'activity_{date_str}.jsonl'
        
        if not log_file.exists():
            return {
                'date': date_str,
                'total_sessions': 0,
                'total_duration_seconds': 0.0,
                'total_duration_human': '0:00:00',
                'by_rule': {},
                'by_hour': {},
                'by_trigger': {}
            }
        
        # Parse log file
        sessions = []
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        sessions.append(json.loads(line))
        except Exception as e:
            self.logger.error(f"Failed to read activity log: {e}")
            return {
                'date': date_str,
                'total_sessions': 0,
                'total_duration_seconds': 0.0,
                'error': str(e)
            }
        
        # Calculate summary
        total_duration = sum(s.get('duration_seconds', 0) for s in sessions)
        
        # By rule
        by_rule = {}
        for session in sessions:
            rule = session.get('rule_name') or session.get('process_name', 'unknown')
            if rule not in by_rule:
                by_rule[rule] = {'count': 0, 'duration': 0.0}
            by_rule[rule]['count'] += 1
            by_rule[rule]['duration'] += session.get('duration_seconds', 0)
        
        # By hour
        by_hour = {}
        for session in sessions:
            try:
                hour = datetime.fromisoformat(session['start_time']).hour
                if hour not in by_hour:
                    by_hour[hour] = {'count': 0, 'duration': 0.0}
                by_hour[hour]['count'] += 1
                by_hour[hour]['duration'] += session.get('duration_seconds', 0)
            except:
                pass
        
        # By trigger type
        by_trigger = {}
        for session in sessions:
            trigger = session.get('trigger_reason', 'unknown')
            if trigger not in by_trigger:
                by_trigger[trigger] = {'count': 0, 'duration': 0.0}
            by_trigger[trigger]['count'] += 1
            by_trigger[trigger]['duration'] += session.get('duration_seconds', 0)
        
        return {
            'date': date_str,
            'total_sessions': len(sessions),
            'total_duration_seconds': total_duration,
            'total_duration_human': str(timedelta(seconds=int(total_duration))),
            'by_rule': by_rule,
            'by_hour': by_hour,
            'by_trigger': by_trigger
        }
    
    def get_weekly_summary(self) -> Dict:
        """Get summary for the last 7 days"""
        summaries = []
        total_all_days = 0.0
        total_sessions = 0
        
        for i in range(7):
            date = datetime.now() - timedelta(days=i)
            summary = self.get_daily_summary(date)
            summaries.append(summary)
            total_all_days += summary['total_duration_seconds']
            total_sessions += summary['total_sessions']
        
        return {
            'period': 'Last 7 days',
            'daily_summaries': summaries,
            'total_sessions': total_sessions,
            'total_duration_seconds': total_all_days,
            'total_duration_human': str(timedelta(seconds=int(total_all_days))),
            'average_per_day': total_all_days / 7.0
        }


def format_duration(seconds: float) -> str:
    """Format duration in human-readable format"""
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds / 3600)
        minutes = int((seconds % 3600) / 60)
        return f"{hours}h {minutes}m"


def print_activity_summary(days: int = 1):
    """
    Print activity summary for recent days.
    
    Args:
        days: Number of days to show (default: 1)
    """
    activity_logger = ActivityLogger()
    
    print(f"\n{'='*70}")
    print(f"  Senthium Activity Summary")
    print(f"  Last {days} day{'s' if days > 1 else ''}")
    print(f"{'='*70}\n")
    
    total_all_days = 0.0
    total_sessions = 0
    
    for i in range(days):
        date = datetime.now() - timedelta(days=i)
        summary = activity_logger.get_daily_summary(date)
        
        if summary['total_sessions'] == 0:
            if i == 0:  # Show today even if empty
                print(f"[*] {summary['date']} (Today)")
                print(f"   No activity recorded")
                print()
            continue
        
        day_label = "Today" if i == 0 else "Yesterday" if i == 1 else ""
        print(f"[*] {summary['date']}{' (' + day_label + ')' if day_label else ''}")
        print(f"   Sessions: {summary['total_sessions']}")
        print(f"   Duration: {summary['total_duration_human']}")
        
        # Top rules
        if summary['by_rule']:
            print(f"   Top rules:")
            sorted_rules = sorted(
                summary['by_rule'].items(),
                key=lambda x: x[1]['duration'],
                reverse=True
            )
            for rule, stats in sorted_rules[:5]:  # Top 5
                duration_str = format_duration(stats['duration'])
                print(f"     • {rule}: {duration_str} ({stats['count']}x)")
        
        # By trigger type
        if summary.get('by_trigger'):
            print(f"   Triggers:")
            for trigger, stats in summary['by_trigger'].items():
                duration_str = format_duration(stats['duration'])
                trigger_label = "Rule Match" if trigger == "rule_match" else "Wrapper Lock"
                print(f"     • {trigger_label}: {duration_str} ({stats['count']}x)")
        
        print()
        total_all_days += summary['total_duration_seconds']
        total_sessions += summary['total_sessions']
    
    if days > 1 and total_sessions > 0:
        print(f"{'='*70}")
        total_human = str(timedelta(seconds=int(total_all_days)))
        avg_per_day = format_duration(total_all_days / days)
        print(f"  Total: {total_human} across {total_sessions} sessions")
        print(f"  Average: {avg_per_day} per day")
        print(f"{'='*70}\n")


# CLI command integration
def cmd_activity(args):
    """Handle activity command"""
    days = getattr(args, 'days', 1)
    print_activity_summary(days)
    return 0


if __name__ == '__main__':
    # Test activity logger
    logger = ActivityLogger()
    
    # Simulate a session
    print("Testing activity logger...")
    logger.start_session(
        reason='rule_match',
        rule_name='Test Rule',
        metrics={'cpu': 75, 'disk_read': 10, 'disk_write': 5}
    )
    
    import time
    time.sleep(2)
    
    logger.end_session()
    
    # Show summary
    print("\nActivity Summary:")
    print_activity_summary(days=1)
