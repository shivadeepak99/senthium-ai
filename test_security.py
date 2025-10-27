"""
Quick Security System Test
Tests AI face recognition and alert system
"""
import sys
from pathlib import Path
import yaml
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add src to path and set working directory
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir / 'src'))
import os
os.chdir(script_dir)

print("\n" + "=" * 70)
print("SENTHIUM AI SECURITY SYSTEM TEST")
print("=" * 70)

# Load config
print("\n[STEP 1] Loading configuration...")
with open('config/config.yaml', 'r') as f:
    full_config = yaml.safe_load(f)

security_config = full_config['senthium']['security']
print(f"✓ Security enabled: {security_config['enabled']}")
print(f"✓ Camera index: {security_config['camera_index']}")
print(f"✓ Detection model: {security_config['detection_model']}")
print(f"✓ Recognition tolerance: {security_config['recognition_tolerance']}")
print(f"✓ Alert cooldown: {security_config['alert_cooldown_seconds']}s")

# Initialize SecurityManager
print("\n[STEP 2] Initializing AI Security Manager...")
from vision.security_manager import SecurityManager

try:
    security = SecurityManager(config=security_config)
    print("✓ SecurityManager initialized successfully!")
    
    # Enable security monitoring
    security.enable()
    print("✓ Security monitoring enabled!")
except Exception as e:
    print(f"✗ Failed to initialize SecurityManager: {e}")
    sys.exit(1)

# Check enrolled faces
print("\n[STEP 3] Checking authorized users database...")
authorized_users = security.recognizer.get_authorized_users()
if authorized_users:
    print(f"✓ {len(authorized_users)} authorized user(s) enrolled:")
    for user in authorized_users:
        print(f"   - {user}")
else:
    print("⚠ WARNING: No authorized users enrolled!")
    print("   Everyone will be detected as unauthorized")
    print("   Enroll yourself with: python -m src.cli.main enroll --name YourName")

# Perform security check
print("\n[STEP 4] Performing security check...")
print("⏳ Looking at camera... (make sure you're in frame!)")

try:
    result = security.perform_security_check()
    
    if result and result.get('status') == 'success':
        print("\n" + "=" * 70)
        print("SECURITY CHECK RESULTS")
        print("=" * 70)
        print(f"Status: ✓ SUCCESS")
        print(f"Faces detected: {result.get('total_faces', 0)}")
        print(f"Known faces: {len(result.get('recognized_faces', []))}")
        print(f"Unknown faces: {len(result.get('unknown_faces', []))}")
        print(f"Alert sent: {'YES' if result.get('alert_sent') else 'NO'}")
        
        if result.get('snapshot_path'):
            print(f"\n📸 Snapshot saved to: {result['snapshot_path']}")
        
        if result.get('recognized_faces'):
            print(f"\n✅ AUTHORIZED USERS DETECTED:")
            for face in result['recognized_faces']:
                print(f"   👤 {face['name']} (confidence: {face['confidence']:.1%})")
        
        if result.get('unknown_faces'):
            print(f"\n🚨 SECURITY ALERT!")
            print(f"   {len(result['unknown_faces'])} unauthorized person(s) detected!")
            print(f"   Alert logged to: logs/security/alerts.jsonl")
            
            # Check if alerts were sent
            if result.get('alert_sent'):
                print(f"   Alerts sent via configured channels")
        
        print("=" * 70)
        
    elif result and result.get('status') == 'no_faces':
        print("\n👻 No faces detected in camera frame")
        print(f"   Snapshot: {result.get('snapshot_path')}")
        print("   Make sure you're in front of the camera!")
        
    elif result and result.get('status') == 'error':
        print(f"\n✗ Security check failed: {result.get('error', 'Unknown error')}")
    else:
        print("\n✗ Security check returned unexpected result")
        print(f"   Result: {result}")
        
except Exception as e:
    print(f"\n✗ ERROR during security check: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n✓ Test complete!")
print("\nNext steps:")
if not authorized_users:
    print("  1. Enroll yourself: python -m src.cli.main enroll --name YourName")
print("  2. Configure alert channels in config/config.yaml (Discord/Email/Telegram)")
print("  3. Start daemon: python -m src.daemon.core")
print("\n")
