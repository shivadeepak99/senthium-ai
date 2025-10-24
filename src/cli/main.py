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


def handle_service_command(args) -> int:
    """Handle service-related commands"""
    action = getattr(args, 'service_action', None)
    
    if not action:
        print("[ERROR] No service action specified")
        print("        Use: senthium service {install|uninstall|start|stop|restart|status}")
        return 1
    
    # Platform detection
    if sys.platform.startswith('win'):
        # Windows Service
        try:
            from service.windows_service import install_service, uninstall_service
            import win32serviceutil  # type: ignore
            
            if action == 'install':
                success = install_service()
                return 0 if success else 1
            
            elif action == 'uninstall':
                success = uninstall_service()
                return 0 if success else 1
            
            elif action == 'start':
                print("[*] Starting Senthium service...")
                win32serviceutil.StartService("Senthium")
                print("[OK] Service started")
                return 0
            
            elif action == 'stop':
                print("[*] Stopping Senthium service...")
                win32serviceutil.StopService("Senthium")
                print("[OK] Service stopped")
                return 0
            
            elif action == 'restart':
                print("[*] Restarting Senthium service...")
                win32serviceutil.RestartService("Senthium")
                print("[OK] Service restarted")
                return 0
            
            elif action == 'status':
                try:
                    status = win32serviceutil.QueryServiceStatus("Senthium")
                    state_map = {
                        1: "STOPPED",
                        2: "START_PENDING",
                        3: "STOP_PENDING",
                        4: "RUNNING",
                        5: "CONTINUE_PENDING",
                        6: "PAUSE_PENDING",
                        7: "PAUSED"
                    }
                    state = state_map.get(status[1], "UNKNOWN")
                    print(f"Service Status: {state}")
                    return 0
                except Exception as e:
                    print(f"[ERROR] Could not query service: {e}")
                    print("        Service may not be installed")
                    return 1
            
            else:
                print(f"[ERROR] Unknown service action: {action}")
                return 1
            
        except ImportError:
            print("[ERROR] pywin32 is required for Windows Service management")
            print("        Install with: pip install pywin32")
            return 1
        except Exception as e:
            print(f"[ERROR] Service operation failed: {e}")
            return 1
    
    elif sys.platform.startswith('linux'):
        # Linux systemd
        try:
            from service.systemd_generator import (
                generate_systemd_service,
                install_systemd_service,
                uninstall_systemd_service
            )
            import subprocess
            
            if action == 'install':
                print("[*] Installing Senthium as systemd service...")
                service_content = generate_systemd_service(
                    user=getattr(args, 'user', None)
                )
                success = install_systemd_service(service_content, enable=True)
                return 0 if success else 1
            
            elif action == 'uninstall':
                success = uninstall_systemd_service()
                return 0 if success else 1
            
            elif action == 'start':
                print("[*] Starting Senthium service...")
                subprocess.run(['sudo', 'systemctl', 'start', 'senthium'], check=True)
                print("[OK] Service started")
                return 0
            
            elif action == 'stop':
                print("[*] Stopping Senthium service...")
                subprocess.run(['sudo', 'systemctl', 'stop', 'senthium'], check=True)
                print("[OK] Service stopped")
                return 0
            
            elif action == 'restart':
                print("[*] Restarting Senthium service...")
                subprocess.run(['sudo', 'systemctl', 'restart', 'senthium'], check=True)
                print("[OK] Service restarted")
                return 0
            
            elif action == 'status':
                subprocess.run(['systemctl', 'status', 'senthium'])
                return 0
            
            else:
                print(f"[ERROR] Unknown service action: {action}")
                return 1
                
        except Exception as e:
            print(f"[ERROR] Service operation failed: {e}")
            return 1
    
    elif sys.platform == 'darwin':
        # macOS launchd
        print("[*] macOS launchd service management")
        print("    (Implementation coming soon)")
        return 1
    
    else:
        print(f"[ERROR] Unsupported platform: {sys.platform}")
        return 1


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
    
    # Service command (Windows Service / systemd / launchd)
    service_parser = subparsers.add_parser('service', help='Manage system service (Windows/Linux/macOS)')
    service_subparsers = service_parser.add_subparsers(dest='service_action', help='Service actions')
    
    # Service install
    service_install = service_subparsers.add_parser('install', help='Install as system service')
    service_install.add_argument(
        '--user',
        help='User to run service as (Linux/macOS only)'
    )
    
    # Service uninstall
    service_subparsers.add_parser('uninstall', help='Uninstall system service')
    
    # Service start
    service_subparsers.add_parser('start', help='Start system service')
    
    # Service stop
    service_subparsers.add_parser('stop', help='Stop system service')
    
    # Service restart
    service_subparsers.add_parser('restart', help='Restart system service')
    
    # Service status
    service_subparsers.add_parser('status', help='Check service status')
    
    # Activity command
    activity_parser = subparsers.add_parser('activity', help='View activity logs and statistics')
    activity_parser.add_argument(
        '--days',
        type=int,
        default=1,
        help='Number of days to show (default: 1)'
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
        
        # Service commands
        elif args.command == 'service':
            return handle_service_command(args)
        
        # Activity command
        elif args.command == 'activity':
            from utils.activity_log import cmd_activity
            return cmd_activity(args)
        
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
