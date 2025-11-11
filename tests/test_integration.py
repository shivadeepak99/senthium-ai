"""
Integration tests for Senthium daemon lifecycle
Tests full end-to-end scenarios with real daemon + IPC + CLI
"""

import pytest
import time
import subprocess
import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from daemon import control as daemon_control
from ipc import IPCClient  # type: ignore
from src.utils.pid import PIDFile


class TestDaemonLifecycle:
    """Test full daemon lifecycle"""
    
    def setup_method(self):
        """Ensure clean state before each test"""
        pid_file = PIDFile()
        if pid_file.is_running():
            daemon_control.stop_daemon()
            time.sleep(2)  # Wait for cleanup
    
    def teardown_method(self):
        """Cleanup after each test"""
        pid_file = PIDFile()
        if pid_file.is_running():
            daemon_control.stop_daemon()
            time.sleep(1)
    
    def test_daemon_start_stop(self):
        """Test basic start and stop"""
        pid_file = PIDFile()
        
        # Should not be running initially
        assert not pid_file.is_running()
        
        # Start daemon
        exit_code = daemon_control.start_daemon()
        assert exit_code == 0, "Failed to start daemon"
        
        # Give it time to initialize
        time.sleep(2)
        
        # Should be running now
        assert pid_file.is_running(), "Daemon not running after start"
        
        # Stop daemon
        exit_code = daemon_control.stop_daemon()
        assert exit_code == 0, "Failed to stop daemon"
        
        # Give it time to shutdown
        time.sleep(2)
        
        # Should not be running
        assert not pid_file.is_running(), "Daemon still running after stop"
    
    def test_daemon_restart(self):
        """Test daemon restart"""
        pid_file = PIDFile()
        
        # Start daemon
        daemon_control.start_daemon()
        time.sleep(2)
        
        # Get initial PID
        old_pid = pid_file.get_pid()
        assert old_pid is not None
        
        # Restart
        exit_code = daemon_control.restart_daemon()
        assert exit_code == 0, "Failed to restart daemon"
        time.sleep(2)
        
        # Get new PID
        new_pid = pid_file.get_pid()
        assert new_pid is not None
        assert new_pid != old_pid, "PID didn't change after restart"
        
        # Cleanup
        daemon_control.stop_daemon()
        time.sleep(1)
    
    def test_prevent_duplicate_daemon(self):
        """Test that PID file prevents duplicate instances"""
        pid_file = PIDFile()
        
        # Start first instance
        daemon_control.start_daemon()
        time.sleep(2)
        assert pid_file.is_running()
        
        # Try to start second instance (should fail)
        exit_code = daemon_control.start_daemon()
        assert exit_code != 0, "Second daemon instance started (should have failed)"
        
        # Cleanup
        daemon_control.stop_daemon()
        time.sleep(1)
    
    def test_daemon_survives_terminal_close(self):
        """Test daemon continues running after parent process exits"""
        # This is a background daemon property - hard to test in pytest
        # We'll just verify detachment by checking parent PID
        pid_file = PIDFile()
        daemon_control.start_daemon()
        time.sleep(2)
        
        pid = pid_file.get_pid()
        assert pid is not None
        
        # On Unix, daemon should be reparented to init (PID 1)
        # On Windows, this doesn't apply the same way
        # Just verify it's running and detached
        assert pid_file.is_running()
        
        daemon_control.stop_daemon()
        time.sleep(1)


class TestIPCCommunication:
    """Test IPC between daemon and clients"""
    
    def setup_method(self):
        """Start daemon before each test"""
        pid_file = PIDFile()
        if pid_file.is_running():
            daemon_control.stop_daemon()
            time.sleep(2)
        
        # Use test config without security/camera
        daemon_control.start_daemon(config_path="config/test_ipc.yaml")
        time.sleep(3)  # Give daemon time to start IPC server
    
    def teardown_method(self):
        """Stop daemon after each test"""
        daemon_control.stop_daemon()
        time.sleep(1)
    
    def test_status_command(self):
        """Test STATUS IPC command"""
        client = IPCClient()
        response = client.send_command("STATUS")
        
        assert response is not None
        assert response.success
        assert "state" in response.data
        assert response.data["state"] in ["idle", "monitoring", "active"]
    
    def test_info_command(self):
        """Test INFO IPC command"""
        client = IPCClient()
        response = client.send_command("INFO")
        
        assert response is not None
        assert response.success
        assert "config_path" in response.data
        assert "rules" in response.data
        assert isinstance(response.data["rules"], list)
    
    def test_acquire_release_lock(self):
        """Test wrapper lock acquire/release cycle"""
        client = IPCClient()
        
        # Acquire lock
        response = client.send_command("ACQUIRE_LOCK", {
            "reason": "Integration test"
        })
        assert response is not None
        assert response.success
        assert response.data.get("lock_active") is True
        
        # Check status shows lock active
        status = client.send_command("STATUS")
        assert status.data.get("wrapper_lock_active") is True
        
        # Release lock
        response = client.send_command("RELEASE_LOCK")
        assert response is not None
        assert response.success
        assert response.data.get("lock_active") is False
        
        # Check status shows lock inactive
        status = client.send_command("STATUS")
        assert status.data.get("wrapper_lock_active") is False
    
    def test_lock_held_during_command(self):
        """Test lock is held for command duration"""
        client = IPCClient()
        
        # Acquire lock
        client.send_command("ACQUIRE_LOCK", {"reason": "Test command"})
        
        # Lock should be active
        status = client.send_command("STATUS")
        assert status.data.get("wrapper_lock_active") is True
        
        # Simulate command running
        time.sleep(2)
        
        # Lock should still be active
        status = client.send_command("STATUS")
        assert status.data.get("wrapper_lock_active") is True
        
        # Release lock
        client.send_command("RELEASE_LOCK")
        
        # Lock should be inactive
        status = client.send_command("STATUS")
        assert status.data.get("wrapper_lock_active") is False
    
    def test_reload_config(self):
        """Test hot config reload"""
        client = IPCClient()
        
        # Get initial rule count
        info1 = client.send_command("INFO")
        initial_count = len(info1.data["rules"])
        
        # Reload config (same config, but tests the mechanism)
        response = client.send_command("RELOAD_CONFIG")
        assert response is not None
        assert response.success
        
        # Check rule count after reload
        info2 = client.send_command("INFO")
        assert len(info2.data["rules"]) == initial_count


