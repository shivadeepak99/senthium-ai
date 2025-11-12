"""Quick IPC test - verify non-blocking works"""
import time
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.daemon import control as daemon_control
from src.utils.pid import PIDFile
from src.ipc.channel import IPCClient

def test_ipc_basic():
    """Test basic IPC communication"""
    print("🔥 Quick IPC Test")
    print("=" * 50)
    
    # Stop any running daemon
    pid_file = PIDFile()
    if pid_file.is_running():
        print("[*] Stopping existing daemon...")
        daemon_control.stop_daemon(force=True)
        time.sleep(2)
    
    # Start daemon with test config
    print("[*] Starting daemon...")
    daemon_control.start_daemon(config_path="config/test_ipc.yaml")
    time.sleep(3)  # Wait for IPC server
    
    try:
        # Test STATUS command
        print("[*] Sending STATUS command...")
        client = IPCClient()
        response = client.send_command("STATUS")
        
        if response and response.success:
            print(f"[OK] STATUS: {response.data}")
        else:
            print(f"[FAIL] STATUS failed: {response}")
            return False
        
        # Test INFO command
        print("[*] Sending INFO command...")
        response = client.send_command("INFO")
        
        if response and response.success:
            print(f"[OK] INFO: {response.data}")
        else:
            print(f"[FAIL] INFO failed: {response}")
            return False
        
        print("\n=== All tests PASSED! ===")
        return True
        
    finally:
        # Cleanup
        print("\n[*] Stopping daemon...")
        daemon_control.stop_daemon(force=True)
        time.sleep(1)
        print("✅ Cleanup complete")

if __name__ == "__main__":
    success = test_ipc_basic()
    sys.exit(0 if success else 1)
