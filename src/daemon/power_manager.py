"""
Power Manager Module
Cross-platform system sleep prevention with OS-specific implementations

Supports:
- Windows: SetThreadExecutionState (Win32 API)
- Linux: systemd-logind D-Bus inhibitor (with xdg-screensaver fallback)
- macOS: IOPMAssertion (IOKit framework)
"""

import platform
import logging
from typing import Optional
from abc import ABC, abstractmethod


class PowerManagerBase(ABC):
    """Base class for platform-specific power managers"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._is_awake_asserted = False
    
    @abstractmethod
    def assert_awake(self) -> bool:
        """
        Prevent system from sleeping/locking
        
        Returns:
            True if assertion successful, False otherwise
        """
        pass
    
    @abstractmethod
    def release_awake(self) -> bool:
        """
        Allow system to sleep/lock normally
        
        Returns:
            True if release successful, False otherwise
        """
        pass
    
    @property
    def is_awake_asserted(self) -> bool:
        """Check if stay-awake is currently asserted"""
        return self._is_awake_asserted


class WindowsPowerManager(PowerManagerBase):
    """
    Windows power management via SetThreadExecutionState
    
    Uses kernel32.dll Win32 API to prevent sleep and display dimming.
    No admin rights required, works on Windows 7+.
    """
    
    # SetThreadExecutionState flags
    ES_CONTINUOUS = 0x80000000
    ES_SYSTEM_REQUIRED = 0x00000001
    ES_DISPLAY_REQUIRED = 0x00000002
    ES_AWAYMODE_REQUIRED = 0x00000040
    
    def __init__(self):
        super().__init__()
        try:
            import ctypes
            self.kernel32 = ctypes.windll.kernel32
            self.user32 = ctypes.windll.user32
            self.logger.info("Windows power manager initialized (SetThreadExecutionState)")
        except Exception as e:
            self.logger.error(f"Failed to load Win32 APIs: {e}")
            self.kernel32 = None
    
    def assert_awake(self) -> bool:
        """Prevent Windows from sleeping and dimming display"""
        if not self.kernel32:
            self.logger.error("Win32 API not available")
            return False
        
        if self._is_awake_asserted:
            return True  # Already asserted
        
        try:
            result = self.kernel32.SetThreadExecutionState(
                self.ES_CONTINUOUS | 
                self.ES_SYSTEM_REQUIRED | 
                self.ES_DISPLAY_REQUIRED
            )
            
            if result:
                self._is_awake_asserted = True
                self.logger.info("✅ Stay-awake asserted (Windows)")
                return True
            else:
                self.logger.error("SetThreadExecutionState returned 0 (failed)")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to assert stay-awake: {e}")
            return False
    
    def release_awake(self) -> bool:
        """Allow Windows to sleep normally"""
        if not self.kernel32:
            return False
        
        if not self._is_awake_asserted:
            return True  # Already released
        
        try:
            result = self.kernel32.SetThreadExecutionState(self.ES_CONTINUOUS)
            
            if result:
                self._is_awake_asserted = False
                self.logger.info("🌙 Stay-awake released (Windows)")
                return True
            else:
                self.logger.warning("SetThreadExecutionState release returned 0")
                # Force state to released anyway
                self._is_awake_asserted = False
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to release stay-awake: {e}")
            return False
    
    def get_idle_time(self) -> float:
        """
        Get seconds since last user input (keyboard/mouse)
        
        Returns:
            Idle time in seconds
        """
        if not self.user32 or not self.kernel32:
            return 0.0
        
        try:
            import ctypes
            from ctypes import wintypes
            
            class LASTINPUTINFO(ctypes.Structure):
                _fields_ = [
                    ('cbSize', wintypes.UINT),
                    ('dwTime', wintypes.DWORD),
                ]
            
            lii = LASTINPUTINFO()
            lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
            
            if self.user32.GetLastInputInfo(ctypes.byref(lii)):
                millis = self.kernel32.GetTickCount() - lii.dwTime  # type: ignore
                return millis / 1000.0
            
            return 0.0
            
        except Exception as e:
            self.logger.error(f"Failed to get idle time: {e}")
            return 0.0


class LinuxPowerManager(PowerManagerBase):
    """
    Linux power management via systemd-logind D-Bus
    
    Falls back to xdg-screensaver if D-Bus unavailable.
    Works on most modern Linux distros with systemd.
    """
    
    def __init__(self):
        super().__init__()
        self.inhibitor_fd = None
        self.method = self._detect_method()
        self.logger.info(f"Linux power manager initialized (method: {self.method})")
    
    def _detect_method(self) -> str:
        """Detect best available power management method"""
        try:
            import dbus  # type: ignore  # Linux-only dependency
            bus = dbus.SystemBus()
            bus.get_object('org.freedesktop.login1', '/org/freedesktop/login1')
            return 'systemd'
        except:
            # Fall back to xdg-screensaver
            import subprocess
            try:
                subprocess.run(['which', 'xdg-screensaver'], 
                             check=True, capture_output=True)
                return 'xdg'
            except:
                self.logger.warning("No supported power management method found")
                return 'none'
    
    def assert_awake(self) -> bool:
        """Prevent Linux system from sleeping/locking"""
        if self._is_awake_asserted:
            return True
        
        if self.method == 'systemd':
            return self._inhibit_systemd()
        elif self.method == 'xdg':
            return self._reset_screensaver()
        else:
            self.logger.error("No power management method available")
            return False
    
    def release_awake(self) -> bool:
        """Allow Linux system to sleep normally"""
        if not self._is_awake_asserted:
            return True
        
        if self.method == 'systemd' and self.inhibitor_fd:
            try:
                import os
                os.close(self.inhibitor_fd)
                self.inhibitor_fd = None
                self._is_awake_asserted = False
                self.logger.info("🌙 Stay-awake released (Linux/systemd)")
                return True
            except Exception as e:
                self.logger.error(f"Failed to release systemd inhibitor: {e}")
                return False
        
        # xdg-screensaver doesn't need explicit release
        self._is_awake_asserted = False
        return True
    
    def _inhibit_systemd(self) -> bool:
        """Use systemd-logind Inhibit to prevent sleep"""
        try:
            import dbus  # type: ignore  # Linux-only dependency
            bus = dbus.SystemBus()
            login_manager = bus.get_object(
                'org.freedesktop.login1',
                '/org/freedesktop/login1'
            )
            interface = dbus.Interface(
                login_manager,
                'org.freedesktop.login1.Manager'
            )
            
            # Inhibit both idle and sleep
            self.inhibitor_fd = interface.Inhibit(
                "idle:sleep",
                "Senthium",
                "Critical task running - stay awake requested",
                "block"
            )
            
            self._is_awake_asserted = True
            self.logger.info("✅ Stay-awake asserted (Linux/systemd)")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create systemd inhibitor: {e}")
            return False
    
    def _reset_screensaver(self) -> bool:
        """Poke xdg-screensaver to prevent lock (legacy fallback)"""
        try:
            import subprocess
            subprocess.run(['xdg-screensaver', 'reset'], 
                         check=True, capture_output=True)
            self._is_awake_asserted = True
            self.logger.debug("xdg-screensaver reset")
            return True
        except Exception as e:
            self.logger.error(f"Failed to reset screensaver: {e}")
            return False


class MacOSPowerManager(PowerManagerBase):
    """
    macOS power management via IOKit IOPMAssertion
    
    Uses IOKit framework to create power assertions.
    Works on macOS 10.9+, both Intel and Apple Silicon.
    """
    
    def __init__(self):
        super().__init__()
        self.assertion_id = None
        try:
            import ctypes
            import ctypes.util
            
            # Load IOKit framework
            iokit_path = ctypes.util.find_library('IOKit')
            self.iokit = ctypes.CDLL(iokit_path) if iokit_path else None
            
            if self.iokit:
                self.logger.info("macOS power manager initialized (IOPMAssertion)")
            else:
                self.logger.error("Failed to load IOKit framework")
        except Exception as e:
            self.logger.error(f"Failed to initialize macOS power manager: {e}")
            self.iokit = None
    
    def assert_awake(self) -> bool:
        """Create IOPMAssertion to prevent macOS sleep"""
        if not self.iokit:
            return False
        
        if self._is_awake_asserted:
            return True
        
        try:
            import ctypes
            from ctypes import c_void_p, c_char_p, c_uint32, byref
            
            assertion_id = c_uint32()
            assertion_type = b"PreventUserIdleDisplaySleep"
            reason = b"Senthium: Critical task running"
            
            result = self.iokit.IOPMAssertionCreateWithName(
                assertion_type,
                c_uint32(255),  # kIOPMAssertionLevelOn
                reason,
                byref(assertion_id)
            )
            
            if result == 0:  # kIOReturnSuccess
                self.assertion_id = assertion_id.value
                self._is_awake_asserted = True
                self.logger.info(f"✅ Stay-awake asserted (macOS, ID: {self.assertion_id})")
                return True
            else:
                self.logger.error(f"IOPMAssertionCreateWithName failed: {result}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to create macOS assertion: {e}")
            return False
    
    def release_awake(self) -> bool:
        """Release IOPMAssertion"""
        if not self.iokit or not self._is_awake_asserted:
            return True
        
        if self.assertion_id is None:
            return True
        
        try:
            import ctypes
            from ctypes import c_uint32
            
            result = self.iokit.IOPMAssertionRelease(c_uint32(self.assertion_id))
            
            if result == 0:
                self.logger.info(f"🌙 Stay-awake released (macOS, ID: {self.assertion_id})")
                self.assertion_id = None
                self._is_awake_asserted = False
                return True
            else:
                self.logger.error(f"IOPMAssertionRelease failed: {result}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to release macOS assertion: {e}")
            return False


def create_power_manager() -> PowerManagerBase:
    """
    Factory function to create platform-appropriate power manager
    
    Returns:
        PowerManagerBase subclass for current platform
    """
    system = platform.system()
    
    if system == 'Windows':
        return WindowsPowerManager()
    elif system == 'Linux':
        return LinuxPowerManager()
    elif system == 'Darwin':  # macOS
        return MacOSPowerManager()
    else:
        raise NotImplementedError(f"Platform '{system}' not supported")


# Example usage / testing
if __name__ == '__main__':
    from utils.logger import setup_logger
    import time
    
    # Setup logging
    logger = setup_logger('senthium.power', level='DEBUG')
    
    print(f"🔌 Senthium Power Manager Test - {platform.system()}")
    print("=" * 60)
    
    try:
        # Create power manager
        pm = create_power_manager()
        
        print("\n📋 Test 1: Assert stay-awake")
        success = pm.assert_awake()
        print(f"  Result: {'✅ Success' if success else '❌ Failed'}")
        print(f"  Asserted: {pm.is_awake_asserted}")
        
        print("\n⏳ Staying awake for 10 seconds...")
        print("  Try to put your computer to sleep - it should resist! 😎")
        time.sleep(10)
        
        print("\n📋 Test 2: Release stay-awake")
        success = pm.release_awake()
        print(f"  Result: {'✅ Success' if success else '❌ Failed'}")
        print(f"  Asserted: {pm.is_awake_asserted}")
        
        print("\n✅ Power manager test complete!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise
