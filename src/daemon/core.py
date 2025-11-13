"""
Senthium Daemon Core
Main control loop and state machine for intelligent stay-awake management

The heart of Senthium! Integrates system monitoring, rules evaluation,
and power management into a cohesive daemon service.
"""

import time
import signal
import logging
import sys
import os
from enum import Enum
from typing import Optional
from datetime import datetime

from pathlib import Path

from src.daemon.monitor import SystemMonitor
from src.daemon.power_manager import create_power_manager, PowerManagerBase
from src.rules.engine import RulesEngine
from src.rules.schema import ConfigValidationError
from src.utils.failsafe import FailsafeTimer
from src.utils.activity_log import ActivityLogger
from src.ipc import IPCServer, IPCMessage, IPCResponse


class DaemonState(Enum):
    """Daemon state machine states"""
    IDLE = "idle"                    # Not monitoring, sleeping allowed
    MONITORING = "monitoring"        # Watching metrics, no rules match yet
    ACTIVE = "active"                # Rules matched, stay-awake asserted
    SHUTDOWN = "shutdown"            # Graceful shutdown in progress
    
    # 🔒 Security states (v0.6.0+)
    AUTHORIZED = "authorized"        # Owner present, all good 🟢
    NO_FACE = "no_face"             # Nobody detected, grace timer started 👻
    UNAUTHORIZED = "unauthorized"    # Intruder detected, lock delay timer 🔴
    LOCKED = "locked"               # System locked, intruder blocked 🔒
    PAUSED = "paused"               # Monitoring paused by user ⏸️
    GRACE = "grace"                 # Grace period active (no face < 30s) ⏳


