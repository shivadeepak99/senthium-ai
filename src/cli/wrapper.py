"""
CLI wrapper for explicit stay-awake mode.

Allows running specific commands with guaranteed stay-awake lock:
    senthium --stay-awake "npm run build"
    senthium --stay-awake "docker build -t myapp ."
    senthium --status
    senthium --reload
"""

import sys
import logging
import subprocess
import argparse
from typing import Optional
from pathlib import Path

from ipc import IPCClient, IPCResponse

logger = logging.getLogger(__name__)


def setup_cli_logging(level: str = "INFO") -> None:
    """
    Set up logging for CLI (simpler than daemon).
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
    """
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(message)s",  # Clean format for CLI
        handlers=[logging.StreamHandler(sys.stdout)]
    )


def cmd_stay_awake(command: str) -> int:
    """
    Run command with wrapper lock (stay-awake guaranteed).
    
    Args:
        command: Shell command to execute
        
    Returns:
        Exit code from command
    """
    ipc_client = IPCClient(timeout=5.0)
    
    try:
        # Acquire wrapper lock from daemon
        print("[*] Acquiring stay-awake lock...")
        response = ipc_client.send_command("ACQUIRE_LOCK")
        
        if not response.success:
            print(f"[ERROR] Failed to acquire lock: {response.message}")
            return 1
            
        print("[OK] Stay-awake lock acquired")
        print(f"[EXEC] Running: {command}")
        print()
        
        # Execute user command
        try:
            result = subprocess.run(
                command,
                shell=True,
                stdin=sys.stdin,
                stdout=sys.stdout,
                stderr=sys.stderr
            )
            
            exit_code = result.returncode
            print()
            print(f"[OK] Command completed with exit code: {exit_code}")
            
            return exit_code
            
        except KeyboardInterrupt:
            print()
            print("[WARN] Command interrupted by user (Ctrl+C)")
            return 130  # Standard SIGINT exit code
            
        except Exception as e:
            print()
            print(f"[ERROR] Command failed: {e}")
            return 1
            
    finally:
        # Always release lock
        try:
            print("[*] Releasing stay-awake lock...")
            release_response = ipc_client.send_command("RELEASE_LOCK")
            
            if release_response.success:
                print("[OK] Stay-awake lock released")
            else:
                print(f"[WARN] Failed to release lock: {release_response.message}")
                
        except Exception as e:
            print(f"[WARN] Error releasing lock: {e}")


def cmd_status() -> int:
    """
    Query daemon status.
    
    Returns:
        0 on success, 1 on failure
    """
    ipc_client = IPCClient(timeout=5.0)
    
    try:
        response = ipc_client.send_command("STATUS")
        
        if not response.success:
            print(f"[ERROR] Failed to get status: {response.message}")
            return 1
            
        # Pretty-print status
        data = response.data
        state = data.get("state", "unknown")
        uptime = data.get("uptime_seconds", 0)
        
        print("=" * 60)
        print("  Senthium Daemon Status")
        print("=" * 60)
        print(f"  State:           {state}")
        print(f"  Uptime:          {_format_duration(uptime)}")
        print(f"  Poll count:      {data.get('poll_count', 0)}")
        print(f"  Rules matched:   {data.get('rules_matched', 0)}")
        print(f"  Active sessions: {data.get('active_sessions', 0)}")
        
        if data.get("awake", False):
            awake_duration = data.get("awake_duration_seconds", 0)
            max_duration = data.get("max_awake_duration", 0)
            remaining = max_duration - awake_duration
            
            print(f"  Stay-awake:      Active ({_format_duration(awake_duration)})")
            print(f"  Failsafe:        {_format_duration(remaining)} remaining")
        else:
            print(f"  Stay-awake:      Inactive")
            
        print("=" * 60)
        
        return 0
        
    except ConnectionError as e:
        print(f"[ERROR] {e}")
        return 1
    except Exception as e:
        print(f"[ERROR] {e}")
        return 1


def cmd_info() -> int:
    """
    Show detailed daemon information (config, rules, etc.).
    
    Returns:
        0 on success, 1 on failure
    """
    ipc_client = IPCClient(timeout=5.0)
    
    try:
        response = ipc_client.send_command("INFO")
        
        if not response.success:
            print(f"[ERROR] Failed to get info: {response.message}")
            return 1
            
        data = response.data
        
        print("=" * 60)
        print("  Senthium Daemon Information")
        print("=" * 60)
        
        # Config info
        config_path = data.get("config_path", "unknown")
        poll_interval = data.get("poll_interval", 0)
        max_awake = data.get("max_awake_duration", 0)
        
        print(f"  Config:      {Path(config_path).name}")
        print(f"  Poll every:  {poll_interval}s")
        print(f"  Max awake:   {_format_duration(max_awake)}")
        print("-" * 60)
        
        # Rules info
        rules = data.get("rules", [])
        print(f"  Active Rules: {len(rules)}")
        print("-" * 60)
        
        for i, rule in enumerate(rules, 1):
            rule_name = rule.get("name", f"Rule {i}")
            rule_type = rule.get("type", "unknown")
            print(f"  {i}. {rule_name}")
            print(f"     Type: {rule_type}")
            
        print("=" * 60)
        
        return 0
        
    except ConnectionError as e:
        print(f"[ERROR] {e}")
        return 1
    except Exception as e:
        print(f"[ERROR] {e}")
        return 1


def cmd_reload() -> int:
    """
    Reload daemon configuration without restart.
    
    Returns:
        0 on success, 1 on failure
    """
    ipc_client = IPCClient(timeout=5.0)
    
    try:
        print("[*] Reloading daemon configuration...")
        response = ipc_client.send_command("RELOAD_CONFIG")
        
        if not response.success:
            print(f"[ERROR] Failed to reload: {response.message}")
            return 1
            
        print("[OK] Configuration reloaded successfully")
        
        # Show how many rules loaded
        rules_count = response.data.get("rules_count", 0)
        print(f"     Loaded {rules_count} rule(s)")
        
        return 0
        
    except ConnectionError as e:
        print(f"[ERROR] {e}")
        return 1
    except Exception as e:
        print(f"[ERROR] {e}")
        return 1


def _format_duration(seconds: float) -> str:
    """
    Format duration in human-readable form.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted string like "2h 30m" or "45s"
    """
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s" if secs > 0 else f"{minutes}m"
    else:
        hours = int(seconds / 3600)
        minutes = int((seconds % 3600) / 60)
        return f"{hours}h {minutes}m" if minutes > 0 else f"{hours}h"


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        prog="senthium",
        description="Intelligent lock & sleep manager - CLI wrapper",
        epilog="Examples:\n"
               "  senthium --stay-awake 'npm run build'\n"
               "  senthium --status\n"
               "  senthium --info\n"
               "  senthium --reload\n",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--stay-awake",
        metavar="COMMAND",
        help="Run command with stay-awake lock (explicit mode)"
    )
    
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show daemon status"
    )
    
    parser.add_argument(
        "--info",
        action="store_true",
        help="Show detailed daemon information"
    )
    
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Reload daemon configuration"
    )
    
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Set logging level (default: INFO)"
    )
    
    return parser.parse_args()


def main() -> int:
    """
    Main CLI entry point.
    
    Returns:
        Exit code
    """
    args = parse_args()
    
    # Setup logging
    setup_cli_logging(args.log_level)
    
    # Route to appropriate command
    try:
        if args.stay_awake:
            return cmd_stay_awake(args.stay_awake)
        elif args.status:
            return cmd_status()
        elif args.info:
            return cmd_info()
        elif args.reload:
            return cmd_reload()
        else:
            # No command specified - show help
            parse_args().print_help()
            return 0
            
    except KeyboardInterrupt:
        print("\n[WARN] Interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1
if __name__ == "__main__":
    sys.exit(main())
