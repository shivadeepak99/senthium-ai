"""
Daemon control module for starting/stopping/managing Senthium daemon.

Provides commands to control the daemon lifecycle:
- start: Start daemon in background
- stop: Stop running daemon
- restart: Restart daemon
- status: Check daemon status
"""

import sys
import os
import logging
import signal
import subprocess
import time
from pathlib import Path
from typing import Optional

from utils.pid import PIDFile

logger = logging.getLogger(__name__)


def start_daemon(
    config_path: str = "config/config.yaml",
    log_level: str = "INFO",
    foreground: bool = False
) -> int:
    """
    Start Senthium daemon.
    
    Args:
        config_path: Path to configuration file
        log_level: Logging level
        foreground: If True, run in foreground (don't detach)
        
    Returns:
        Exit code (0 = success)
    """
    pid_file = PIDFile()
    
    # Check if already running
    if pid_file.is_running():
        print(f"[ERROR] Daemon is already running (PID {pid_file.get_pid()})")
        print("        Stop it first with: senthium stop")
        return 1
    
    if foreground:
        # Run in foreground (blocking)
        print("[*] Starting daemon in foreground mode...")
        print("    Press Ctrl+C to stop")
        
        # Import and run daemon directly
        from daemon.core import SenthiumDaemon
        from utils.logger import setup_logger
        
        setup_logger('senthium', level=log_level)
        
        try:
            with pid_file:  # Automatically creates and removes PID file
                daemon = SenthiumDaemon(config_path=config_path)
                daemon.run()
            return 0
        except KeyboardInterrupt:
            print("\n[WARN] Interrupted by user")
            return 0
        except Exception as e:
            logger.exception(f"Daemon failed: {e}")
            return 1
    
    else:
        # Run in background (detached)
        print("[*] Starting daemon in background...")
        
        # Get Python executable and daemon script path
        python_exe = sys.executable
        daemon_script = Path(__file__).parent.parent / "daemon" / "core.py"
        
        # Build command
        cmd = [
            python_exe,
            str(daemon_script),
            "--config", config_path,
            "--log-level", log_level
        ]
        
        # Set up environment with PYTHONPATH
        env = os.environ.copy()
        env['PYTHONPATH'] = str(Path(__file__).parent.parent)
        
        try:
            # Start daemon as background process
            if sys.platform == "win32":
                # Windows: Use CREATE_NEW_PROCESS_GROUP and CREATE_NO_WINDOW
                import subprocess as sp
                DETACHED_PROCESS = 0x00000008
                CREATE_NO_WINDOW = 0x08000000
                CREATE_NEW_PROCESS_GROUP = 0x00000200
                
                process = sp.Popen(
                    cmd,
                    env=env,
                    creationflags=CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP | DETACHED_PROCESS,
                    stdin=sp.DEVNULL,
                    stdout=sp.DEVNULL,
                    stderr=sp.DEVNULL,
                    close_fds=True
                )
            else:
                # Unix: Fork and detach
                process = subprocess.Popen(
                    cmd,
                    env=env,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                    close_fds=True
                )
            
            # Wait a moment to see if daemon starts successfully
            print(f"    Daemon process launched (PID {process.pid})")
            print(f"    Waiting for initialization...")
            time.sleep(3)
            
            # Check if daemon is running
            if pid_file.is_running():
                pid = pid_file.get_pid()
                print(f"[OK] Daemon started successfully (PID {pid})")
                print(f"     Config: {config_path}")
                print(f"     Check status: senthium status")
                return 0
            else:
                print("[ERROR] Daemon failed to start")
                print("        The process may have crashed during initialization")
                print("        Try running in foreground to see errors:")
                print(f"        senthium start --foreground --config {config_path}")
                return 1
                
        except Exception as e:
            print(f"[ERROR] Failed to start daemon: {e}")
            import traceback
            traceback.print_exc()
            return 1


def stop_daemon(force: bool = False, timeout: int = 10) -> int:
    """
    Stop running Senthium daemon.
    
    Args:
        force: If True, force kill daemon (SIGKILL)
        timeout: Time to wait for graceful shutdown
        
    Returns:
        Exit code (0 = success)
    """
    pid_file = PIDFile()
    
    # Check if running
    pid = pid_file.get_pid()
    if pid is None:
        print("[WARN] Daemon is not running")
        return 0
    
    print(f"[*] Stopping daemon (PID {pid})...")
    
    if force:
        # Force kill (SIGKILL / terminate)
        print("    Using force kill...")
        if pid_file.send_signal(signal.SIGKILL if sys.platform != "win32" else 9):
            time.sleep(1)
            if not pid_file.is_running():
                print("[OK] Daemon forcefully terminated")
                pid_file.remove()
                return 0
            else:
                print("[ERROR] Failed to kill daemon")
                return 1
        else:
            return 1
    
    else:
        # Graceful shutdown (SIGTERM)
        if pid_file.send_signal(signal.SIGTERM if sys.platform != "win32" else 15):
            print(f"    Waiting for graceful shutdown (max {timeout}s)...")
            
            if pid_file.wait_for_shutdown(timeout=timeout):
                print("[OK] Daemon stopped gracefully")
                return 0
            else:
                print(f"[WARN] Daemon did not stop within {timeout}s")
                print("       Try: senthium stop --force")
                return 1
        else:
            return 1


def restart_daemon(
    config_path: str = "config/config.yaml",
    log_level: str = "INFO"
) -> int:
    """
    Restart Senthium daemon.
    
    Args:
        config_path: Path to configuration file
        log_level: Logging level
        
    Returns:
        Exit code (0 = success)
    """
    print("[*] Restarting daemon...")
    
    # Stop if running
    result = stop_daemon(force=False, timeout=10)
    if result != 0:
        print("[ERROR] Failed to stop daemon")
        return result
    
    # Small delay
    time.sleep(1)
    
    # Start again
    return start_daemon(config_path=config_path, log_level=log_level, foreground=False)


def daemon_status(verbose: bool = False) -> int:
    """
    Check daemon status.
    
    Args:
        verbose: If True, show detailed status
        
    Returns:
        Exit code (0 = running, 1 = not running)
    """
    pid_file = PIDFile()
    
    if pid_file.is_running():
        pid = pid_file.get_pid()
        print("[OK] Daemon is running")
        print(f"     PID: {pid}")
        print(f"     PID file: {pid_file.pid_file_path}")
        
        if verbose:
            # Try to get detailed status via IPC
            try:
                from ipc import IPCClient
                
                client = IPCClient(timeout=2.0)
                response = client.send_command("STATUS")
                
                if response.success:
                    data = response.data
                    print(f"     State: {data.get('state', 'unknown')}")
                    print(f"     Uptime: {_format_uptime(data.get('uptime_seconds', 0))}")
                    print(f"     Polls: {data.get('poll_count', 0)}")
                    print(f"     Active: {data.get('awake', False)}")
                    
            except Exception as e:
                print(f"     [WARN] Could not get detailed status: {e}")
        
        return 0
    else:
        print("[INFO] Daemon is not running")
        print("       Start it with: senthium start")
        return 1


def _format_uptime(seconds: float) -> str:
    """Format uptime in human-readable form."""
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes}m"
    else:
        hours = int(seconds / 3600)
        minutes = int((seconds % 3600) / 60)
        return f"{hours}h {minutes}m" if minutes > 0 else f"{hours}h"
