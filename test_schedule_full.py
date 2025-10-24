"""
Test schedule rules with full daemon integration
"""

from pathlib import Path
import sys
import time

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from rules.engine import RulesEngine
from daemon.monitor import SystemMonitor

def main():
    print("=" * 60)
    print("Schedule Rules Integration Test")
    print("=" * 60)
    
    config_path = Path('test_config_schedule.yaml')
    
    if not config_path.exists():
        print(f"ERROR: Config file not found: {config_path}")
        return 1
    
    try:
        # Create rules engine
        engine = RulesEngine(config_path)
        print(f"Loaded {len(engine.rules)} rules from config")
        
        # Count schedule rules
        schedule_rules = [r for r in engine.rules if r.get('type') == 'schedule']
        print(f"Found {len(schedule_rules)} schedule rules")
        
        for rule in schedule_rules:
            enabled = rule.get('enabled', True)
            status = "ENABLED" if enabled else "DISABLED"
            days = ', '.join(rule.get('days', [])).upper()
            times = f"{rule['start_time']}-{rule['end_time']}"
            print(f"  - {rule['name']} ({status})")
            print(f"    Days: {days}")
            print(f"    Time: {times}")
        
        print()
        print("Testing rule evaluation...")
        
        # Create system monitor
        monitor = SystemMonitor()
        
        # Get current metrics
        metrics = monitor.get_current_state()
        
        # Evaluate all rules
        should_stay_awake = engine.evaluate(metrics)
        
        print()
        print("=" * 60)
        status = "STAY AWAKE" if should_stay_awake else "CAN SLEEP"
        print(f"Result: {status}")
        print("=" * 60)
        
        return 0
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
