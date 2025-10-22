"""
Lock Controller module for platform-specific system lock actions.
Handles: inhibit sleep, lock screen, dim display, keyboard/mouse control.
"""
import platform
import subprocess
import logging
from typing import Optional
from enum import Enum

logger = logging.getLogger(__name__)


class LockAction(Enum):
    """Supported lock actions."""
    KEEP_AWAKE = "keep_awake"
    DELAY_LOCK = "delay_lock"
    FULL_LOCK = "full_lock"
    RESTORE = "restore"
    DIM_SCREEN = "dim_screen"
    SCREEN_OFF = "screen_off"


class LockController:
    """
    Platform-specific controller for system lock and power management.
    
    Supports:
    - Linux: systemd-inhibit, xset, loginctl, gnome-screensaver
    - macOS: caffeinate, pmset, CGSession
    - Windows: powercfg, rundll32, SetThreadExecutionState
    """
    
    def __init__(self, dry_run: bool = False):
        """
        Initialize lock controller.
        
        Args:
            dry_run: If True, log actions without executing
        """
        self.dry_run = dry_run
        self.platform = platform.system()
        self.sleep_inhibitor_pid = None
        
        logger.info(f"LockController initialized for {self.platform} (dry_run={dry_run})")
    
    def _run_command(self, cmd: list, check: bool = False) -> Optional[subprocess.CompletedProcess]:
        """
        Run a system command.
        
        Args:
            cmd: Command and arguments as list
            check: Raise exception on non-zero exit code
            
        Returns:
            CompletedProcess if executed, None if dry_run
        """
        if self.dry_run:
            logger.info(f"[DRY-RUN] Would execute: {' '.join(cmd)}")
            return None
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=check)
            logger.debug(f"Executed: {' '.join(cmd)} - Exit code: {result.returncode}")
            return result
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {' '.join(cmd)} - {e}")
            return None
        except FileNotFoundError:
            logger.warning(f"Command not found: {cmd[0]}")
            return None
    
    def keep_awake(self) -> bool:
        """
        Prevent system sleep while allowing screen to lock.
        
        Returns:
            True if successful
        """
        logger.info("Executing keep_awake action")
        
        if self.platform == 'Linux':
            # Try systemd-inhibit (preferred method)
            if self._run_command(['which', 'systemd-inhibit']):
                # Start background inhibitor
                if not self.dry_run:
                    try:
                        process = subprocess.Popen(
                            ['systemd-inhibit', '--what=sleep:idle', 
                             '--who=senthium-ai', '--why=Critical task running',
                             'sleep', 'infinity'],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL
                        )
                        self.sleep_inhibitor_pid = process.pid
                        logger.info(f"Started systemd-inhibit with PID {self.sleep_inhibitor_pid}")
                    except Exception as e:
                        logger.error(f"Failed to start systemd-inhibit: {e}")
                        return False
                else:
                    logger.info("[DRY-RUN] Would start systemd-inhibit")
                return True
            
            # Fallback: use xset to disable DPMS
            self._run_command(['xset', 's', 'off'])
            self._run_command(['xset', '-dpms'])
            return True
            
        elif self.platform == 'Darwin':  # macOS
            # Use caffeinate
            if not self.dry_run:
                try:
                    process = subprocess.Popen(
                        ['caffeinate', '-di'],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    self.sleep_inhibitor_pid = process.pid
                    logger.info(f"Started caffeinate with PID {self.sleep_inhibitor_pid}")
                except Exception as e:
                    logger.error(f"Failed to start caffeinate: {e}")
                    return False
            else:
                logger.info("[DRY-RUN] Would start caffeinate")
            return True
            
        elif self.platform == 'Windows':
            # Use powercfg to prevent sleep
            self._run_command(['powercfg', '/change', 'standby-timeout-ac', '0'])
            self._run_command(['powercfg', '/change', 'standby-timeout-dc', '0'])
            return True
        
        return False
    
    def delay_lock(self, minutes: int = 5) -> bool:
        """
        Delay automatic lock for specified minutes.
        
        Args:
            minutes: Minutes to delay lock
            
        Returns:
            True if successful
        """
        logger.info(f"Executing delay_lock action ({minutes} minutes)")
        
        if self.platform == 'Linux':
            # Set screen saver timeout using xset
            seconds = minutes * 60
            self._run_command(['xset', 's', str(seconds)])
            return True
            
        elif self.platform == 'Darwin':  # macOS
            # Use pmset to set displaysleep
            self._run_command(['pmset', 'displaysleep', str(minutes)])
            return True
            
        elif self.platform == 'Windows':
            # Set monitor timeout
            seconds = minutes * 60
            self._run_command(['powercfg', '/change', 'monitor-timeout-ac', str(minutes)])
            return True
        
        return False
    
    def full_lock(self) -> bool:
        """
        Lock the screen immediately.
        
        Returns:
            True if successful
        """
        logger.info("Executing full_lock action")
        
        if self.platform == 'Linux':
            # Try multiple methods (in order of preference)
            commands = [
                ['loginctl', 'lock-session'],
                ['gnome-screensaver-command', '--lock'],
                ['xdg-screensaver', 'lock'],
                ['dm-tool', 'lock']
            ]
            
            for cmd in commands:
                result = self._run_command(cmd)
                if result is None and self.dry_run:
                    return True  # In dry-run, first command succeeds
                if result and result.returncode == 0:
                    return True
            
            logger.warning("No lock method succeeded on Linux")
            return False
            
        elif self.platform == 'Darwin':  # macOS
            # Use CGSession to lock screen
            self._run_command(['/System/Library/CoreServices/Menu Extras/User.menu/Contents/Resources/CGSession', '-suspend'])
            return True
            
        elif self.platform == 'Windows':
            # Use rundll32 to lock workstation
            self._run_command(['rundll32.exe', 'user32.dll,LockWorkStation'])
            return True
        
        return False
    
    def screen_off(self) -> bool:
        """
        Turn off the screen/display.
        
        Returns:
            True if successful
        """
        logger.info("Executing screen_off action")
        
        if self.platform == 'Linux':
            # Force display off using xset
            self._run_command(['xset', 'dpms', 'force', 'off'])
            return True
            
        elif self.platform == 'Darwin':  # macOS
            # Use pmset to sleep display
            self._run_command(['pmset', 'displaysleepnow'])
            return True
            
        elif self.platform == 'Windows':
            # Turn off monitor using powercfg
            self._run_command(['powercfg', '/change', 'monitor-timeout-ac', '0'])
            return True
        
        return False
    
    def dim_screen(self, brightness: int = 30) -> bool:
        """
        Dim the screen to specified brightness level.
        
        Args:
            brightness: Brightness level (0-100)
            
        Returns:
            True if successful
        """
        logger.info(f"Executing dim_screen action (brightness={brightness})")
        
        if self.platform == 'Linux':
            # Try to set brightness using xrandr or brightnessctl
            # This is system-dependent and may not work on all systems
            self._run_command(['xrandr', '--output', 'eDP-1', '--brightness', str(brightness / 100)])
            self._run_command(['brightnessctl', 'set', f"{brightness}%"])
            return True
            
        elif self.platform == 'Darwin':  # macOS
            # Use brightness CLI tool if available
            self._run_command(['brightness', str(brightness / 100)])
            return True
            
        elif self.platform == 'Windows':
            # Windows brightness control is complex, log warning
            logger.warning("Brightness control not implemented for Windows")
            return False
        
        return False
    
    def restore(self) -> bool:
        """
        Restore normal power management settings.
        
        Returns:
            True if successful
        """
        logger.info("Executing restore action")
        
        # Kill sleep inhibitor if running
        if self.sleep_inhibitor_pid:
            if not self.dry_run:
                try:
                    import os
                    import signal
                    os.kill(self.sleep_inhibitor_pid, signal.SIGTERM)
                    logger.info(f"Killed sleep inhibitor process {self.sleep_inhibitor_pid}")
                except Exception as e:
                    logger.error(f"Failed to kill sleep inhibitor: {e}")
            else:
                logger.info(f"[DRY-RUN] Would kill process {self.sleep_inhibitor_pid}")
            self.sleep_inhibitor_pid = None
        
        if self.platform == 'Linux':
            # Re-enable DPMS and screensaver
            self._run_command(['xset', 's', 'on'])
            self._run_command(['xset', '+dpms'])
            return True
            
        elif self.platform == 'Darwin':  # macOS
            # Reset sleep settings to defaults
            self._run_command(['pmset', 'restoredefaults'])
            return True
            
        elif self.platform == 'Windows':
            # Restore default power plan
            self._run_command(['powercfg', '/setactive', 'SCHEME_BALANCED'])
            return True
        
        return False
    
    def execute_action(self, action: LockAction, **kwargs) -> bool:
        """
        Execute a lock action.
        
        Args:
            action: LockAction to execute
            **kwargs: Additional arguments for specific actions
            
        Returns:
            True if successful
        """
        action_map = {
            LockAction.KEEP_AWAKE: self.keep_awake,
            LockAction.DELAY_LOCK: lambda: self.delay_lock(kwargs.get('minutes', 5)),
            LockAction.FULL_LOCK: self.full_lock,
            LockAction.RESTORE: self.restore,
            LockAction.DIM_SCREEN: lambda: self.dim_screen(kwargs.get('brightness', 30)),
            LockAction.SCREEN_OFF: self.screen_off
        }
        
        handler = action_map.get(action)
        if handler:
            return handler()
        else:
            logger.error(f"Unknown action: {action}")
            return False
    
    def cleanup(self):
        """Clean up resources and restore normal state."""
        logger.info("Cleaning up lock controller")
        self.restore()


def main():
    """CLI interface for lock controller."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Senthium AI Lock Controller')
    parser.add_argument('action', choices=['keep-awake', 'delay-lock', 'full-lock', 
                                           'screen-off', 'dim', 'restore'],
                       help='Lock action to execute')
    parser.add_argument('--dry-run', '-d', action='store_true', help='Dry run mode')
    parser.add_argument('--minutes', '-m', type=int, default=5, help='Minutes for delay-lock')
    parser.add_argument('--brightness', '-b', type=int, default=30, help='Brightness for dim (0-100)')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    controller = LockController(dry_run=args.dry_run)
    
    # Map CLI action to LockAction
    action_map = {
        'keep-awake': LockAction.KEEP_AWAKE,
        'delay-lock': LockAction.DELAY_LOCK,
        'full-lock': LockAction.FULL_LOCK,
        'screen-off': LockAction.SCREEN_OFF,
        'dim': LockAction.DIM_SCREEN,
        'restore': LockAction.RESTORE
    }
    
    action = action_map[args.action]
    kwargs = {}
    
    if action == LockAction.DELAY_LOCK:
        kwargs['minutes'] = args.minutes
    elif action == LockAction.DIM_SCREEN:
        kwargs['brightness'] = args.brightness
    
    print(f"\n{'='*60}")
    print(f"Lock Controller - {args.action.upper().replace('-', ' ')}")
    print(f"{'='*60}")
    print(f"Platform: {platform.system()}")
    print(f"Dry Run: {args.dry_run}")
    if kwargs:
        print(f"Parameters: {kwargs}")
    print(f"{'='*60}\n")
    
    success = controller.execute_action(action, **kwargs)
    
    if success:
        print("✓ Action executed successfully")
        return 0
    else:
        print("✗ Action failed")
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
