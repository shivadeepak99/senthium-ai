"""
Test CLI wrapper - Run a command with explicit stay-awake lock.

This test demonstrates the explicit mode:
1. Daemon running in background
2. CLI wrapper executes a command with stay-awake lock
3. Lock is automatically released after command completes
"""

import sys
import time
import subprocess
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

def test_cli_wrapper():
    """Test CLI wrapper with real command"""
    logger.info("=" * 70)
    logger.info("🧪 Testing CLI Wrapper (Explicit Mode)")
    logger.info("=" * 70)
    
    # Start daemon in background
    logger.info("\n▶️  Starting daemon in background...")
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
    
    # Wait for daemon to start
    logger.info("⏳ Waiting for daemon to initialize (3 seconds)...")
    time.sleep(3)
    
    if daemon_process.poll() is not None:
        logger.error("❌ Daemon failed to start!")
        return False
    
    logger.info("✅ Daemon running\n")
    
    try:
        # Test CLI wrapper with a simple Python command
        logger.info("▶️  Running command via CLI wrapper:")
        logger.info('   senthium --stay-awake "python -c \'import time; print(\\"Hello\\"); time.sleep(2); print(\\"Goodbye\\")\'"\n')
        
        # Set PYTHONPATH for wrapper
        import os
        env = os.environ.copy()
        env['PYTHONPATH'] = 'src'
        
        wrapper_process = subprocess.run(
            [
                sys.executable,
                "src/cli/wrapper.py",
                "--stay-awake",
                "python -c \"import time; print('[TEST] Command executing with stay-awake lock!'); time.sleep(2); print('[TEST] Command completed!')\"",
                "--log-level", "INFO"
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=15,
            env=env
        )
        
        logger.info("CLI Wrapper Output:")
        logger.info("-" * 70)
        logger.info(wrapper_process.stdout)
        logger.info("-" * 70)
        
        if wrapper_process.returncode == 0:
            logger.info("\n✅ CLI wrapper test passed!")
            return True
        else:
            logger.error(f"\n❌ CLI wrapper failed with exit code: {wrapper_process.returncode}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("❌ CLI wrapper timed out!")
        return False
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False
    finally:
        # Cleanup daemon
        logger.info("\n🧹 Stopping daemon...")
        daemon_process.terminate()
        try:
            daemon_process.wait(timeout=5)
            logger.info("✅ Daemon stopped\n")
        except subprocess.TimeoutExpired:
            daemon_process.kill()
            logger.warning("⚠️  Daemon killed\n")


if __name__ == "__main__":
    try:
        success = test_cli_wrapper()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n⚠️  Test interrupted")
        sys.exit(130)
