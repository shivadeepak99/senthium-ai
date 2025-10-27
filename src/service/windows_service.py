"""
Windows Service wrapper for Senthium daemon.
Allows Senthium to run as a Windows Service with auto-start on boot.

Installation:
    python -m service.windows_service install
    
Usage:
    sc start Senthium
    sc stop Senthium
    sc query Senthium
"""

import sys
import os
import logging
import time
from pathlib import Path

try:
    import win32serviceutil  # type: ignore
    import win32service  # type: ignore
    import win32event  # type: ignore
    import servicemanager  # type: ignore
except ImportError:
    print("[ERROR] pywin32 is required for Windows Service")
    print("        Install with: pip install pywin32")
    sys.exit(1)

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.daemon.core import SenthiumDaemon
from src.utils.logger import setup_logger


class SenthiumWindowsService(win32serviceutil.ServiceFramework):
    """Windows Service wrapper for Senthium daemon"""
    
    # Service identity
    _svc_name_ = "Senthium"
    _svc_display_name_ = "Senthium Power Management Daemon"
    _svc_description_ = (
        "Intelligent power management service that prevents system sleep "
        "during critical tasks (downloads, compilations, media serving). "
        "Uses configurable rules to automatically detect when to stay awake."
    )
    
    def __init__(self, args):
        """Initialize Windows Service"""
        win32serviceutil.ServiceFramework.__init__(self, args)
        
        # Create stop event
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.is_running = True
        self.daemon = None
        
        # Setup logging to AppData
        log_dir = Path.home() / 'AppData' / 'Local' / 'Senthium' / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = setup_logger(
            'senthium_service',
            level='INFO',
            log_dir=log_dir
        )
        
        self.logger.info("Service object created")
    
    def SvcStop(self):
        """Called when Windows requests service stop"""
        self.logger.info("Service stop requested by Windows")
        
        # Report that we're stopping
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        
        # Signal stop event
        win32event.SetEvent(self.stop_event)
        self.is_running = False
        
        # Stop daemon gracefully
        if self.daemon:
            try:
                self.logger.info("Shutting down daemon...")
                self.daemon.shutdown()
                self.logger.info("Daemon shut down successfully")
            except Exception as e:
                self.logger.error(f"Error shutting down daemon: {e}")
        
        # Report stopped
        self.ReportServiceStatus(win32service.SERVICE_STOPPED)
    
    def SvcDoRun(self):
        """Called when service starts"""
        self.logger.info("Service starting...")
        
        # Log to Windows Event Log
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, 'Service started successfully')
        )
        
        try:
            # Run main service loop
            self.main()
            
        except Exception as e:
            self.logger.exception(f"Service crashed: {e}")
            servicemanager.LogErrorMsg(f"Senthium service crashed: {e}")
            
        finally:
            self.logger.info("Service stopped")
            servicemanager.LogMsg(
                servicemanager.EVENTLOG_INFORMATION_TYPE,
                servicemanager.PYS_SERVICE_STOPPED,
                (self._svc_name_, 'Service stopped')
            )
    
    def main(self):
        """Main service loop"""
        try:
            # Get config path
            config_path = self.get_config_path()
            self.logger.info(f"Using config: {config_path}")
            
            # Verify config exists
            if not Path(config_path).exists():
                self.logger.error(f"Config file not found: {config_path}")
                self.logger.error("Service will exit. Please create config file.")
                return
            
            # Create daemon instance
            self.logger.info("Creating daemon instance...")
            self.daemon = SenthiumDaemon(config_path=config_path)
            
            self.logger.info("Starting daemon main loop...")
            
            # Start daemon in separate thread to allow stop signals
            import threading
            daemon_thread = threading.Thread(target=self.daemon.run, daemon=True)
            daemon_thread.start()
            
            # Wait for stop event
            self.logger.info("Service running. Waiting for stop signal...")
            while self.is_running:
                # Check stop event every second
                result = win32event.WaitForSingleObject(
                    self.stop_event,
                    1000  # 1 second timeout
                )
                
                if result == win32event.WAIT_OBJECT_0:
                    # Stop event signaled
                    break
                
                # Check if daemon thread is still alive
                if not daemon_thread.is_alive():
                    self.logger.error("Daemon thread died unexpectedly")
                    break
            
            self.logger.info("Stop signal received, cleaning up...")
            
            # Give daemon time to shutdown
            daemon_thread.join(timeout=5.0)
            
            if daemon_thread.is_alive():
                self.logger.warning("Daemon thread did not stop gracefully")
            
        except Exception as e:
            self.logger.exception(f"Error in main service loop: {e}")
            raise
    
    def get_config_path(self) -> str:
        """
        Get configuration file path.
        Priority:
        1. %USERPROFILE%\\AppData\\Local\\Senthium\\config.yaml
        2. Installation directory config\\config.yaml
        """
        # User-specific config in AppData
        user_config = Path.home() / 'AppData' / 'Local' / 'Senthium' / 'config.yaml'
        if user_config.exists():
            return str(user_config)
        
        # Installation directory config
        install_config = Path(__file__).parent.parent.parent / 'config' / 'config.yaml'
        if install_config.exists():
            return str(install_config)
        
        # Fallback to example config
        example_config = Path(__file__).parent.parent.parent / 'config' / 'config.example.yaml'
        if example_config.exists():
            self.logger.warning("Using example config (no config.yaml found)")
            return str(example_config)
        
        # Last resort
        self.logger.error("No config file found!")
        return str(user_config)  # Return expected path even if doesn't exist


