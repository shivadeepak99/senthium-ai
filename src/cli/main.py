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
    
    # Web dashboard command
    web_parser = subparsers.add_parser('web', help='Start web dashboard')
    web_parser.add_argument(
        '--host',
        default='127.0.0.1',
        help='Host to bind to (default: 127.0.0.1)'
    )
    web_parser.add_argument(
        '--port',
        type=int,
        default=5000,
        help='Port to bind to (default: 5000)'
    )
    web_parser.add_argument(
        '--debug',
        action='store_true',
        help='Run in debug mode'
    )
    
    # Security enrollment command
    enroll_parser = subparsers.add_parser('enroll', help='Enroll authorized face for security monitoring')
    enroll_parser.add_argument(
        '--name',
        default='Owner',
        help='Name for this authorized user (default: Owner)'
    )
    enroll_parser.add_argument(
        '--image',
        help='Path to image file (or use camera if not specified)'
    )
    
    # Security management command
    security_parser = subparsers.add_parser('security', help='Security system management')
    security_subparsers = security_parser.add_subparsers(dest='security_action', help='Security actions')
    
    # Security stats
    security_subparsers.add_parser('stats', help='Get security system statistics')
    
    # Security check
    security_subparsers.add_parser('check', help='Perform security check now')
    
    # Security enable
    security_subparsers.add_parser('enable', help='Enable security monitoring')
    
    # Security disable
    security_subparsers.add_parser('disable', help='Disable security monitoring')
    
    # Wrapper mode arguments (when no subcommand)
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
        '--metrics',
        action='store_true',
        help='Show real-time system metrics (for dashboard integration)'
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
            from src.daemon.control import start_daemon
            return start_daemon(
                config_path=args.config,
                log_level=args.log_level,
                foreground=args.foreground
            )
        
        elif args.command == 'stop':
            from src.daemon.control import stop_daemon
            return stop_daemon(force=args.force, timeout=args.timeout)
        
        elif args.command == 'restart':
            from src.daemon.control import restart_daemon
            return restart_daemon(
                config_path=args.config,
                log_level=args.log_level
            )
        
        elif args.command == 'status':
            from src.daemon.control import daemon_status
            return daemon_status(verbose=args.verbose)
        
        # Service commands
        elif args.command == 'service':
            return handle_service_command(args)
        
        # Activity command
        elif args.command == 'activity':
            from utils.activity_log import cmd_activity
            return cmd_activity(args)
        
        # Web dashboard command
        elif args.command == 'web':
            from web.server import run_dashboard
            print(f"🌐 Starting Senthium Web Dashboard on http://{args.host}:{args.port}")
            print("   Press Ctrl+C to stop")
            print()
            run_dashboard(host=args.host, port=args.port, debug=args.debug)
            return 0
        
        # Enrollment command
        elif args.command == 'enroll':
            from src.vision.security_manager import SecurityManager
            from src.rules.schema import ConfigSchema
            
            print("=" * 60)
            print("  📸 Senthium Security Enrollment")
            print("=" * 60)
            print()
            
            # Load config to get settings
            try:
                from pathlib import Path
                validator = ConfigSchema()
                config_data = validator.load_and_validate(Path('config/config.yaml'))
                security_config = config_data.get('senthium', {}).get('security', {})
            except:
                security_config = {}
            
            manager = SecurityManager(config=security_config)
            
            if args.image:
                # Enroll from image file
                print(f"  Loading image: {args.image}")
                success = manager.enroll_owner_from_file(args.image, args.name)
            else:
                # Enroll from camera
                print(f"  Look at your camera!")
                print(f"  Capturing in 3 seconds...")
                import time
                for i in range(3, 0, -1):
                    print(f"  {i}...")
                    time.sleep(1)
                print("  📸 Smile!")
                success = manager.enroll_owner_from_camera(args.name)
            
            print()
            if success:
                print(f"  ✅ SUCCESS! {args.name} has been enrolled.")
                print(f"  Security monitoring will now recognize you!")
            else:
                print(f"  ❌ FAILED! Could not enroll {args.name}.")
                print(f"  Make sure your face is clearly visible.")
            print("=" * 60)
            
            manager.cleanup()
            return 0 if success else 1
        
        # Security management commands
        elif args.command == 'security':
            import json
            from src.vision.security_manager import SecurityManager
            from src.rules.schema import ConfigSchema
            from pathlib import Path
            
            action = args.security_action
            
            if action == 'stats':
                # Get security statistics
                try:
                    validator = ConfigSchema()
                    config_data = validator.load_and_validate(Path('config/config.yaml'))
                    security_config = config_data.get('senthium', {}).get('security', {})
                    
                    manager = SecurityManager(config=security_config)
                    stats = manager.get_stats()
                    manager.cleanup()
                    
                    # Output as JSON for API consumption
                    print(json.dumps(stats))
                    return 0
                except Exception as e:
                    print(json.dumps({"error": str(e)}))
                    return 1
            
            elif action == 'check':
                # Perform immediate security check
                try:
                    validator = ConfigSchema()
                    config_data = validator.load_and_validate(Path('config/config.yaml'))
                    security_config = config_data.get('senthium', {}).get('security', {})
                    
                    manager = SecurityManager(config=security_config)
                    manager.enable()  # Ensure enabled
                    result = manager.perform_security_check()
                    manager.cleanup()
                    
                    print(json.dumps(result or {"error": "Security check failed"}))
                    return 0 if result else 1
                except Exception as e:
                    print(json.dumps({"error": str(e)}))
                    return 1
            
            elif action == 'enable':
                # Enable security in config
                import yaml
                try:
                    config_path = Path('config/config.yaml')
                    with open(config_path, 'r') as f:
                        config = yaml.safe_load(f)
                    
                    config['senthium']['security']['enabled'] = True
                    
                    with open(config_path, 'w') as f:
                        yaml.dump(config, f, default_flow_style=False)
                    
                    print(json.dumps({"status": "success", "message": "Security enabled"}))
                    return 0
                except Exception as e:
                    print(json.dumps({"error": str(e)}))
                    return 1
            
            elif action == 'disable':
                # Disable security in config
                import yaml
                try:
                    config_path = Path('config/config.yaml')
                    with open(config_path, 'r') as f:
                        config = yaml.safe_load(f)
                    
                    config['senthium']['security']['enabled'] = False
                    
                    with open(config_path, 'w') as f:
                        yaml.dump(config, f, default_flow_style=False)
                    
                    print(json.dumps({"status": "success", "message": "Security disabled"}))
                    return 0
                except Exception as e:
                    print(json.dumps({"error": str(e)}))
                    return 1
            
            else:
                print(json.dumps({"error": f"Unknown security action: {action}"}))
                return 1
        
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
        
        # Metrics command (for dashboard)
        elif args.metrics:
            from cli.wrapper import cmd_metrics, setup_cli_logging
            setup_cli_logging(args.wrapper_log_level)
            return cmd_metrics()
        
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
