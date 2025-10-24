"""
Rules Engine
Evaluates user-defined rules against system metrics
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

from daemon.monitor import SystemMetrics
from rules.schema import ConfigSchema, ConfigValidationError


@dataclass
class RuleMatch:
    """Result of rule evaluation"""
    rule_name: str
    matched: bool
    reason: str
    timestamp: datetime


class RulesEngine:
    """
    Rules evaluation engine
    Evaluates system metrics against user-defined rules
    """
    
    def __init__(self, config_path: Path):
        """
        Initialize rules engine
        
        Args:
            config_path: Path to config YAML file
        """
        self.logger = logging.getLogger(__name__)
        self.config_path = config_path
        
        # Load and validate config
        validator = ConfigSchema()
        self.config = validator.load_and_validate(config_path)
        
        # Extract settings
        self.senthium_config = self.config['senthium']
        self.rules = self.senthium_config['rules']
        
        # Duration tracking (for sustained conditions)
        self._condition_start_times: Dict[str, datetime] = {}
        
        self.logger.info(f"RulesEngine initialized with {len(self.rules)} rules")
        self.logger.info(f"Config version: {self.senthium_config['version']}")
    
    def evaluate(self, metrics: SystemMetrics) -> bool:
        """
        Evaluate all rules against current metrics
        
        Args:
            metrics: Current system metrics
            
        Returns:
            True if ANY rule matches (system should stay awake)
        """
        matches: List[RuleMatch] = []
        
        for rule in self.rules:
            # Skip disabled rules
            if not rule.get('enabled', True):
                continue
            
            match = self._evaluate_rule(rule, metrics)
            matches.append(match)
            
            if match.matched:
                self.logger.info(f"Rule matched: {match.rule_name} - {match.reason}")
        
        # Return True if ANY rule matched (OR logic)
        any_matched = any(m.matched for m in matches)
        
        if any_matched:
            matched_rules = [m.rule_name for m in matches if m.matched]
            self.logger.debug(f"Stay awake requested by: {', '.join(matched_rules)}")
        
        return any_matched
    
    def _evaluate_rule(self, rule: Dict, metrics: SystemMetrics) -> RuleMatch:
        """Evaluate a single rule"""
        rule_name = rule['name']
        rule_type = rule['type']
        
        try:
            if rule_type == 'process':
                return self._evaluate_process_rule(rule, metrics)
            elif rule_type == 'cpu':
                return self._evaluate_cpu_rule(rule, metrics)
            elif rule_type == 'disk':
                return self._evaluate_disk_rule(rule, metrics)
            elif rule_type == 'network':
                return self._evaluate_network_rule(rule, metrics)
            elif rule_type == 'combined':
                return self._evaluate_combined_rule(rule, metrics)
            elif rule_type == 'schedule':
                return self._evaluate_schedule_rule(rule, metrics)
            else:
                return RuleMatch(
                    rule_name=rule_name,
                    matched=False,
                    reason=f"Unknown rule type: {rule_type}",
                    timestamp=datetime.now()
                )
        except Exception as e:
            self.logger.error(f"Error evaluating rule '{rule_name}': {e}")
            return RuleMatch(
                rule_name=rule_name,
                matched=False,
                reason=f"Evaluation error: {e}",
                timestamp=datetime.now()
            )
    
    def _evaluate_process_rule(self, rule: Dict, metrics: SystemMetrics) -> RuleMatch:
        """Evaluate process-based rule"""
        rule_name = rule['name']
        target_processes = [p.lower() for p in rule.get('processes', [])]
        
        # Check if any target process is running
        running_processes = set(metrics.processes)
        matched_processes = []
        
        for proc in target_processes:
            # Match exact name or partial match (for .exe variants)
            if any(proc in running_proc or running_proc.startswith(proc) 
                   for running_proc in running_processes):
                matched_processes.append(proc)
        
        if matched_processes:
            return RuleMatch(
                rule_name=rule_name,
                matched=True,
                reason=f"Processes running: {', '.join(matched_processes)}",
                timestamp=datetime.now()
            )
        else:
            return RuleMatch(
                rule_name=rule_name,
                matched=False,
                reason="No target processes running",
                timestamp=datetime.now()
            )
    
    def _evaluate_cpu_rule(self, rule: Dict, metrics: SystemMetrics) -> RuleMatch:
        """Evaluate CPU threshold rule"""
        rule_name = rule['name']
        threshold = rule.get('threshold', 70)
        duration = rule.get('duration', 0)
        
        # Check if CPU exceeds threshold
        if metrics.cpu_percent >= threshold:
            # Check duration if specified
            if duration > 0:
                return self._check_duration(
                    rule_name,
                    True,
                    duration,
                    f"CPU at {metrics.cpu_percent:.1f}% (threshold: {threshold}%)"
                )
            else:
                return RuleMatch(
                    rule_name=rule_name,
                    matched=True,
                    reason=f"CPU at {metrics.cpu_percent:.1f}% (threshold: {threshold}%)",
                    timestamp=datetime.now()
                )
        else:
            # Reset duration tracking
            self._reset_duration(rule_name)
            return RuleMatch(
                rule_name=rule_name,
                matched=False,
                reason=f"CPU at {metrics.cpu_percent:.1f}% (below {threshold}%)",
                timestamp=datetime.now()
            )
    
    def _evaluate_disk_rule(self, rule: Dict, metrics: SystemMetrics) -> RuleMatch:
        """Evaluate disk I/O rule"""
        rule_name = rule['name']
        read_threshold = rule.get('read_mbps', 0)
        write_threshold = rule.get('write_mbps', 0)
        duration = rule.get('duration', 0)
        
        # Check if disk I/O exceeds thresholds
        read_exceeded = metrics.disk_read_mbps >= read_threshold if read_threshold > 0 else True
        write_exceeded = metrics.disk_write_mbps >= write_threshold if write_threshold > 0 else True
        
        if read_exceeded and write_exceeded:
            reason = f"Disk I/O: {metrics.disk_read_mbps:.1f}R / {metrics.disk_write_mbps:.1f}W MB/s"
            
            if duration > 0:
                return self._check_duration(rule_name, True, duration, reason)
            else:
                return RuleMatch(
                    rule_name=rule_name,
                    matched=True,
                    reason=reason,
                    timestamp=datetime.now()
                )
        else:
            self._reset_duration(rule_name)
            return RuleMatch(
                rule_name=rule_name,
                matched=False,
                reason="Disk I/O below threshold",
                timestamp=datetime.now()
            )
    
    def _evaluate_network_rule(self, rule: Dict, metrics: SystemMetrics) -> RuleMatch:
        """Evaluate network I/O rule"""
        rule_name = rule['name']
        download_threshold = rule.get('download_mbps', 0)
        upload_threshold = rule.get('upload_mbps', 0)
        duration = rule.get('duration', 0)
        
        # Check if network I/O exceeds thresholds
        download_exceeded = metrics.net_recv_mbps >= download_threshold if download_threshold > 0 else True
        upload_exceeded = metrics.net_sent_mbps >= upload_threshold if upload_threshold > 0 else True
        
        if download_exceeded and upload_exceeded:
            reason = f"Network: {metrics.net_recv_mbps:.1f}↓ / {metrics.net_sent_mbps:.1f}↑ MB/s"
            
            if duration > 0:
                return self._check_duration(rule_name, True, duration, reason)
            else:
                return RuleMatch(
                    rule_name=rule_name,
                    matched=True,
                    reason=reason,
                    timestamp=datetime.now()
                )
        else:
            self._reset_duration(rule_name)
            return RuleMatch(
                rule_name=rule_name,
                matched=False,
                reason="Network I/O below threshold",
                timestamp=datetime.now()
            )
    
    def _evaluate_combined_rule(self, rule: Dict, metrics: SystemMetrics) -> RuleMatch:
        """Evaluate combined rule (AND logic for sub-conditions)"""
        rule_name = rule['name']
        conditions = rule.get('conditions', [])
        
        if not conditions:
            return RuleMatch(
                rule_name=rule_name,
                matched=False,
                reason="No conditions defined",
                timestamp=datetime.now()
            )
        
        # Evaluate all conditions (must ALL match - AND logic)
        condition_results = []
        
        for condition in conditions:
            # Create temporary rule from condition
            temp_rule = {
                'name': f"{rule_name}_condition",
                'type': condition['type'],
                **condition
            }
            
            result = self._evaluate_rule(temp_rule, metrics)
            condition_results.append(result)
        
        # Check if ALL conditions matched
        all_matched = all(r.matched for r in condition_results)
        
        if all_matched:
            reasons = [r.reason for r in condition_results if r.matched]
            return RuleMatch(
                rule_name=rule_name,
                matched=True,
                reason=f"All conditions met: {'; '.join(reasons)}",
                timestamp=datetime.now()
            )
        else:
            return RuleMatch(
                rule_name=rule_name,
                matched=False,
                reason="Not all conditions met",
                timestamp=datetime.now()
            )
    
    def _evaluate_schedule_rule(self, rule: Dict, metrics: SystemMetrics) -> RuleMatch:
        """Evaluate schedule-based rule (time-based stay-awake)"""
        rule_name = rule['name']
        days = rule.get('days', [])
        start_time_str = rule.get('start_time', '00:00')
        end_time_str = rule.get('end_time', '23:59')
        
        now = datetime.now()
        
        # Get current day of week (0=Monday, 6=Sunday)
        current_weekday = now.weekday()
        day_names = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
        current_day = day_names[current_weekday]
        
        # Check if today is in the schedule
        if 'all' not in days and current_day not in days:
            return RuleMatch(
                rule_name=rule_name,
                matched=False,
                reason=f"Not active on {current_day.upper()} (active: {', '.join(d.upper() for d in days)})",
                timestamp=now
            )
        
        # Parse time strings (HH:MM)
        try:
            start_hour, start_min = map(int, start_time_str.split(':'))
            end_hour, end_min = map(int, end_time_str.split(':'))
            
            # Create time objects for today
            start_time = now.replace(hour=start_hour, minute=start_min, second=0, microsecond=0)
            end_time = now.replace(hour=end_hour, minute=end_min, second=0, microsecond=0)
            
            # Handle overnight schedules (e.g., 22:00 - 06:00)
            if end_time <= start_time:
                # If current time is after start, extend end time to next day
                if now >= start_time:
                    end_time += timedelta(days=1)
                # If current time is before end, move start time back a day
                else:
                    start_time -= timedelta(days=1)
            
            # Check if current time is within schedule
            if start_time <= now <= end_time:
                time_str = now.strftime('%H:%M')
                return RuleMatch(
                    rule_name=rule_name,
                    matched=True,
                    reason=f"Within schedule: {start_time_str}-{end_time_str} (now: {time_str})",
                    timestamp=now
                )
            else:
                return RuleMatch(
                    rule_name=rule_name,
                    matched=False,
                    reason=f"Outside schedule: {start_time_str}-{end_time_str}",
                    timestamp=now
                )
                
        except Exception as e:
            return RuleMatch(
                rule_name=rule_name,
                matched=False,
                reason=f"Invalid time format: {e}",
                timestamp=now
            )
    
    def _check_duration(self, rule_name: str, condition_met: bool, 
                       required_duration: int, reason: str) -> RuleMatch:
        """Check if condition has been true for required duration"""
        now = datetime.now()
        
        if condition_met:
            # Start tracking if not already
            if rule_name not in self._condition_start_times:
                self._condition_start_times[rule_name] = now
                elapsed = 0
            else:
                start_time = self._condition_start_times[rule_name]
                elapsed = (now - start_time).total_seconds()
            
            # Check if duration requirement met
            if elapsed >= required_duration:
                return RuleMatch(
                    rule_name=rule_name,
                    matched=True,
                    reason=f"{reason} (sustained for {elapsed:.0f}s)",
                    timestamp=now
                )
            else:
                remaining = required_duration - elapsed
                return RuleMatch(
                    rule_name=rule_name,
                    matched=False,
                    reason=f"{reason} (need {remaining:.0f}s more)",
                    timestamp=now
                )
        else:
            self._reset_duration(rule_name)
            return RuleMatch(
                rule_name=rule_name,
                matched=False,
                reason=reason,
                timestamp=now
            )
    
    def _reset_duration(self, rule_name: str):
        """Reset duration tracking for a rule"""
        if rule_name in self._condition_start_times:
            del self._condition_start_times[rule_name]
    
    def get_config_value(self, key: str, default=None):
        """Get a config value by key"""
        return self.senthium_config.get(key, default)


# Example usage / testing
if __name__ == '__main__':
    from utils.logger import setup_logger
    from daemon.monitor import SystemMonitor
    import time
    
    # Setup logging
    logger = setup_logger('senthium.rules', level='DEBUG')
    
    # Load example config
    config_path = Path(__file__).parent.parent.parent / 'config' / 'config.example.yaml'
    
    if not config_path.exists():
        print(f"❌ Config file not found: {config_path}")
        print("   Please create config.example.yaml first!")
        exit(1)
    
    try:
        # Create rules engine
        engine = RulesEngine(config_path)
        
        # Create system monitor
        monitor = SystemMonitor()
        
        print("🧠 Senthium Rules Engine - Live Evaluation Test")
        print("=" * 60)
        print(f"Loaded {len(engine.rules)} rules from config")
        print("Evaluating every 3 seconds. Press Ctrl+C to stop.\n")
        
        iteration = 1
        while True:
            # Get current metrics
            metrics = monitor.get_current_state()
            
            # Evaluate rules
            should_stay_awake = engine.evaluate(metrics)
            
            # Display result
            status = "🔓 STAY AWAKE" if should_stay_awake else "😴 CAN SLEEP"
            print(f"\n[{iteration}] {metrics.timestamp.strftime('%H:%M:%S')} - {status}")
            print(f"  CPU: {metrics.cpu_percent:.1f}%")
            print(f"  Disk: {metrics.disk_read_mbps:.2f}R / {metrics.disk_write_mbps:.2f}W MB/s")
            print(f"  Network: {metrics.net_recv_mbps:.2f}↓ / {metrics.net_sent_mbps:.2f}↑ MB/s")
            print(f"  Processes: {len(metrics.processes)}")
            
            iteration += 1
            time.sleep(3)
            
    except ConfigValidationError as e:
        print(f"❌ Config validation failed: {e}")
    except KeyboardInterrupt:
        print("\n\n✅ Rules engine test complete!")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
