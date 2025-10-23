"""
Unit tests for System Monitor module
"""

import pytest
import time
from daemon.monitor import SystemMonitor, SystemMetrics
from unittest.mock import Mock, patch
import psutil


class TestSystemMonitor:
    """Test suite for SystemMonitor class"""
    
    def test_monitor_initialization(self):
        """Test that monitor initializes correctly"""
        monitor = SystemMonitor(poll_interval=5.0)
        assert monitor.poll_interval == 5.0
        assert monitor._last_disk_io is None
        assert monitor._last_net_io is None
        assert monitor._last_poll_time is None
    
    def test_get_current_state_returns_metrics(self):
        """Test that get_current_state returns SystemMetrics object"""
        monitor = SystemMonitor()
        metrics = monitor.get_current_state()
        
        assert isinstance(metrics, SystemMetrics)
        assert metrics.timestamp is not None
        assert isinstance(metrics.cpu_percent, float)
        assert isinstance(metrics.disk_read_mbps, float)
        assert isinstance(metrics.disk_write_mbps, float)
        assert isinstance(metrics.net_sent_mbps, float)
        assert isinstance(metrics.net_recv_mbps, float)
        assert isinstance(metrics.processes, list)
        assert isinstance(metrics.idle_time_seconds, float)
    
    def test_cpu_percent_in_valid_range(self):
        """Test that CPU percentage is between 0 and 100"""
        monitor = SystemMonitor()
        metrics = monitor.get_current_state()
        assert 0.0 <= metrics.cpu_percent <= 100.0
    
    def test_disk_rates_non_negative(self):
        """Test that disk I/O rates are non-negative"""
        monitor = SystemMonitor()
        
        # First call initializes baseline
        metrics1 = monitor.get_current_state()
        time.sleep(0.5)
        
        # Second call should have rates
        metrics2 = monitor.get_current_state()
        
        assert metrics2.disk_read_mbps >= 0.0
        assert metrics2.disk_write_mbps >= 0.0
    
    def test_network_rates_non_negative(self):
        """Test that network I/O rates are non-negative"""
        monitor = SystemMonitor()
        
        # First call initializes baseline
        metrics1 = monitor.get_current_state()
        time.sleep(0.5)
        
        # Second call should have rates
        metrics2 = monitor.get_current_state()
        
        assert metrics2.net_sent_mbps >= 0.0
        assert metrics2.net_recv_mbps >= 0.0
    
    def test_process_list_not_empty(self):
        """Test that process list contains processes"""
        monitor = SystemMonitor()
        metrics = monitor.get_current_state()
        
        # There should always be at least one process running (python itself)
        assert len(metrics.processes) > 0
    
    def test_process_list_contains_lowercase(self):
        """Test that process names are lowercase"""
        monitor = SystemMonitor()
        metrics = monitor.get_current_state()
        
        for proc_name in metrics.processes[:10]:  # Check first 10
            assert proc_name == proc_name.lower()
    
    def test_process_is_running_detects_python(self):
        """Test that current Python process is detected"""
        monitor = SystemMonitor()
        
        # Python should be running (this test itself!)
        # Check for various Python process names (python, python.exe, python3.13.exe, etc.)
        processes = monitor._get_process_list()
        python_running = any('python' in proc for proc in processes)
        assert python_running, f"No Python process found. Processes: {[p for p in processes if 'py' in p][:10]}"
    
    def test_process_is_running_case_insensitive(self):
        """Test that process detection is case-insensitive"""
        monitor = SystemMonitor()
        
        # Should work with different cases
        assert monitor.process_is_running('PYTHON') == monitor.process_is_running('python')
        assert monitor.process_is_running('Python') == monitor.process_is_running('python')
    
    def test_process_is_running_nonexistent(self):
        """Test that nonexistent process returns False"""
        monitor = SystemMonitor()
        
        # Very unlikely process name
        assert monitor.process_is_running('totally_fake_process_12345') is False
    
    def test_metrics_to_dict(self):
        """Test that SystemMetrics can convert to dictionary"""
        monitor = SystemMonitor()
        metrics = monitor.get_current_state()
        
        metrics_dict = metrics.to_dict()
        
        assert isinstance(metrics_dict, dict)
        assert 'timestamp' in metrics_dict
        assert 'cpu_percent' in metrics_dict
        assert 'disk_read_mbps' in metrics_dict
        assert 'process_count' in metrics_dict
    
    def test_multiple_polls_update_rates(self):
        """Test that multiple polls produce different rate measurements"""
        monitor = SystemMonitor()
        
        # First poll (baseline)
        metrics1 = monitor.get_current_state()
        time.sleep(0.5)
        
        # Second poll
        metrics2 = monitor.get_current_state()
        time.sleep(0.5)
        
        # Third poll
        metrics3 = monitor.get_current_state()
        
        # Timestamps should be different
        assert metrics1.timestamp < metrics2.timestamp < metrics3.timestamp
    
    @patch('psutil.cpu_percent')
    def test_monitor_handles_psutil_cpu_exception(self, mock_cpu):
        """Test that monitor handles psutil exceptions gracefully"""
        mock_cpu.side_effect = psutil.Error("Mocked error")
        
        monitor = SystemMonitor()
        
        # Should raise the exception (we're not handling it yet in v0.1)
        with pytest.raises(psutil.Error):
            monitor._get_cpu_percent()
    
    def test_idle_time_returns_float(self):
        """Test that idle time returns a float (even if not implemented yet)"""
        monitor = SystemMonitor()
        idle_time = monitor._get_idle_time()
        
        assert isinstance(idle_time, float)
        assert idle_time >= 0.0


class TestSystemMetrics:
    """Test suite for SystemMetrics dataclass"""
    
    def test_system_metrics_creation(self):
        """Test that SystemMetrics can be created"""
        from datetime import datetime
        
        metrics = SystemMetrics(
            timestamp=datetime.now(),
            cpu_percent=50.0,
            disk_read_mbps=10.5,
            disk_write_mbps=5.2,
            net_sent_mbps=1.0,
            net_recv_mbps=2.5,
            processes=['python', 'chrome'],
            idle_time_seconds=120.0
        )
        
        assert metrics.cpu_percent == 50.0
        assert metrics.disk_read_mbps == 10.5
        assert len(metrics.processes) == 2


# Performance test (optional, can be slow)
@pytest.mark.slow
def test_monitor_performance():
    """Test that monitor polling is fast enough"""
    monitor = SystemMonitor()
    
    start_time = time.time()
    for _ in range(10):
        metrics = monitor.get_current_state()
    elapsed = time.time() - start_time
    
    # Should complete 10 polls in under 2 seconds
    assert elapsed < 2.0, f"10 polls took {elapsed:.2f}s (should be < 2.0s)"
