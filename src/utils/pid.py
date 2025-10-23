"""
PID file management for daemon process.

Ensures only one daemon instance runs at a time by creating/checking
a PID file that stores the process ID.
"""

import os
import sys
import logging
import psutil
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class PIDFile:
    """
    PID file manager for daemon process.
    
    Creates and manages a PID file to prevent multiple daemon instances.
    """
    
    def __init__(self, pid_file_path: Optional[str] = None):
        """
        Initialize PID file manager.
        
        Args:
            pid_file_path: Path to PID file. Defaults to platform-specific location.
        """
        if pid_file_path is None:
            # Platform-specific default locations
            if sys.platform == "win32":
                # Windows: Use temp directory
                pid_file_path = os.path.join(os.environ.get('TEMP', 'C:\\Temp'), 'senthium.pid')
            else:
                # Linux/macOS: Use /var/run or /tmp
                if os.access('/var/run', os.W_OK):
                    pid_file_path = '/var/run/senthium.pid'
                else:
                    pid_file_path = '/tmp/senthium.pid'
        
        self.pid_file_path = Path(pid_file_path)
        self.pid: Optional[int] = None
    
    def is_running(self) -> bool:
        """
        Check if daemon is already running.
        
        Returns:
            True if daemon process is running, False otherwise
        """
        if not self.pid_file_path.exists():
            return False
        
        try:
            with open(self.pid_file_path, 'r') as f:
                pid_str = f.read().strip()
                pid = int(pid_str)
            
            # Check if process with this PID exists and is a Senthium daemon
            if psutil.pid_exists(pid):
                try:
                    proc = psutil.Process(pid)
                    # Check if it's actually a Python process running senthium
                    cmdline = proc.cmdline()
                    if any('senthium' in arg.lower() or 'daemon' in arg.lower() for arg in cmdline):
                        logger.debug(f"Daemon is running with PID {pid}")
                        self.pid = pid
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # PID file exists but process is dead - clean up stale PID file
            logger.warning(f"Stale PID file found (PID {pid} not running)")
            self.remove()
            return False
            
        except (ValueError, IOError) as e:
            logger.error(f"Error reading PID file: {e}")
            return False
    
    def create(self) -> None:
        """
        Create PID file with current process ID.
        
        Raises:
            RuntimeError: If daemon is already running
        """
        if self.is_running():
            raise RuntimeError(
                f"Daemon is already running with PID {self.pid}. "
                f"Stop it first with: senthium stop"
            )
        
        # Create parent directory if needed
        self.pid_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write current PID
        pid = os.getpid()
        try:
            with open(self.pid_file_path, 'w') as f:
                f.write(str(pid))
            
            # Set permissions (owner only)
            if sys.platform != "win32":
                os.chmod(self.pid_file_path, 0o600)
            
            self.pid = pid
            logger.info(f"PID file created: {self.pid_file_path} (PID: {pid})")
            
        except IOError as e:
            raise RuntimeError(f"Failed to create PID file: {e}")
    
    def remove(self) -> None:
        """Remove PID file."""
        if self.pid_file_path.exists():
            try:
                self.pid_file_path.unlink()
                logger.info(f"PID file removed: {self.pid_file_path}")
            except IOError as e:
                logger.error(f"Failed to remove PID file: {e}")
        
        self.pid = None
    
    def get_pid(self) -> Optional[int]:
        """
        Get PID of running daemon.
        
        Returns:
            PID if daemon is running, None otherwise
        """
        if self.is_running():
            return self.pid
        return None
    
    def send_signal(self, sig: int) -> bool:
        """
        Send signal to running daemon process.
        
        Args:
            sig: Signal number (e.g., signal.SIGTERM)
            
        Returns:
            True if signal sent successfully, False otherwise
        """
        pid = self.get_pid()
        if pid is None:
            logger.error("Cannot send signal: daemon is not running")
            return False
        
        try:
            if sys.platform == "win32":
                # Windows doesn't support signals the same way
                # Use psutil to terminate/kill process
                proc = psutil.Process(pid)
                if sig == 15:  # SIGTERM equivalent
                    proc.terminate()
                elif sig == 9:  # SIGKILL equivalent
                    proc.kill()
                else:
                    logger.warning(f"Signal {sig} not supported on Windows, using terminate()")
                    proc.terminate()
            else:
                # Unix/Linux: Send actual signal
                os.kill(pid, sig)
            
            logger.info(f"Sent signal {sig} to daemon (PID {pid})")
            return True
            
        except (psutil.NoSuchProcess, ProcessLookupError):
            logger.error(f"Process {pid} not found")
            self.remove()  # Clean up stale PID file
            return False
        except Exception as e:
            logger.error(f"Failed to send signal to daemon: {e}")
            return False
    
    def wait_for_shutdown(self, timeout: int = 10) -> bool:
        """
        Wait for daemon process to shutdown.
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            True if daemon stopped, False if timeout
        """
        import time
        
        pid = self.get_pid()
        if pid is None:
            return True
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            if not psutil.pid_exists(pid):
                logger.info(f"Daemon stopped (PID {pid})")
                self.remove()
                return True
            time.sleep(0.2)
        
        logger.warning(f"Daemon did not stop within {timeout}s")
        return False
    
    def __enter__(self):
        """Context manager entry - create PID file."""
        self.create()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - remove PID file."""
        self.remove()
        return False
