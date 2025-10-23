"""
Main CLI entry point for Senthium.

This module serves as the primary command-line interface,
providing both daemon management and wrapper functionality.
"""

import sys
import argparse
import logging

# Setup basic logging for CLI
logging.basicConfig(
    level=logging.WARNING,
    format="%(message)s"
)


def main() -> int:
    """Main entry point for senthium command"""
    parser = argparse.ArgumentParser(
        prog="senthium",
        description="Senthium - Intelligent Lock & Sleep Manager",
        epilog="Examples:\n"
               "  senthium start                          # Start daemon\n"
               "  senthium stop                           # Stop daemon\n"
               "  senthium --stay-awake 'npm run build'  # Run command with stay-awake\n"
               "  senthium --status                       # Show daemon status\n",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Daemon management commands (subparser)
    subparsers = parser.add_subparsers(dest='command', help='Daemon management commands')
    
    # Start command
    start_parser = subparsers.add_parser('start', help='Start daemon in background')
    start_parser.add_argument(
        '--config',
        default='config/config.yaml',
        help='Path to configuration file (default: config/config.yaml)'
    )
    start_parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level (default: INFO)'
    )
    start_parser.add_argument(
        '--foreground',
        action='store_true',
        help='Run in foreground (don\'t detach)'
    )
    
    # Stop command
    stop_parser = subparsers.add_parser('stop', help='Stop running daemon')
    stop_parser.add_argument(
        '--force',
        action='store_true',
        help='Force kill daemon (SIGKILL)'
    )
    stop_parser.add_argument(
        '--timeout',
        type=int,
        default=10,
        help='Timeout for graceful shutdown (default: 10s)'
    )
    
    # Restart command
    restart_parser = subparsers.add_parser('restart', help='Restart daemon')
    restart_parser.add_argument(
        '--config',
        default='config/config.yaml',
        help='Path to configuration file'
    )
    restart_parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level'
    )
    
    # Status command (can also be used as --status flag for backward compat)
    status_parser = subparsers.add_parser('status', help='Check daemon status')
    status_parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed status'
    )
    
    # Wrapper mode arguments (original functionality)
    parser.add_argument(
        '--stay-awake',
        metavar='COMMAND',
        help='Run command with stay-awake lock (explicit mode)'
    )
    
    parser.add_argument(
        '--status',
        action='store_true',
        dest='status_flag',
        help='Show daemon status (shortcut for "senthium status")'
    )
    
    parser.add_argument(
        '--info',
        action='store_true',
        help='Show detailed daemon information'
    )
    
    parser.add_argument(
        '--reload',
        action='store_true',
        help='Reload daemon configuration'
    )
    
    parser.add_argument(
        '--log-level',
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Set logging level (default: INFO)',
        dest='wrapper_log_level'
    )
    
    args = parser.parse_args()
    
    # Route to appropriate handler
    try:
        # Daemon management commands
        if args.command == 'start':
            from daemon.control import start_daemon
            return start_daemon(
                config_path=args.config,
                log_level=args.log_level,
                foreground=args.foreground
            )
        
        elif args.command == 'stop':
            from daemon.control import stop_daemon
            return stop_daemon(force=args.force, timeout=args.timeout)
        
        elif args.command == 'restart':
            from daemon.control import restart_daemon
            return restart_daemon(
                config_path=args.config,
                log_level=args.log_level
            )
        
        elif args.command == 'status':
            from daemon.control import daemon_status
            return daemon_status(verbose=args.verbose)
        
        # Wrapper mode (explicit stay-awake)
        elif args.stay_awake:
            from cli.wrapper import cmd_stay_awake, setup_cli_logging
            setup_cli_logging(args.wrapper_log_level)
            return cmd_stay_awake(args.stay_awake)
        
        # Status flag (backward compat)
        elif args.status_flag:
            from cli.wrapper import cmd_status, setup_cli_logging
            setup_cli_logging(args.wrapper_log_level)
            return cmd_status()
        
        # Info command
        elif args.info:
            from cli.wrapper import cmd_info, setup_cli_logging
            setup_cli_logging(args.wrapper_log_level)
            return cmd_info()
        
        # Reload command
        elif args.reload:
            from cli.wrapper import cmd_reload, setup_cli_logging
            setup_cli_logging(args.wrapper_log_level)
            return cmd_reload()
        
        else:
            # No command specified - show help
            parser.print_help()
            return 0
        
    except KeyboardInterrupt:
        print("\n[WARN] Interrupted by user")
        return 130
    except Exception as e:
        logging.error(f"Error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
