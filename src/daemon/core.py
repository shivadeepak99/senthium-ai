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
from enum import Enum
from typing import Optional
from datetime import datetime

from pathlib import Path

from daemon.monitor import SystemMonitor
from daemon.power_manager import create_power_manager, PowerManagerBase
from rules.engine import RulesEngine
from rules.schema import ConfigValidationError
from utils.failsafe import FailsafeTimer


class DaemonState(Enum):
    """Daemon state machine states"""
    IDLE = "idle"           # Not monitoring, sleeping allowed
    MONITORING = "monitoring"  # Watching metrics, no rules match yet
    ACTIVE = "active"       # Rules matched, stay-awake asserted
    SHUTDOWN = "shutdown"   # Graceful shutdown in progress


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
    
    def _handle_monitoring_state(self, metrics):
        """
        Handle MONITORING state logic
        
        Args:
            metrics: Current system metrics
            
        Returns:
            True if should transition to ACTIVE, False otherwise
        """
        # Evaluate rules (returns bool)
        should_stay_awake = self.rules_engine.evaluate(metrics)
        
        if should_stay_awake:
            self.stats['rules_matched'] += 1
            self.logger.info("🔥 Rules matched - transitioning to ACTIVE state")
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
            return False
        
        # Evaluate rules (returns bool)
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
            return False
    
    def run(self):
        """
        Main daemon loop
        
        Continuously monitors system state and manages power assertions
        based on rule evaluation.
        """
        self._setup_signal_handlers()
        self._running = True
        self._transition_state(DaemonState.MONITORING)
        
        self.logger.info("=" * 70)
        self.logger.info("🚀 Senthium Daemon Started!")
        self.logger.info("=" * 70)
        self.logger.info("Monitoring system for critical tasks...")
        self.logger.info("Press Ctrl+C to stop")
        
        try:
            while self._running and not self._shutdown_requested:
                self.stats['poll_count'] += 1
                
                # Gather system metrics
                try:
                    metrics = self.monitor.get_current_state()
                except Exception as e:
                    self.logger.error(f"Failed to gather metrics: {e}")
                    time.sleep(self.poll_interval)
                    continue
                
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
                
                # Sleep until next poll
                time.sleep(self.poll_interval)
        
        except Exception as e:
            self.logger.exception(f"💥 Fatal error in main loop: {e}")
            raise
        
        finally:
            self._shutdown()
    
    def _shutdown(self):
        """Graceful shutdown procedure"""
        self.logger.info("=" * 70)
        self.logger.info("🌙 Senthium Daemon Shutting Down...")
        self.logger.info("=" * 70)
        
        self._transition_state(DaemonState.SHUTDOWN)
        
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
        self.logger.info("Stop requested externally")
        self._shutdown_requested = True


# Example usage / testing
if __name__ == '__main__':
    from utils.logger import setup_logger
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
    
    # Setup logging
    logger = setup_logger('senthium', level=args.log_level)
    
    try:
        # Create and run daemon
        daemon = SenthiumDaemon(config_path=args.config)
        daemon.run()
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1)
