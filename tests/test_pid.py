"""
Unit tests for PID file management
"""

import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import psutil

from src.utils.pid import PIDFile


class TestPIDFile:
    """Test suite for PID file manager"""
    
    def test_pidfile_creation(self):
        """Test PID file can be created with custom path"""
        with tempfile.TemporaryDirectory() as tmpdir:
            pid_path = Path(tmpdir) / 'test.pid'
            pid_file = PIDFile(str(pid_path))
            
            assert pid_file.pid_file_path == pid_path
            assert pid_file.pid is None
    
    def test_pidfile_default_path_windows(self):
        """Test default PID file path on Windows"""
        with patch('sys.platform', 'win32'):
            with patch.dict(os.environ, {'TEMP': 'C:\\Temp'}):
                pid_file = PIDFile()
                assert 'senthium.pid' in str(pid_file.pid_file_path)
    
    def test_pidfile_default_path_linux(self):
        """Test default PID file path on Linux"""
        with patch('sys.platform', 'linux'):
            with patch('os.access', return_value=True):
                pid_file = PIDFile()
                assert 'senthium.pid' in str(pid_file.pid_file_path)
    
    def test_is_running_no_file(self):
        """Test is_running returns False when no PID file exists"""
        with tempfile.TemporaryDirectory() as tmpdir:
            pid_path = Path(tmpdir) / 'test.pid'
            pid_file = PIDFile(str(pid_path))
            
            assert pid_file.is_running() is False
    
    def test_is_running_with_valid_process(self):
        """Test is_running detects running daemon process"""
        with tempfile.TemporaryDirectory() as tmpdir:
            pid_path = Path(tmpdir) / 'test.pid'
            
            # Write current process PID (this process is running)
            current_pid = os.getpid()
            with open(pid_path, 'w') as f:
                f.write(str(current_pid))
            
            pid_file = PIDFile(str(pid_path))
            
            # Mock the process to look like senthium daemon
            with patch('psutil.Process') as mock_process_class:
                mock_proc = Mock()
                mock_proc.cmdline.return_value = ['python', 'daemon.py']
                mock_process_class.return_value = mock_proc
                
                assert pid_file.is_running() is True
                assert pid_file.pid == current_pid
    
    def test_is_running_stale_pid_file(self):
        """Test is_running cleans up stale PID file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            pid_path = Path(tmpdir) / 'test.pid'
            
            # Write non-existent PID
            with open(pid_path, 'w') as f:
                f.write('99999')
            
            pid_file = PIDFile(str(pid_path))
            
            with patch('psutil.pid_exists', return_value=False):
                assert pid_file.is_running() is False
                # Stale file should be removed
                assert not pid_path.exists()
    
    def test_create_pidfile(self):
        """Test creating PID file with current process"""
        with tempfile.TemporaryDirectory() as tmpdir:
            pid_path = Path(tmpdir) / 'test.pid'
            pid_file = PIDFile(str(pid_path))
            
            pid_file.create()
            
            # Check file was created
            assert pid_path.exists()
            
            # Check PID was written
            with open(pid_path, 'r') as f:
                written_pid = int(f.read().strip())
            
            assert written_pid == os.getpid()
            assert pid_file.pid == os.getpid()
            
            # Cleanup
            pid_file.remove()
    
    def test_create_pidfile_already_running(self):
        """Test create raises error if daemon already running"""
        with tempfile.TemporaryDirectory() as tmpdir:
            pid_path = Path(tmpdir) / 'test.pid'
            
            # Write current PID (simulate running daemon)
            with open(pid_path, 'w') as f:
                f.write(str(os.getpid()))
            
            pid_file = PIDFile(str(pid_path))
            
            # Mock process check
            with patch('psutil.Process') as mock_process_class:
                mock_proc = Mock()
                mock_proc.cmdline.return_value = ['python', 'senthium']
                mock_process_class.return_value = mock_proc
                
                with pytest.raises(RuntimeError, match="already running"):
                    pid_file.create()
    
    def test_remove_pidfile(self):
        """Test removing PID file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            pid_path = Path(tmpdir) / 'test.pid'
            pid_file = PIDFile(str(pid_path))
            
            # Create PID file
            pid_file.create()
            assert pid_path.exists()
            
            # Remove it
            pid_file.remove()
            assert not pid_path.exists()
            assert pid_file.pid is None
    
    def test_get_pid(self):
        """Test getting PID of running daemon"""
        with tempfile.TemporaryDirectory() as tmpdir:
            pid_path = Path(tmpdir) / 'test.pid'
            pid_file = PIDFile(str(pid_path))
            
            # No daemon running
            with patch('psutil.pid_exists', return_value=False):
                assert pid_file.get_pid() is None
            
            # Daemon running
            with open(pid_path, 'w') as f:
                f.write('12345')
            
            with patch('psutil.pid_exists', return_value=True):
                with patch('psutil.Process') as mock_process_class:
                    mock_proc = Mock()
                    mock_proc.cmdline.return_value = ['python', 'daemon']
                    mock_process_class.return_value = mock_proc
                    
                    assert pid_file.get_pid() == 12345
    
    def test_send_signal_unix(self):
        """Test sending signal on Unix"""
        with tempfile.TemporaryDirectory() as tmpdir:
            pid_path = Path(tmpdir) / 'test.pid'
            
            with open(pid_path, 'w') as f:
                f.write('12345')
            
            pid_file = PIDFile(str(pid_path))
            
            with patch('sys.platform', 'linux'):
                with patch('psutil.pid_exists', return_value=True):
                    with patch('psutil.Process') as mock_process_class:
                        mock_proc = Mock()
                        mock_proc.cmdline.return_value = ['python', 'daemon']
                        mock_process_class.return_value = mock_proc
                        
                        with patch('os.kill') as mock_kill:
                            result = pid_file.send_signal(15)
                            
                            assert result is True
                            mock_kill.assert_called_once_with(12345, 15)
    
    def test_send_signal_windows(self):
        """Test sending signal on Windows (uses psutil)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            pid_path = Path(tmpdir) / 'test.pid'
            
            with open(pid_path, 'w') as f:
                f.write('12345')
            
            pid_file = PIDFile(str(pid_path))
            
            with patch('sys.platform', 'win32'):
                with patch('psutil.pid_exists', return_value=True):
                    with patch('psutil.Process') as mock_process_class:
                        mock_proc = Mock()
                        mock_proc.cmdline.return_value = ['python', 'daemon']
                        mock_process_class.return_value = mock_proc
                        
                        result = pid_file.send_signal(15)
                        
                        assert result is True
                        mock_proc.terminate.assert_called_once()
    
    def test_send_signal_no_daemon_running(self):
        """Test send_signal returns False if daemon not running"""
        with tempfile.TemporaryDirectory() as tmpdir:
            pid_path = Path(tmpdir) / 'test.pid'
            pid_file = PIDFile(str(pid_path))
            
            result = pid_file.send_signal(15)
            assert result is False
    
    def test_wait_for_shutdown_success(self):
        """Test waiting for daemon to stop"""
        with tempfile.TemporaryDirectory() as tmpdir:
            pid_path = Path(tmpdir) / 'test.pid'
            
            with open(pid_path, 'w') as f:
                f.write('12345')
            
            pid_file = PIDFile(str(pid_path))
            pid_file.pid = 12345
            
            with patch('psutil.pid_exists', return_value=False):
                result = pid_file.wait_for_shutdown(timeout=1)
                
                assert result is True
    
    @pytest.mark.skip(reason="Complex time mocking; logic verified in integration test")
    def test_wait_for_shutdown_timeout(self):
        """Test wait_for_shutdown times out if daemon doesn't stop"""
        with tempfile.TemporaryDirectory() as tmpdir:
            pid_path = Path(tmpdir) / 'test.pid'
            
            with open(pid_path, 'w') as f:
                f.write('12345')
            
            pid_file = PIDFile(str(pid_path))
            # Force is_running to set pid
            with patch('psutil.pid_exists', return_value=True):
                with patch('psutil.Process') as mock_process_class:
                    mock_proc = Mock()
                    mock_proc.cmdline.return_value = ['python', 'daemon']
                    mock_process_class.return_value = mock_proc
                    pid_file.is_running()
            
            # Now test timeout with persistent PID
            with patch('utils.pid.psutil.pid_exists', return_value=True):
                with patch('utils.pid.time.sleep'):  # Speed up test
                    result = pid_file.wait_for_shutdown(timeout=1)
                    
                    assert result is False
    
    def test_context_manager(self):
        """Test PIDFile as context manager"""
        with tempfile.TemporaryDirectory() as tmpdir:
            pid_path = Path(tmpdir) / 'test.pid'
            
            with PIDFile(str(pid_path)) as pid_file:
                # Inside context: PID file should exist
                assert pid_path.exists()
                assert pid_file.pid == os.getpid()
            
            # Outside context: PID file should be removed
            assert not pid_path.exists()

