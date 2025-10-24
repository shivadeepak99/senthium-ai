"""
Quick test for schedule rule evaluation
"""

from datetime import datetime
from pathlib import Path
from src.rules.engine import RulesEngine
from src.daemon.monitor import SystemMetrics

# Create test metrics (dummy)
metrics = SystemMetrics(
    timestamp=datetime.now(),
    cpu_percent=10.0,
    disk_read_mbps=0.5,
    disk_write_mbps=0.3,
    net_recv_mbps=0.1,
    net_sent_mbps=0.05,
    processes=['python.exe'],
    idle_time_seconds=100
)

# Test 1: Current time schedule
now = datetime.now()
current_day = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'][now.weekday()]
current_time = now.strftime('%H:%M')

print("🧪 Schedule Rule Test")
print("=" * 60)
print(f"Current time: {current_time}")
print(f"Current day: {current_day.upper()}")
print()

# Test different schedule configurations
test_rules = [
    {
        'name': 'Current Time Test',
        'type': 'schedule',
        'days': [current_day],
        'start_time': '00:00',
        'end_time': '23:59'
    },
    {
        'name': 'Weekday Mornings',
        'type': 'schedule',
        'days': ['mon', 'tue', 'wed', 'thu', 'fri'],
        'start_time': '09:00',
        'end_time': '12:00'
    },
    {
        'name': 'Weekend Evenings',
        'type': 'schedule',
        'days': ['sat', 'sun'],
        'start_time': '18:00',
        'end_time': '23:00'
    },
    {
        'name': 'All Day Every Day',
        'type': 'schedule',
        'days': ['all'],
        'start_time': '00:00',
        'end_time': '23:59'
    },
    {
        'name': 'Overnight Schedule',
        'type': 'schedule',
        'days': ['all'],
        'start_time': '22:00',
        'end_time': '06:00'
    }
]

# Create a minimal rules engine instance
from src.rules.engine import RulesEngine

engine = RulesEngine.__new__(RulesEngine)  # Create without __init__
engine.logger = None  # Bypass logger

for rule in test_rules:
    result = engine._evaluate_schedule_rule(rule, metrics)
    
    status = "✅ MATCH" if result.matched else "❌ NO MATCH"
    print(f"{status} | {rule['name']}")
    print(f"         Days: {', '.join(rule['days']).upper()}")
    print(f"         Time: {rule['start_time']} - {rule['end_time']}")
    print(f"         Reason: {result.reason}")
    print()

print("✅ Schedule rule test complete!")
