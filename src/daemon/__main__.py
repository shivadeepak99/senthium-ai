"""
Entry point for running daemon control module via `python -m src.daemon.control`
"""

import argparse
import sys
from src.daemon.control import start_daemon, stop_daemon, restart_daemon, daemon_status


def main():
    """Main entry point for daemon control CLI."""
    parser = argparse.ArgumentParser(
        description="Senthium Daemon Control",
        prog="python -m src.daemon.control"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Start command
    start_parser = subparsers.add_parser('start', help='Start the daemon')
    start_parser.add_argument('--config', default='config/config.yaml', help='Path to config file')
    start_parser.add_argument('--log-level', default='INFO', help='Logging level')
    start_parser.add_argument('--foreground', action='store_true', help='Run in foreground')
    
    # Stop command
    subparsers.add_parser('stop', help='Stop the daemon')
    
    # Restart command
    restart_parser = subparsers.add_parser('restart', help='Restart the daemon')
    restart_parser.add_argument('--config', default='config/config.yaml', help='Path to config file')
    restart_parser.add_argument('--log-level', default='INFO', help='Logging level')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Check daemon status')
    status_parser.add_argument('--verbose', '-v', action='store_true', help='Show detailed status')
    
    args = parser.parse_args()
    
    # Execute command
    if args.command == 'start':
        sys.exit(start_daemon(
            config_path=args.config,
            log_level=args.log_level,
            foreground=args.foreground
        ))
    
    elif args.command == 'stop':
        sys.exit(stop_daemon())
    
    elif args.command == 'restart':
        sys.exit(restart_daemon(
            config_path=args.config,
            log_level=args.log_level
        ))
    
    elif args.command == 'status':
        sys.exit(daemon_status(verbose=args.verbose))
    
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
