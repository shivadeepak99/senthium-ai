"""
Unit tests for daemon control module
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
from pathlib import Path
import sys

from src.daemon.control import (
    start_daemon,
    stop_daemon,
    restart_daemon,
    daemon_status
)


class TestDaemonControl:
    """Test suite for daemon control functions"""
    
    def test_start_daemon_already_running(self):
        """Test start_daemon fails if daemon already running"""
        with patch('src.daemon.control.PIDFile') as mock_pidfile_class:
            mock_pidfile = Mock()
            mock_pidfile.is_running.return_value = True
            mock_pidfile.get_pid.return_value = 12345
            mock_pidfile_class.return_value = mock_pidfile
            
            result = start_daemon()
            
            assert result == 1  # Error code
            mock_pidfile.is_running.assert_called_once()
    
    def test_start_daemon_foreground_success(self):
        """Test starting daemon in foreground mode"""
        with patch('src.daemon.control.PIDFile') as mock_pidfile_class:
            mock_pidfile = Mock()
            mock_pidfile.is_running.return_value = False
            mock_pidfile.__enter__ = Mock(return_value=mock_pidfile)
            mock_pidfile.__exit__ = Mock(return_value=False)
            mock_pidfile_class.return_value = mock_pidfile
            
            # Mock the dynamically imported SenthiumDaemon
            with patch('src.daemon.core.SenthiumDaemon') as mock_daemon_class:
                mock_daemon = Mock()
                mock_daemon_class.return_value = mock_daemon
                
                with patch('src.utils.logger.setup_logger'):
                    result = start_daemon(foreground=True)
                    
                    assert result == 0
                    mock_daemon.run.assert_called_once()
    
    def test_start_daemon_foreground_keyboard_interrupt(self):
        """Test foreground daemon handles Ctrl+C gracefully"""
        with patch('src.daemon.control.PIDFile') as mock_pidfile_class:
            mock_pidfile = Mock()
            mock_pidfile.is_running.return_value = False
            mock_pidfile.__enter__ = Mock(return_value=mock_pidfile)
            mock_pidfile.__exit__ = Mock(return_value=False)
            mock_pidfile_class.return_value = mock_pidfile
            
            # Mock the dynamically imported SenthiumDaemon
            with patch('src.daemon.core.SenthiumDaemon') as mock_daemon_class:
                mock_daemon = Mock()
                mock_daemon.run.side_effect = KeyboardInterrupt()
                mock_daemon_class.return_value = mock_daemon
                
                with patch('src.utils.logger.setup_logger'):
                    result = start_daemon(foreground=True)
                    
                    assert result == 0  # Clean exit on Ctrl+C
    
    def test_start_daemon_background_success(self):
        """Test starting daemon in background mode"""
        with patch('src.daemon.control.PIDFile') as mock_pidfile_class:
            mock_pidfile = Mock()
            mock_pidfile.is_running.side_effect = [False, True]  # Not running, then running
            mock_pidfile.get_pid.return_value = 99999
            mock_pidfile_class.return_value = mock_pidfile
            
            with patch('src.daemon.control.subprocess.Popen') as mock_popen:
                mock_process = Mock()
                mock_process.pid = 99999
                mock_popen.return_value = mock_process
                
                with patch('src.daemon.control.time.sleep'):
                    with patch('src.daemon.control.Path'):
                        result = start_daemon(foreground=False)
                        
                        assert result == 0
                        mock_popen.assert_called_once()
    
    def test_start_daemon_background_windows(self):
        """Test background start on Windows uses correct flags"""
        with patch('src.daemon.control.PIDFile') as mock_pidfile_class:
            mock_pidfile = Mock()
            mock_pidfile.is_running.side_effect = [False, True]
            mock_pidfile.get_pid.return_value = 99999
            mock_pidfile_class.return_value = mock_pidfile
            
            with patch('sys.platform', new='win32'):
                with patch('src.daemon.control.subprocess.Popen') as mock_popen:
                    mock_process = Mock()
                    mock_process.pid = 99999
                    mock_popen.return_value = mock_process
                    
                    with patch('src.daemon.control.time.sleep'):
                        with patch('src.daemon.control.Path'):
                            result = start_daemon(foreground=False)
                            
                            assert result == 0
                            # Verify Popen was called
                            mock_popen.assert_called_once()
                            # Check Windows-specific creation flags were used
                            call_kwargs = mock_popen.call_args[1]
                            assert 'creationflags' in call_kwargs
    
    def test_stop_daemon_not_running(self):
        """Test stop_daemon when daemon not running"""
        with patch('src.daemon.control.PIDFile') as mock_pidfile_class:
            mock_pidfile = Mock()
            mock_pidfile.get_pid.return_value = None
            mock_pidfile_class.return_value = mock_pidfile
            
            result = stop_daemon()
            
            assert result == 0  # Success (nothing to stop)
    
    def test_stop_daemon_graceful(self):
        """Test graceful daemon shutdown"""
        with patch('src.daemon.control.PIDFile') as mock_pidfile_class:
            mock_pidfile = Mock()
            mock_pidfile.get_pid.return_value = 12345
            mock_pidfile.send_signal.return_value = True
            mock_pidfile.wait_for_shutdown.return_value = True
            mock_pidfile_class.return_value = mock_pidfile
            
            result = stop_daemon(force=False, timeout=10)
            
            assert result == 0
            mock_pidfile.send_signal.assert_called_once()
            mock_pidfile.wait_for_shutdown.assert_called_once_with(timeout=10)
    
    def test_stop_daemon_timeout(self):
        """Test stop_daemon when graceful shutdown times out"""
        with patch('src.daemon.control.PIDFile') as mock_pidfile_class:
            mock_pidfile = Mock()
            mock_pidfile.get_pid.return_value = 12345
            mock_pidfile.send_signal.return_value = True
            mock_pidfile.wait_for_shutdown.return_value = False  # Timeout
            mock_pidfile_class.return_value = mock_pidfile
            
            result = stop_daemon(force=False, timeout=5)
            
            assert result == 1  # Error
    
    def test_stop_daemon_force(self):
        """Test force kill daemon"""
        with patch('src.daemon.control.PIDFile') as mock_pidfile_class:
            mock_pidfile = Mock()
            mock_pidfile.get_pid.return_value = 12345
            mock_pidfile.send_signal.return_value = True
            mock_pidfile.is_running.return_value = False
            mock_pidfile_class.return_value = mock_pidfile
            
            with patch('src.daemon.control.time.sleep'):
                result = stop_daemon(force=True)
                
                assert result == 0
                # Should use SIGKILL or 9
                call_args = mock_pidfile.send_signal.call_args[0]
                assert call_args[0] in [9, 15]  # Platform dependent
    
    def test_restart_daemon_success(self):
        """Test restarting daemon"""
        with patch('src.daemon.control.stop_daemon') as mock_stop:
            mock_stop.return_value = 0
            
            with patch('src.daemon.control.start_daemon') as mock_start:
                mock_start.return_value = 0
                
                with patch('src.daemon.control.time.sleep'):
                    result = restart_daemon()
                    
                    assert result == 0
                    mock_stop.assert_called_once()
                    mock_start.assert_called_once()
    
    def test_restart_daemon_stop_fails(self):
        """Test restart fails if stop fails"""
        with patch('src.daemon.control.stop_daemon') as mock_stop:
            mock_stop.return_value = 1  # Error
            
            result = restart_daemon()
            
            assert result == 1
    
    def test_daemon_status_running(self):
        """Test daemon_status when daemon is running"""
        with patch('src.daemon.control.PIDFile') as mock_pidfile_class:
            mock_pidfile = Mock()
            mock_pidfile.is_running.return_value = True
            mock_pidfile.get_pid.return_value = 12345
            mock_pidfile.pid_file_path = Path('/tmp/senthium.pid')
            mock_pidfile_class.return_value = mock_pidfile
            
            result = daemon_status(verbose=False)
            
            assert result == 0
    
    def test_daemon_status_not_running(self):
        """Test daemon_status when daemon not running"""
        with patch('src.daemon.control.PIDFile') as mock_pidfile_class:
            mock_pidfile = Mock()
            mock_pidfile.is_running.return_value = False
            mock_pidfile_class.return_value = mock_pidfile
            
            result = daemon_status(verbose=False)
            
            assert result == 1
    
    def test_daemon_status_verbose(self):
        """Test verbose daemon status with IPC"""
        with patch('src.daemon.control.PIDFile') as mock_pidfile_class:
            mock_pidfile = Mock()
            mock_pidfile.is_running.return_value = True
            mock_pidfile.get_pid.return_value = 12345
            mock_pidfile.pid_file_path = Path('/tmp/senthium.pid')
            mock_pidfile_class.return_value = mock_pidfile
            
            # Mock the dynamically imported IPCClient
            with patch('ipc.IPCClient') as mock_ipc_class:
                mock_client = Mock()
                mock_response = Mock()
                mock_response.success = True
                mock_response.data = {
                    'state': 'monitoring',
                    'uptime_seconds': 120,
                    'poll_count': 10,
                    'awake': False
                }
                mock_client.send_command.return_value = mock_response
                mock_ipc_class.return_value = mock_client
                
                result = daemon_status(verbose=True)
                
                assert result == 0
                mock_client.send_command.assert_called_once_with('STATUS')

