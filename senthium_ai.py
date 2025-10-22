#!/usr/bin/env python3
"""
Senthium AI - Main Application
Intelligent task-aware lock system with ANN and Fuzzy Logic
"""
import argparse
import logging
import sys
import time
import yaml
from pathlib import Path
from senthium_ai import LockStateManager

# Configure logging
def setup_logging(log_level: str, log_file: str = None):
    """Setup logging configuration."""
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    handlers = [logging.StreamHandler(sys.stdout)]
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )


def load_config(config_path: str) -> dict:
    """Load configuration from YAML file."""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logging.warning(f"Config file {config_path} not found, using defaults")
        return {}
    except Exception as e:
        logging.error(f"Error loading config: {e}")
        return {}


def state_change_handler(state: str, info: dict):
    """Handle lock state changes."""
    print(f"\n{'='*60}")
    print(f"Lock State Changed: {state.upper().replace('_', ' ')}")
    print(f"{'='*60}")
    print(f"Task Level: {info['task_level']}")
    print(f"Task Criticality: {info['task_criticality']:.1f}%")
    print(f"System Load: {info['system_load']:.1f}%")
    print(f"Presence Confidence: {info['presence_confidence']:.1f}%")
    print(f"Critical Processes: {info['critical_process_count']}")
    print(f"Active Processes: {info['active_process_count']}")
    print(f"{'='*60}\n")


def main():
    """Main application loop."""
    parser = argparse.ArgumentParser(
        description='Senthium AI - Intelligent Task-Aware Lock System'
    )
    parser.add_argument(
        '--config', '-c',
        default='config.yaml',
        help='Path to configuration file (default: config.yaml)'
    )
    parser.add_argument(
        '--dry-run', '-d',
        action='store_true',
        help='Run without actually applying lock states'
    )
    parser.add_argument(
        '--interval', '-i',
        type=int,
        help='Override update interval (seconds)'
    )
    parser.add_argument(
        '--enable-face-detection', '-f',
        action='store_true',
        help='Enable face detection for presence verification'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose (DEBUG) logging'
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Override with command line arguments
    if args.dry_run:
        config['apply_lock_state'] = False
    if args.interval:
        config['update_interval'] = args.interval
    if args.enable_face_detection:
        config['enable_face_detection'] = True
    if args.verbose:
        config['log_level'] = 'DEBUG'
    
    # Setup logging
    setup_logging(
        config.get('log_level', 'INFO'),
        config.get('log_file')
    )
    
    logger = logging.getLogger(__name__)
    logger.info("Starting Senthium AI...")
    logger.info(f"Configuration: {args.config}")
    
    if not config.get('apply_lock_state', True):
        logger.warning("Running in DRY-RUN mode - lock states will not be applied")
    
    # Initialize lock manager
    try:
        manager = LockStateManager(config)
        manager.set_state_change_callback(state_change_handler)
        
        logger.info("Lock manager initialized successfully")
        
        update_interval = config.get('update_interval', 10)
        logger.info(f"Update interval: {update_interval} seconds")
        
        print("\n" + "="*60)
        print("Senthium AI - Intelligent Lock System Active")
        print("="*60)
        print("Monitoring system processes and user presence...")
        print("Press Ctrl+C to stop\n")
        
        # Main loop
        while True:
            try:
                # Evaluate lock state
                state_info = manager.evaluate_lock_state()
                
                # Log current state
                logger.debug(f"Current state: {state_info['lock_state']}, "
                           f"Task: {state_info['task_level']}, "
                           f"Load: {state_info['system_load']:.1f}%")
                
                # Apply lock state if enabled
                if config.get('apply_lock_state', True):
                    manager.apply_lock_state(state_info['lock_state'])
                
                # Display status update
                print(f"[{time.strftime('%H:%M:%S')}] "
                      f"State: {state_info['lock_state'].replace('_', ' ').title():12s} | "
                      f"Task: {state_info['task_level']:8s} | "
                      f"Load: {state_info['system_load']:5.1f}% | "
                      f"Presence: {state_info['presence_confidence']:5.1f}% | "
                      f"Critical: {state_info['critical_process_count']:2d} | "
                      f"Active: {state_info['active_process_count']:3d}",
                      end='\r')
                
                # Wait for next update
                time.sleep(update_interval)
                
            except KeyboardInterrupt:
                print("\n\nShutting down gracefully...")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}", exc_info=True)
                time.sleep(5)  # Brief pause before retrying
        
    except Exception as e:
        logger.error(f"Failed to initialize: {e}", exc_info=True)
        return 1
    finally:
        if 'manager' in locals():
            manager.cleanup()
        logger.info("Senthium AI stopped")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
