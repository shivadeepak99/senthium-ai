"""
Test IPC functionality - CLI wrapper communicating with daemon.

This test:
1. Starts daemon in background
2. Uses CLI wrapper to run a command with stay-awake lock
3. Verifies lock is acquired/released properly
"""

import sys
import time
import subprocess
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

def test_ipc_communication():
    """Test basic IPC communication"""
    logger.info("=" * 70)
    logger.info("🧪 Testing IPC Communication")
    logger.info("=" * 70)
    
    # Test 1: Import IPC modules
    logger.info("Test 1: Importing IPC modules...")
    try:
        from src.ipc import IPCClient, IPCMessage, IPCResponse
        logger.info("✅ IPC modules imported successfully")
    except ImportError as e:
        logger.error(f"❌ Failed to import IPC modules: {e}")
        return False
    
    # Test 2: Start daemon with test config (background)
    logger.info("\nTest 2: Starting daemon with test config...")
    daemon_process = subprocess.Popen(
        [
            sys.executable,
            "src/daemon/core.py",
            "--config", "config/test.yaml",
            "--log-level", "INFO"
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Give daemon time to start and create IPC socket
    logger.info("⏳ Waiting for daemon to initialize (3 seconds)...")
    time.sleep(3)
    
    # Check if daemon is still running
    if daemon_process.poll() is not None:
        logger.error("❌ Daemon terminated early!")
        stdout, stderr = daemon_process.communicate()
        logger.error(f"STDOUT:\n{stdout}")
        logger.error(f"STDERR:\n{stderr}")
        return False
    
    logger.info("✅ Daemon started successfully")
    
    try:
        # Test 3: Send STATUS command
        logger.info("\nTest 3: Querying daemon status via IPC...")
        try:
            client = IPCClient(timeout=5.0)
            response = client.send_command("STATUS")
            
            if response.success:
                logger.info("✅ STATUS command successful")
                logger.info(f"   State: {response.data.get('state')}")
                logger.info(f"   Polls: {response.data.get('poll_count')}")
            else:
                logger.error(f"❌ STATUS command failed: {response.message}")
                return False
        except Exception as e:
            logger.error(f"❌ IPC communication failed: {e}")
            return False
        
        # Test 4: Acquire wrapper lock
        logger.info("\nTest 4: Acquiring wrapper lock...")
        try:
            response = client.send_command("ACQUIRE_LOCK")
            
            if response.success:
                logger.info("✅ Wrapper lock acquired")
            else:
                logger.error(f"❌ Failed to acquire lock: {response.message}")
                return False
        except Exception as e:
            logger.error(f"❌ Lock acquisition failed: {e}")
            return False
        
        # Wait a bit with lock active
        logger.info("⏳ Holding lock for 3 seconds...")
        time.sleep(3)
        
        # Test 5: Release wrapper lock
        logger.info("\nTest 5: Releasing wrapper lock...")
        try:
            response = client.send_command("RELEASE_LOCK")
            
            if response.success:
                logger.info("✅ Wrapper lock released")
            else:
                logger.error(f"❌ Failed to release lock: {response.message}")
                return False
        except Exception as e:
            logger.error(f"❌ Lock release failed: {e}")
            return False
        
        # Test 6: INFO command
        logger.info("\nTest 6: Querying daemon info...")
        try:
            response = client.send_command("INFO")
            
            if response.success:
                logger.info("✅ INFO command successful")
                logger.info(f"   Config: {response.data.get('config_path')}")
                logger.info(f"   Rules: {len(response.data.get('rules', []))}")
            else:
                logger.error(f"❌ INFO command failed: {response.message}")
                return False
        except Exception as e:
            logger.error(f"❌ INFO query failed: {e}")
            return False
        
        logger.info("\n" + "=" * 70)
        logger.info("✅ All IPC tests passed!")
        logger.info("=" * 70)
        return True
        
    finally:
        # Cleanup: Stop daemon
        logger.info("\n🧹 Cleaning up - stopping daemon...")
        daemon_process.terminate()
        try:
            daemon_process.wait(timeout=5)
            logger.info("✅ Daemon stopped cleanly")
        except subprocess.TimeoutExpired:
            daemon_process.kill()
            logger.warning("⚠️  Daemon killed (didn't stop gracefully)")


if __name__ == "__main__":
    try:
        success = test_ipc_communication()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n⚠️  Test interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.exception(f"💥 Test failed with exception: {e}")
        sys.exit(1)