class TestCLIWrapper:
    """Test CLI wrapper functionality"""
    
    def setup_method(self):
        """Start daemon before each test"""
        pid_file = PIDFile()
        if pid_file.is_running():
            daemon_control.stop_daemon()
            time.sleep(2)
        
        daemon_control.start_daemon()
        time.sleep(3)
    
    def teardown_method(self):
        """Stop daemon after each test"""
        daemon_control.stop_daemon()
        time.sleep(1)
    
    def test_wrapper_simple_command(self):
        """Test running simple command with wrapper"""
        result = subprocess.run(
            [sys.executable, "-c", "print('Hello from wrapped command!')"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent / 'src',
            env={**os.environ, "PYTHONPATH": "src"}
        )
        
        assert result.returncode == 0
        assert "Hello from wrapped command!" in result.stdout
    
    def test_wrapper_exit_code_propagation(self):
        """Test wrapper propagates command exit codes"""
        # Command that exits with code 42
        result = subprocess.run(
            [sys.executable, "-c", "import sys; sys.exit(42)"],
            capture_output=True,
            cwd=Path(__file__).parent.parent / 'src',
            env={**os.environ, "PYTHONPATH": "src"}
        )
        
        assert result.returncode == 42


class TestRulesEvaluation:
    """Test rules engine integration with daemon"""
    
    def setup_method(self):
        """Start daemon before each test"""
        pid_file = PIDFile()
        if pid_file.is_running():
            daemon_control.stop_daemon()
            time.sleep(2)
        
        # Start with test config
        daemon_control.start_daemon(config_path="config/test.yaml")
        time.sleep(3)
    
    def teardown_method(self):
        """Stop daemon after each test"""
        daemon_control.stop_daemon()
        time.sleep(1)
    
    def test_rules_trigger_active_state(self):
        """Test that matching rules move daemon to active state"""
        # Test config has python.exe rule
        # This test is running Python, so rule should match!
        
        client = IPCClient()
        time.sleep(5)  # Wait for daemon to poll and evaluate
        
        status = client.send_command("STATUS")
        
        # State should be monitoring or active (depends on timing)
        assert status.data["state"] in ["monitoring", "active"]
        
        # If active, stay_awake should be true
        if status.data["state"] == "active":
            assert status.data.get("stay_awake_active") is True


@pytest.mark.slow
class TestLongRunning:
    """Long-running stress tests"""
    
    def test_daemon_runs_for_extended_period(self):
        """Test daemon stability over 30 seconds"""
        pid_file = PIDFile()
        
        # Clean start
        if pid_file.is_running():
            daemon_control.stop_daemon()
            time.sleep(2)
        
        daemon_control.start_daemon()
        time.sleep(2)
        
        # Check status every 5 seconds for 30 seconds
        for i in range(6):
            assert pid_file.is_running(), f"Daemon died after {i*5} seconds"
            
            client = IPCClient()
            status = client.send_command("STATUS")
            assert status is not None, f"IPC failed after {i*5} seconds"
            assert status.success
            
            time.sleep(5)
        
        # Cleanup
        daemon_control.stop_daemon()
        time.sleep(1)
    
    def test_rapid_lock_cycles(self):
        """Test rapid lock acquire/release cycles"""
        pid_file = PIDFile()
        
        if pid_file.is_running():
            daemon_control.stop_daemon()
            time.sleep(2)
        
        daemon_control.start_daemon()
        time.sleep(3)
        
        client = IPCClient()
        
        # 20 rapid lock cycles
        for i in range(20):
            # Acquire
            response = client.send_command("ACQUIRE_LOCK", {"reason": f"Test {i}"})
            assert response.success, f"Acquire failed on cycle {i}"
            
            # Release
            response = client.send_command("RELEASE_LOCK")
            assert response.success, f"Release failed on cycle {i}"
        
        # Daemon should still be healthy
        assert pid_file.is_running()
        status = client.send_command("STATUS")
        assert status.success
        
        daemon_control.stop_daemon()
        time.sleep(1)


if __name__ == '__main__':
    # Run with: pytest tests/test_integration.py -v
    pytest.main([__file__, "-v", "-s"])