class SenthiumDaemon:
    """
    Main Senthium daemon service
    
    Orchestrates system monitoring, rules evaluation, and power management
    to intelligently prevent system sleep during critical tasks.
    """
    
    def __init__(self, config_path: str = 'config/config.yaml'):
        """
        Initialize Senthium daemon
        
        Args:
            config_path: Path to configuration YAML file
        """
        self.config_path = config_path
        self.logger = logging.getLogger(__name__)
        self.state = DaemonState.IDLE
        self._running = False
        self._shutdown_requested = False
        self._wrapper_lock_active = False  # Track CLI wrapper lock
        
        # Initialize components
        self.logger.info("=" * 70)
        self.logger.info("🌸 Senthium Daemon Initializing...")
        self.logger.info("=" * 70)
        
        try:
            # Load rules engine
            self.rules_engine = RulesEngine(Path(config_path))
            self.config = self.rules_engine.config['senthium']
            
            # Get configuration
            self.poll_interval = self.config.get('poll_interval', 5.0)
            max_awake_duration = self.config.get('max_awake_duration', 14400)
            
            # Initialize monitor
            self.monitor = SystemMonitor(poll_interval=self.poll_interval)
            
            # Initialize power manager
            self.power_manager = create_power_manager()
            
            # Initialize failsafe timer
            self.failsafe = FailsafeTimer(max_duration_seconds=max_awake_duration)
            
            # Initialize IPC server for CLI communication
            # Enable for tests via environment variable
            enable_ipc_env = os.getenv('SENTHIUM_ENABLE_IPC', 'NOT_SET')
            print(f"[DEBUG IPC INIT] SENTHIUM_ENABLE_IPC={enable_ipc_env}")
            
            enable_ipc = enable_ipc_env.lower() == 'true'
            
            self.logger.debug(f"[IPC] Environment: SENTHIUM_ENABLE_IPC={enable_ipc_env}")
            self.logger.debug(f"[IPC] Enabled: {enable_ipc}")
            
            if enable_ipc:
                try:
                    from src.ipc.channel import IPCServer
                    self.ipc_server = IPCServer()
                    self.logger.info("✅ IPC server enabled (test mode)")
                    print("[DEBUG IPC INIT] IPC server created successfully!")
                except ImportError as e:
                    self.ipc_server = None
                    self.logger.warning(f"⚠️  IPC module not available: {e}")
                    print(f"[DEBUG IPC INIT] ImportError: {e}")
            else:
                self.ipc_server = None
                self.logger.info("⚠️  IPC server disabled (daemon-only mode, use Streamlit UI for control)")
                print("[DEBUG IPC INIT] IPC disabled by config")
            
            # Initialize activity logger
            self.activity_logger = ActivityLogger()
            
            # 🔒 Initialize AI Security (v0.6.0)
            self.security_enabled = False
            self.security_manager = None
            self.security_check_interval = 2  # Check every N polls (default: every 10 seconds)
            
            security_config = self.config.get('security', {})
            if security_config.get('enabled', False):
                try:
                    from src.vision.security_manager import SecurityManager
                    self.security_manager = SecurityManager(config=security_config)
                    self.security_enabled = True
                    
                    # Calculate check interval (convert seconds to poll counts)
                    check_interval_seconds = security_config.get('check_interval_seconds', 10)
                    self.security_check_interval = max(1, int(check_interval_seconds / self.poll_interval))
                    
                    self.logger.info("✅ AI Security enabled (face recognition active)")
                    self.logger.info(f"   Check interval: every {check_interval_seconds}s ({self.security_check_interval} polls)")
                except Exception as e:
                    self.logger.error(f"⚠️  Failed to initialize AI security: {e}")
                    self.logger.warning("   Continuing without security features...")
                    self.security_enabled = False
            else:
                self.logger.info("ℹ️  AI Security disabled in config")
            
            # Statistics
            self.stats = {
                'started_at': datetime.now(),
                'poll_count': 0,
                'rules_matched': 0,
                'failsafe_triggers': 0,
                'active_sessions': 0,
            }
            
            self.logger.info("✅ Daemon initialized successfully")
            self.logger.info(f"   Config: {config_path}")
            self.logger.info(f"   Poll interval: {self.poll_interval}s")
            self.logger.info(f"   Max awake duration: {max_awake_duration}s ({max_awake_duration/3600:.1f}h)")
            self.logger.info(f"   Rules loaded: {len(self.config.get('rules', []))}")
            
        except ConfigValidationError as e:
            self.logger.error(f"❌ Configuration validation failed: {e}")
            raise
        except Exception as e:
            self.logger.error(f"❌ Daemon initialization failed: {e}")
            raise
    
    def _setup_signal_handlers(self):
        """Setup graceful shutdown signal handlers"""
        def signal_handler(signum, frame):
            signame = signal.Signals(signum).name
            self.logger.info(f"📨 Received signal {signame} - initiating graceful shutdown")
            self._shutdown_requested = True
        
        # Handle SIGINT (Ctrl+C) and SIGTERM
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        self.logger.debug("Signal handlers registered (SIGINT, SIGTERM)")
    
    def _transition_state(self, new_state: DaemonState):
        """
        Transition to new daemon state with logging
        
        Args:
            new_state: Target state to transition to
        """
        if self.state != new_state:
            old_state = self.state
            self.state = new_state
            self.logger.info(f"🔄 State transition: {old_state.value} → {new_state.value}")
    
    def _handle_ipc_message(self, message: IPCMessage) -> IPCResponse:
        """
        Handle incoming IPC message from CLI.
        
        Args:
            message: Incoming IPC message
            
        Returns:
            Response to send back to CLI
        """
        command = message.command
        self.logger.debug(f"📨 IPC command received: {command}")
        
        try:
            if command == "ACQUIRE_LOCK":
                # CLI wrapper requesting stay-awake lock
                self._wrapper_lock_active = True
                self.logger.info("🔒 Wrapper lock acquired (explicit mode)")
                return IPCResponse(
                    success=True,
                    message="Wrapper lock acquired - stay-awake guaranteed",
                    data={"lock_active": True}
                )
            
            elif command == "RELEASE_LOCK":
                # CLI wrapper releasing stay-awake lock
                self._wrapper_lock_active = False
                self.logger.info("🔓 Wrapper lock released")
                return IPCResponse(
                    success=True,
                    message="Wrapper lock released",
                    data={"lock_active": False}
                )
            
            elif command == "STATUS":
                # CLI requesting daemon status
                uptime = (datetime.now() - self.stats['started_at']).total_seconds()
                awake = self.power_manager.is_awake_asserted
                
                status_data = {
                    "state": self.state.value,
                    "uptime_seconds": uptime,
                    "poll_count": self.stats['poll_count'],
                    "rules_matched": self.stats['rules_matched'],
                    "active_sessions": self.stats['active_sessions'],
                    "failsafe_triggers": self.stats['failsafe_triggers'],
                    "awake": awake,
                    "wrapper_lock": self._wrapper_lock_active,
                }
                
                if awake:
                    status_data["awake_duration_seconds"] = self.failsafe.get_elapsed_seconds()
                    status_data["max_awake_duration"] = self.config.get('max_awake_duration', 14400)
                
                return IPCResponse(
                    success=True,
                    message="Status retrieved successfully",
                    data=status_data
                )
            
            elif command == "INFO":
                # CLI requesting detailed daemon information
                rules_info = []
                for rule in self.config.get('rules', []):
                    rules_info.append({
                        "name": rule.get('name', 'Unnamed'),
                        "type": rule.get('type', 'unknown'),
                    })
                
                info_data = {
                    "config_path": self.config_path,
                    "poll_interval": self.poll_interval,
                    "max_awake_duration": self.config.get('max_awake_duration', 14400),
                    "rules": rules_info,
                }
                
                return IPCResponse(
                    success=True,
                    message="Info retrieved successfully",
                    data=info_data
                )
            
            elif command == "METRICS":
                # Dashboard requesting real-time system metrics
                try:
                    metrics = self.monitor.get_metrics()
                    return IPCResponse(
                        success=True,
                        message="Metrics retrieved successfully",
                        data=metrics.to_dict()
                    )
                except Exception as e:
                    return IPCResponse(
                        success=False,
                        message=f"Failed to get metrics: {str(e)}"
                    )
            
            elif command == "RELOAD_CONFIG":
                # CLI requesting config reload
                try:
                    old_rules_count = len(self.config.get('rules', []))
                    self.rules_engine = RulesEngine(Path(self.config_path))
                    self.config = self.rules_engine.config['senthium']
                    new_rules_count = len(self.config.get('rules', []))
                    
                    self.logger.info(f"🔄 Configuration reloaded ({new_rules_count} rules)")
                    
                    return IPCResponse(
                        success=True,
                        message=f"Configuration reloaded successfully",
                        data={
                            "rules_count": new_rules_count,
                            "old_rules_count": old_rules_count
                        }
                    )
                    
                except Exception as e:
                    self.logger.error(f"Failed to reload config: {e}")
                    return IPCResponse(
                        success=False,
                        message=f"Failed to reload config: {e}"
                    )
            
            else:
                return IPCResponse(
                    success=False,
                    message=f"Unknown command: {command}"
                )
                
        except Exception as e:
            self.logger.error(f"Error handling IPC command '{command}': {e}")
            return IPCResponse(
                success=False,
                message=f"Internal error: {e}"
            )
    
    def _poll_ipc(self):
        """Poll for incoming IPC messages"""
        if self.ipc_server is None:
            return
        
        try:
            result = self.ipc_server.poll()
            if result:
                message, client_context = result
                response = self._handle_ipc_command(message)
                self.ipc_server.send_response(response, client_context)
        except Exception as e:
            self.logger.error(f"IPC poll error: {e}")
    
    def _handle_ipc_command(self, message):
        """Handle incoming IPC command"""
        from src.ipc.channel import IPCResponse
        
        command = message.command.upper()
        
        if command == "STATUS":
            return IPCResponse(
                success=True,
                data={
                    "state": self.state.value,
                    "uptime": (datetime.now() - self._start_time).total_seconds() if hasattr(self, '_start_time') else 0,
                    "wrapper_lock_active": self._wrapper_lock_active,
                    "failsafe_active": self.failsafe.is_active() if self.failsafe else False
                }
            )
        
        elif command == "INFO":
            return IPCResponse(
                success=True,
                data={
                    "config_path": str(self.config_path),
                    "rules": [r.to_dict() for r in self.rules_engine.rules],
                    "poll_interval": self.poll_interval,
                    "max_awake": self.max_awake_duration
                }
            )
        
        elif command == "ACQUIRE_LOCK":
            self._wrapper_lock_active = True
            self._wrapper_lock_reason = message.data.get("reason", "CLI command")
            return IPCResponse(
                success=True,
                data={"lock_active": True}
            )
        
        elif command == "RELEASE_LOCK":
            self._wrapper_lock_active = False
            self._wrapper_lock_reason = None
            return IPCResponse(
                success=True,
                data={"lock_active": False}
            )
        
        elif command == "RELOAD_CONFIG":
            try:
                # Reload config (simplified - just reload rules)
                from pathlib import Path
                self.rules_engine = RulesEngine(Path(self.config_path))
                return IPCResponse(
                    success=True,
                    message="Config reloaded successfully",
                    data={"rules_count": len(self.rules_engine.rules)}
                )
            except Exception as e:
                return IPCResponse(
                    success=False,
                    message=f"Failed to reload config: {str(e)}"
                )
        
        else:
            return IPCResponse(
                success=False,
                message=f"Unknown command: {command}"
            )
    
    def _handle_monitoring_state(self, metrics):
        """
        Handle MONITORING state logic
        
        Args:
            metrics: Current system metrics
            
        Returns:
            True if should transition to ACTIVE, False otherwise
        """
        # Check wrapper lock first (explicit mode takes priority)
        if self._wrapper_lock_active:
            self.logger.debug("💼 Wrapper lock active - staying awake (explicit mode)")
            
            # Start activity session if not already started
            if self.activity_logger.current_session is None:
                self.activity_logger.start_session(
                    reason='wrapper_lock',
                    process_name='CLI wrapper command',
                    metrics={
                        'cpu': metrics.cpu_percent,
                        'disk_read': metrics.disk_read_mbps,
                        'disk_write': metrics.disk_write_mbps
                    }
                )
            
            return True
        
        # Evaluate rules (implicit mode)
        should_stay_awake = self.rules_engine.evaluate(metrics)
        
        if should_stay_awake:
            self.stats['rules_matched'] += 1
            self.logger.info("🔥 Rules matched - transitioning to ACTIVE state")
            
            # Start activity logging
            matched_rules = [r.rule_name for r in self.rules_engine.get_last_matches()]
            rule_name = matched_rules[0] if matched_rules else 'unknown'
            self.activity_logger.start_session(
                reason='rule_match',
                rule_name=rule_name,
                metrics={
                    'cpu': metrics.cpu_percent,
                    'disk_read': metrics.disk_read_mbps,
                    'disk_write': metrics.disk_write_mbps,
                    'network_down': metrics.net_recv_mbps,
                    'network_up': metrics.net_sent_mbps
                }
            )
            
            return True
        
        return False
    
    def _handle_active_state(self, metrics):
        """
        Handle ACTIVE state logic
        
        Args:
            metrics: Current system metrics
            
        Returns:
            True if should stay active, False if should return to MONITORING
        """
        # Check failsafe first
        if self.failsafe.check_exceeded():
            self.logger.critical("🚨 FAILSAFE TRIGGERED - Forcing release of stay-awake")
            self.stats['failsafe_triggers'] += 1
            # Force release wrapper lock on failsafe
            self._wrapper_lock_active = False
            
            # End activity session
            if self.activity_logger.current_session:
                self.activity_logger.end_session()
            
            return False
        
        # Check wrapper lock (explicit mode)
        if self._wrapper_lock_active:
            # Wrapper lock active - stay awake regardless of rules
            if self.stats['poll_count'] % 12 == 0:  # Log every ~1 minute
                elapsed = self.failsafe.get_elapsed_seconds()
                remaining = self.failsafe.get_remaining_seconds()
                self.logger.debug(
                    f"💼 Wrapper lock active - Awake for {self.failsafe._format_duration(elapsed)}, "
                    f"{self.failsafe._format_duration(remaining)} remaining"
                )
            return True
        
        # Evaluate rules (implicit mode)
        should_stay_awake = self.rules_engine.evaluate(metrics)
        
        if should_stay_awake:
            # Still active - log progress if needed
            elapsed = self.failsafe.get_elapsed_seconds()
            remaining = self.failsafe.get_remaining_seconds()
            
            if self.stats['poll_count'] % 12 == 0:  # Log every ~1 minute
                self.logger.debug(
                    f"💚 Still active - Awake for {self.failsafe._format_duration(elapsed)}, "
                    f"{self.failsafe._format_duration(remaining)} remaining"
                )
            
            return True
        else:
            self.logger.info("😴 Rules no longer match - returning to MONITORING")
            
            # End activity session
            if self.activity_logger.current_session:
                self.activity_logger.end_session()
            
            return False
    
    def run(self):
        """
        Main daemon loop
        
        Continuously monitors system state and manages power assertions
        based on rule evaluation.
        """
        print("[DEBUG] Setting up signal handlers...")
        self._setup_signal_handlers()
        self._running = True
        print("[DEBUG] Transitioning to MONITORING state...")
        self._transition_state(DaemonState.MONITORING)
        
        # Start IPC server if enabled
        if self.ipc_server:
            print("[DEBUG] Starting IPC server...")
            try:
                self.ipc_server.start()
                self.logger.info("✅ IPC server started")
                print("[DEBUG] IPC server started successfully!")
            except Exception as e:
                self.logger.error(f"Failed to start IPC server: {e}")
                print(f"[DEBUG] IPC server start failed: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("[DEBUG] self.ipc_server is None - not starting")
        
        self.logger.info("=" * 70)
        self.logger.info("🚀 Senthium Daemon Started!")
        self.logger.info("=" * 70)
        self.logger.info("Monitoring system for critical tasks...")
        self.logger.info(f"Poll interval: {self.poll_interval}s")
        self.logger.info("Press Ctrl+C to stop (may take up to 1 second to respond)")
        
        print("[DEBUG] Entering main loop...")
        print(f"[DEBUG] _running={self._running}, _shutdown_requested={self._shutdown_requested}")
        print("[DEBUG] Daemon is now monitoring... (Ctrl+C to stop)")
        try:
            while self._running and not self._shutdown_requested:
                print(f"[DEBUG] Loop iteration {self.stats['poll_count'] + 1}")
                self.stats['poll_count'] += 1
                
                print(f"[DEBUG] About to poll IPC...")
                # Poll IPC for CLI commands (non-blocking)
                self._poll_ipc()
                
                print(f"[DEBUG] About to gather metrics...")
                # Gather system metrics
                try:
                    metrics = self.monitor.get_current_state()
                    print(f"[DEBUG] Got metrics: CPU={metrics.cpu_percent}%")
                except Exception as e:
                    self.logger.error(f"Failed to gather metrics: {e}")
                    print(f"[DEBUG] Metrics failed: {e}")
                    time.sleep(self.poll_interval)
                    continue
                
                logger.debug(f"About to check security (enabled={self.security_enabled})...")
                # 🔒 AI SECURITY CHECK (v0.6.0)
                # Perform face recognition security check if enabled
                if self.security_enabled and self.security_manager is not None:
                    try:
                        # Only check every N polls (security_check_interval)
                        logger.debug(f"poll_count={self.stats['poll_count']}, interval={self.security_check_interval}, modulo={self.stats['poll_count'] % self.security_check_interval}")
                        if self.stats['poll_count'] % self.security_check_interval == 0:
                            logger.debug(f"🎯 Running security check now...")
                            security_result = self.security_manager.perform_security_check()
                            logger.debug(f"Security result: {security_result}")
                            
                            # Log security events (handle all response types)
                            if security_result:
                                status = security_result.get('status', 'success')
                                
                                if status == 'error':
                                    self.logger.error(f"❌ Security check error: {security_result.get('error', 'Unknown')}")
                                elif status == 'no_faces':
                                    self.logger.debug("👻 No faces detected in security check")
                                elif security_result.get('unknown_faces_count', 0) > 0:
                                    self.logger.warning(
                                        f"⚠️ SECURITY ALERT! {security_result['unknown_faces_count']} "
                                        f"unauthorized face(s) detected!"
                                    )
                                elif security_result.get('authorized_faces_count', 0) > 0:
                                    self.logger.info(
                                        f"✅ Authorized user recognized: {security_result.get('detected_faces_count', 0)} face(s)"
                                    )
                    except Exception as e:
                        self.logger.error(f"Security check failed: {e}")
                        import traceback
                        traceback.print_exc()
                
                # State machine logic
                if self.state == DaemonState.MONITORING:
                    should_activate = self._handle_monitoring_state(metrics)
                    
                    if should_activate:
                        # Transition to ACTIVE
                        self._transition_state(DaemonState.ACTIVE)
                        self.stats['active_sessions'] += 1
                        
                        # Assert stay-awake
                        success = self.power_manager.assert_awake()
                        if success:
                            self.failsafe.start()
                        else:
                            self.logger.error("Failed to assert stay-awake - staying in MONITORING")
                            self._transition_state(DaemonState.MONITORING)
                
                elif self.state == DaemonState.ACTIVE:
                    should_stay_active = self._handle_active_state(metrics)
                    
                    if not should_stay_active:
                        # Transition back to MONITORING
                        self._transition_state(DaemonState.MONITORING)
                        
                        # Release stay-awake
                        self.power_manager.release_awake()
                        self.failsafe.reset()
                
                # Sleep until next poll (use smaller intervals for better Ctrl+C responsiveness on Windows)
                remaining_sleep = self.poll_interval
                while remaining_sleep > 0 and not self._shutdown_requested:
                    sleep_chunk = min(0.5, remaining_sleep)  # Sleep in 0.5s chunks
                    time.sleep(sleep_chunk)
                    remaining_sleep -= sleep_chunk
        
        except KeyboardInterrupt:
            self.logger.info("⌨️  Keyboard interrupt (Ctrl+C) detected")
            self._shutdown_requested = True
        except Exception as e:
            self.logger.exception(f"💥 Fatal error in main loop: {e}")
            print(f"[DEBUG] Exception type: {type(e).__name__}")
            print(f"[DEBUG] Exception: {e}")
            import traceback
            traceback.print_exc()
            raise
        finally:
            print("[DEBUG] Exited main loop")
            print(f"[DEBUG] _running={self._running}, _shutdown_requested={self._shutdown_requested}")
            self._shutdown()
    
    def _shutdown(self):
        """Graceful shutdown procedure"""
        self.logger.info("=" * 70)
        self.logger.info("🌙 Senthium Daemon Shutting Down...")
        self.logger.info("=" * 70)
        
        self._transition_state(DaemonState.SHUTDOWN)
        
        # Stop IPC server
        if self.ipc_server:
            self.logger.info("Stopping IPC server...")
            self.ipc_server.stop()
        
        # Release any active stay-awake assertion
        if self.power_manager.is_awake_asserted:
            self.logger.info("Releasing stay-awake assertion...")
            self.power_manager.release_awake()
        
        # Reset failsafe
        if self.failsafe.is_active():
            self.failsafe.reset()
        
        # Log final statistics
        uptime = (datetime.now() - self.stats['started_at']).total_seconds()
        self.logger.info("📊 Session Statistics:")
        self.logger.info(f"   Uptime: {self.failsafe._format_duration(uptime)}")
        self.logger.info(f"   Total polls: {self.stats['poll_count']}")
        self.logger.info(f"   Rules matched: {self.stats['rules_matched']}")
        self.logger.info(f"   Active sessions: {self.stats['active_sessions']}")
        self.logger.info(f"   Failsafe triggers: {self.stats['failsafe_triggers']}")
        
        self.logger.info("✅ Senthium daemon stopped cleanly")
        self._running = False
    
    def stop(self):
        """Request daemon to stop (can be called externally)"""
        import traceback
        self.logger.info("Stop requested externally")
        self.logger.debug(f"Stop called from:\n{''.join(traceback.format_stack())}")
        self._shutdown_requested = True


# Example usage / testing
if __name__ == '__main__':
    from src.utils.logger import setup_logger
    from src.utils.pid import PIDFile
    import argparse
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description='Senthium Daemon - Intelligent Stay-Awake Management'
    )
    parser.add_argument(
        '--config',
        default='config/config.yaml',
        help='Path to configuration file (default: config/config.yaml)'
    )
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level (default: INFO)'
    )
    
    args = parser.parse_args()
    
    # Setup logging - configure BOTH root logger and specific 'senthium' logger
    # Root logger configuration ensures ALL child modules (security_manager, detector, recognizer) inherit it
    root_logger = setup_logger('', level=args.log_level)  # '' = root logger
    logger = setup_logger('senthium', level=args.log_level)
    
    logger.debug(f"Logging configured: level={args.log_level}, root logger and 'senthium' logger initialized")
    
    # Use PID file to prevent multiple instances
    pid_file = PIDFile()
    
    try:
        # Create PID file (will raise if already running)
        with pid_file:
            # Create and run daemon
            daemon = SenthiumDaemon(config_path=args.config)
            daemon.run()
        
    except RuntimeError as e:
        # Already running or PID file issue
        logger.error(str(e))
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1)
