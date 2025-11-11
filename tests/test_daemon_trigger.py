"""Quick daemon test script with explicit stdout logging"""
import sys
import os

# Add src to path
sys.path.insert(0, 'src')

# Force stdout for logs
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout,
    force=True
)

print("🔥 Starting Senthium Daemon Test (WILL TRIGGER RULE!)...")
print("=" * 70)
print("Config: config/test.yaml (matches python.exe)")
print("This daemon itself is python.exe, so rule will match immediately!")
print("=" * 70)

from src.daemon.core import SenthiumDaemon

try:
    daemon = SenthiumDaemon('config/test.yaml')
    print("\n✅ Daemon created successfully!")
    print(f"   Poll interval: {daemon.poll_interval}s")
    print(f"   Rules loaded: {len(daemon.config.get('rules', []))}")
    print(f"   Max awake: {daemon.config.get('max_awake_duration')}s")
    
    print("\n🚀 Starting daemon loop...")
    print("   🔥 RULE SHOULD MATCH IN 2 SECONDS!")
    print("   💪 Your PC will REFUSE TO SLEEP!")
    print("   Press Ctrl+C to stop\n")
    
    daemon.run()
    
except KeyboardInterrupt:
    print("\n\n✅ Stopped by user - graceful shutdown!")
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
