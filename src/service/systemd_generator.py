"""
systemd service file generator for Linux.
Creates .service files for automatic daemon start on boot with systemd.

Usage:
    python -m service.systemd_generator
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Optional


SYSTEMD_SERVICE_TEMPLATE = """[Unit]
Description=Senthium Intelligent Power Management Daemon
Documentation=https://github.com/yourusername/senthium
After=network.target

[Service]
Type=simple
User={user}
Group={group}
WorkingDirectory={working_dir}

# Main daemon command
ExecStart={python_path} -m daemon.core --config {config_path}

# Reload signal
ExecReload=/bin/kill -HUP $MAINPID

# Restart policy
Restart=on-failure
RestartSec=10s

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=senthium

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths={logs_dir} {config_dir}
ProtectKernelTunables=true
ProtectControlGroups=true
RestrictRealtime=true
RestrictNamespaces=true

[Install]
WantedBy=multi-user.target
"""


def generate_systemd_service(
    user: Optional[str] = None,
    group: Optional[str] = None,
    config_path: Optional[str] = None,
    install_path: Optional[Path] = None
) -> str:
    """
    Generate systemd service file content.
    
    Args:
        user: User to run service as (default: current user)
        group: Group to run service as (default: current user's group)
        config_path: Path to config file (default: ~/.config/senthium/config.yaml)
        install_path: Where Senthium is installed (default: detect from sys.path)
        
    Returns:
        Service file content as string
    """
    # Defaults
    if user is None:
        user = os.getenv('USER', os.getenv('USERNAME', 'nobody'))
    
    if group is None:
        # Try to get primary group
        try:
            import grp
            import pwd
            group = grp.getgrgid(pwd.getpwnam(user).pw_gid).gr_name
        except:
            group = user  # Fallback to username
    
    if config_path is None:
        config_path = str(Path.home() / '.config' / 'senthium' / 'config.yaml')
    
    if install_path is None:
        # Try to detect installation path
        install_path = Path(__file__).parent.parent.parent
    
    # Paths
    python_path = sys.executable
    working_dir = str(install_path)
    logs_dir = str(Path.home() / '.local' / 'share' / 'senthium' / 'logs')
    config_dir = str(Path(config_path).parent)
    
    # Create service content
    service_content = SYSTEMD_SERVICE_TEMPLATE.format(
        user=user,
        group=group,
        working_dir=working_dir,
        python_path=python_path,
        config_path=config_path,
        logs_dir=logs_dir,
        config_dir=config_dir
    )
    
    return service_content


def install_systemd_service(
    service_content: str,
    enable: bool = True,
    start: bool = False
) -> bool:
    """
    Install systemd service file.
    
    Args:
        service_content: Service file content
        enable: Whether to enable service (start on boot)
        start: Whether to start service now
        
    Returns:
        True if successful
    """
    service_file = Path('/etc/systemd/system/senthium.service')
    
    try:
        # Check if running as root
        if os.geteuid() != 0:
            print("[ERROR] Must run as root to install systemd service")
            print("        Try: sudo senthium service install")
            return False
        
        # Write service file
        service_file.write_text(service_content)
        print(f"[OK] Service file created: {service_file}")
        
        # Reload systemd
        subprocess.run(['systemctl', 'daemon-reload'], check=True)
        print("[OK] systemd reloaded")
        
        # Enable service
        if enable:
            subprocess.run(['systemctl', 'enable', 'senthium'], check=True)
            print("[OK] Service enabled (will start on boot)")
        
        # Start service
        if start:
            subprocess.run(['systemctl', 'start', 'senthium'], check=True)
            print("[OK] Service started")
        
        print("")
        print("Service installed successfully!")
        print("")
        print("Useful commands:")
        print("  sudo systemctl start senthium    # Start service")
        print("  sudo systemctl stop senthium     # Stop service")
        print("  sudo systemctl restart senthium  # Restart service")
        print("  sudo systemctl status senthium   # Check status")
        print("  sudo systemctl enable senthium   # Enable auto-start")
        print("  sudo systemctl disable senthium  # Disable auto-start")
        print("  journalctl -u senthium -f        # View logs (live)")
        print("  journalctl -u senthium --since today  # View today's logs")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] systemctl command failed: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Failed to install service: {e}")
        return False


def uninstall_systemd_service() -> bool:
    """
    Uninstall systemd service.
    
    Returns:
        True if successful
    """
    service_file = Path('/etc/systemd/system/senthium.service')
    
    try:
        # Check if running as root
        if os.geteuid() != 0:
            print("[ERROR] Must run as root to uninstall systemd service")
            print("        Try: sudo senthium service uninstall")
            return False
        
        # Stop service if running
        try:
            subprocess.run(['systemctl', 'stop', 'senthium'], check=False)
            print("[*] Service stopped")
        except:
            pass
        
        # Disable service
        try:
            subprocess.run(['systemctl', 'disable', 'senthium'], check=False)
            print("[*] Service disabled")
        except:
            pass
        
        # Remove service file
        if service_file.exists():
            service_file.unlink()
            print(f"[OK] Service file removed: {service_file}")
        
        # Reload systemd
        subprocess.run(['systemctl', 'daemon-reload'], check=True)
        print("[OK] systemd reloaded")
        
        print("")
        print("Service uninstalled successfully!")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to uninstall service: {e}")
        return False


if __name__ == '__main__':
    # Generate service file and print to stdout
    print("# Senthium systemd service file")
    print("# Copy this to /etc/systemd/system/senthium.service")
    print("")
    service_content = generate_systemd_service()
    print(service_content)