def install_service():
    """Install Senthium as Windows Service"""
    print("[*] Installing Senthium as Windows Service...")
    print("")
    
    try:
        # Install service
        win32serviceutil.InstallService(
            SenthiumWindowsService._svc_reg_class_,
            SenthiumWindowsService._svc_name_,
            SenthiumWindowsService._svc_display_name_,
            startType=win32service.SERVICE_AUTO_START,
            description=SenthiumWindowsService._svc_description_
        )
        
        print("[OK] Service installed successfully!")
        print("")
        print("Service Details:")
        print(f"  Name:         {SenthiumWindowsService._svc_name_}")
        print(f"  Display Name: {SenthiumWindowsService._svc_display_name_}")
        print(f"  Start Type:   Automatic (starts on boot)")
        print("")
        print("Configuration:")
        config_path = Path.home() / 'AppData' / 'Local' / 'Senthium' / 'config.yaml'
        print(f"  Config File:  {config_path}")
        
        if not config_path.exists():
            print("")
            print("[WARN] Config file not found!")
            print("       Please create config.yaml before starting service:")
            print(f"       1. Create directory: {config_path.parent}")
            print(f"       2. Copy config: copy config\\config.example.yaml {config_path}")
            print(f"       3. Edit config: notepad {config_path}")
        
        print("")
        print("To start the service:")
        print("  sc start Senthium")
        print("  OR")
        print("  net start Senthium")
        print("")
        print("To stop the service:")
        print("  sc stop Senthium")
        print("")
        print("To check status:")
        print("  sc query Senthium")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to install service: {e}")
        print("")
        print("Common issues:")
        print("  • Run as Administrator (required for service installation)")
        print("  • Ensure pywin32 is installed: pip install pywin32")
        return False


def uninstall_service():
    """Uninstall Senthium Windows Service"""
    print("[*] Uninstalling Senthium service...")
    
    try:
        # Stop service if running
        try:
            win32serviceutil.StopService(SenthiumWindowsService._svc_name_)
            print("[*] Service stopped")
            time.sleep(2)
        except:
            pass  # Service might not be running
        
        # Remove service
        win32serviceutil.RemoveService(SenthiumWindowsService._svc_name_)
        
        print("[OK] Service uninstalled successfully!")
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to uninstall service: {e}")
        return False


if __name__ == '__main__':
    if len(sys.argv) == 1:
        # Called by Windows SCM (Service Control Manager)
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(SenthiumWindowsService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        # Called from command line
        command = sys.argv[1].lower() if len(sys.argv) > 1 else ''
        
        if command == 'install':
            install_service()
        elif command == 'remove' or command == 'uninstall':
            uninstall_service()
        else:
            # Use default pywin32 command handling
            win32serviceutil.HandleCommandLine(SenthiumWindowsService)
