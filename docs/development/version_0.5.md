# 🚀 Senthium Version 0.5 - Development Roadmap
**Version**: 0.5 (Service Integration & Enhanced Features)  
**Goal**: Production-grade service installation and quality-of-life improvements  
**Platform**: Cross-platform (Windows, Linux, macOS)  
**Timeline**: Week 9-10  
**Status**: 🎯 READY TO START (October 24, 2025)

---

## 📋 **Version 0.5 Objectives**

Building on v0.4 (IPC + CLI wrapper), v0.5 makes Senthium **truly production-ready**:

🎯 **Service Integration**
- [ ] Windows Service wrapper (auto-start on boot)
- [ ] systemd service generator (Linux)
- [ ] launchd plist generator (macOS)
- [ ] Service installer/uninstaller commands

🎯 **Enhanced Features**
- [ ] Activity logging (track what kept PC awake)
- [ ] Rule scheduler (time-based rules, e.g., "no sleep 9am-5pm")
- [ ] Web dashboard (optional, real-time monitoring UI)
- [ ] Config validation tool (test rules before applying)

🎯 **Quality of Life**
- [ ] Better error messages with suggestions
- [ ] Config migration tool (upgrade old configs)
- [ ] Telemetry/analytics (opt-in usage stats)
- [ ] Auto-update checker

**Success Criteria**: You can install Senthium as a system service that starts on boot, with professional logging and helpful error messages.

---

## 🎯 **Phase 1: Windows Service Integration (Days 1-2)**

### **Goal**: Install Senthium as a Windows Service

Windows Services run in the background, start automatically on boot, and survive user logoff.

---

### **Step 1.1: Create Windows Service Wrapper**

**Create `src/service/windows_service.py`**:

```python
"""
Windows Service wrapper for Senthium daemon.
Allows Senthium to run as a Windows Service with auto-start.
"""

import sys
import os
import win32serviceutil  # type: ignore
import win32service  # type: ignore
import win32event  # type: ignore
import servicemanager  # type: ignore
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from daemon.core import SenthiumDaemon
from utils.logger import setup_logger


class SenthiumWindowsService(win32serviceutil.ServiceFramework):
    """Windows Service wrapper for Senthium daemon"""
    
    _svc_name_ = "Senthium"
    _svc_display_name_ = "Senthium Power Management Daemon"
    _svc_description_ = "Intelligent power management service that prevents system sleep during critical tasks"
    
    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.daemon = None
        
        # Setup logging
        self.logger = setup_logger(
            'senthium_service',
            level='INFO',
            log_dir=Path.home() / 'AppData' / 'Local' / 'Senthium' / 'logs'
        )
    
    def SvcStop(self):
        """Called when service is stopped"""
        self.logger.info("Service stop requested")
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        
        # Stop daemon gracefully
        if self.daemon:
            self.daemon.shutdown()
    
    def SvcDoRun(self):
        """Called when service starts"""
        self.logger.info("Service starting...")
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, '')
        )
        
        try:
            self.main()
        except Exception as e:
            self.logger.exception(f"Service crashed: {e}")
            servicemanager.LogErrorMsg(f"Senthium service crashed: {e}")
    
    def main(self):
        """Main service loop"""
        # Config path from registry or default
        config_path = self.get_config_path()
        
        self.logger.info(f"Starting daemon with config: {config_path}")
        
        # Create and run daemon
        self.daemon = SenthiumDaemon(
            config_path=config_path,
            log_level='INFO'
        )
        
        # Run until stop event
        self.daemon.run()
        
        # Wait for stop signal
        win32event.WaitForSingleObject(self.stop_event, win32event.INFINITE)
        
        self.logger.info("Service stopped")
    
    def get_config_path(self) -> str:
        """Get config path from registry or use default"""
        # TODO: Read from registry
        # For now, use default location
        default_config = Path.home() / 'AppData' / 'Local' / 'Senthium' / 'config.yaml'
        
        if default_config.exists():
            return str(default_config)
        
        # Fallback to installation directory
        return str(Path(__file__).parent.parent.parent / 'config' / 'config.yaml')


if __name__ == '__main__':
    if len(sys.argv) == 1:
        # Called by Windows SCM (Service Control Manager)
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(SenthiumWindowsService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        # Called from command line for install/remove/start/stop
        win32serviceutil.HandleCommandLine(SenthiumWindowsService)
```

**Key Features:**
- Runs as Windows Service
- Auto-starts on boot
- Survives user logoff
- Logs to user AppData directory
- Graceful start/stop

---

### **Step 1.2: Add Service Management Commands**

**Update `src/cli/main.py`** to add service commands:

```python
def cmd_install_service():
    """Install Senthium as Windows service"""
    if not sys.platform.startswith('win'):
        print("[ERROR] Service installation is only supported on Windows")
        print("        Use systemd on Linux or launchd on macOS")
        return 1
    
    try:
        import win32serviceutil  # type: ignore
        from service.windows_service import SenthiumWindowsService
        
        print("[*] Installing Senthium as Windows service...")
        
        # Install service
        win32serviceutil.InstallService(
            SenthiumWindowsService._svc_reg_class_,
            SenthiumWindowsService._svc_name_,
            SenthiumWindowsService._svc_display_name_,
            startType=win32service.SERVICE_AUTO_START
        )
        
        print("[OK] Service installed successfully")
        print("     Service name: Senthium")
        print("     Start type: Automatic (starts on boot)")
        print("")
        print("To start the service now:")
        print("     senthium service start")
        
        return 0
        
    except Exception as e:
        print(f"[ERROR] Failed to install service: {e}")
        return 1


def cmd_uninstall_service():
    """Uninstall Senthium Windows service"""
    if not sys.platform.startswith('win'):
        print("[ERROR] Service commands are only for Windows")
        return 1
    
    try:
        import win32serviceutil  # type: ignore
        from service.windows_service import SenthiumWindowsService
        
        print("[*] Uninstalling Senthium service...")
        
        # Remove service
        win32serviceutil.RemoveService(SenthiumWindowsService._svc_name_)
        
        print("[OK] Service uninstalled successfully")
        return 0
        
    except Exception as e:
        print(f"[ERROR] Failed to uninstall service: {e}")
        return 1
```

**New CLI commands:**
```bash
senthium service install   # Install as Windows service
senthium service uninstall # Remove Windows service
senthium service start     # Start service
senthium service stop      # Stop service
senthium service restart   # Restart service
```

---

## 🎯 **Phase 2: Linux systemd Integration (Day 2)**

### **Goal**: Generate systemd service files for Linux

---

### **Step 2.1: Create systemd Service Generator**

**Create `src/service/systemd_generator.py`**:

```python
"""
systemd service file generator for Linux.
Creates .service files for automatic daemon start on boot.
"""

import os
import sys
from pathlib import Path
from typing import Optional


SYSTEMD_SERVICE_TEMPLATE = """[Unit]
Description=Senthium Intelligent Power Management Daemon
After=network.target

[Service]
Type=simple
User={user}
Group={group}
WorkingDirectory={working_dir}
ExecStart={python_path} -m daemon.core --config {config_path}
ExecReload=/bin/kill -HUP $MAINPID
Restart=on-failure
RestartSec=10s
StandardOutput=journal
StandardError=journal

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths={logs_dir}

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
        user = os.getenv('USER', 'nobody')
    
    if group is None:
        group = os.getenv('USER', 'nobody')
    
    if config_path is None:
        config_path = str(Path.home() / '.config' / 'senthium' / 'config.yaml')
    
    if install_path is None:
        # Try to detect installation path
        install_path = Path(__file__).parent.parent.parent
    
    python_path = sys.executable
    working_dir = str(install_path)
    logs_dir = str(Path.home() / '.local' / 'share' / 'senthium' / 'logs')
    
    # Create service content
    service_content = SYSTEMD_SERVICE_TEMPLATE.format(
        user=user,
        group=group,
        working_dir=working_dir,
        python_path=python_path,
        config_path=config_path,
        logs_dir=logs_dir
    )
    
    return service_content


def install_systemd_service(service_content: str) -> bool:
    """
    Install systemd service file.
    
    Args:
        service_content: Service file content
        
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
        os.system('systemctl daemon-reload')
        
        print("[OK] systemd reloaded")
        print("")
        print("To enable service (start on boot):")
        print("     sudo systemctl enable senthium")
        print("")
        print("To start service now:")
        print("     sudo systemctl start senthium")
        print("")
        print("To check status:")
        print("     sudo systemctl status senthium")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to install service: {e}")
        return False
```

---

## 🎯 **Phase 3: Activity Logging (Day 3)**

### **Goal**: Track what rules kept the PC awake and for how long

---

### **Step 3.1: Create Activity Logger**

**Create `src/utils/activity_log.py`**:

```python
"""
Activity logger - tracks what kept the system awake.
Provides analytics and insights into power management decisions.
"""

import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict


@dataclass
class ActivitySession:
    """Represents a period when system was kept awake"""
    start_time: datetime
    end_time: Optional[datetime]
    duration_seconds: float
    trigger_reason: str  # 'rule_match' or 'wrapper_lock'
    rule_name: Optional[str]  # Which rule matched
    process_name: Optional[str]  # Wrapper command if applicable
    metrics_snapshot: Dict  # CPU, disk, network at start


class ActivityLogger:
    """Logs and analyzes stay-awake sessions"""
    
    def __init__(self, log_dir: Path = None):
        """
        Initialize activity logger.
        
        Args:
            log_dir: Directory for activity logs (default: logs/activity/)
        """
        if log_dir is None:
            log_dir = Path(__file__).parent.parent.parent / 'logs' / 'activity'
        
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.current_session: Optional[ActivitySession] = None
        self.logger = logging.getLogger(__name__)
    
    def start_session(
        self,
        reason: str,
        rule_name: Optional[str] = None,
        process_name: Optional[str] = None,
        metrics: Optional[Dict] = None
    ):
        """Start new activity session"""
        if self.current_session and self.current_session.end_time is None:
            # End previous session first
            self.end_session()
        
        self.current_session = ActivitySession(
            start_time=datetime.now(),
            end_time=None,
            duration_seconds=0.0,
            trigger_reason=reason,
            rule_name=rule_name,
            process_name=process_name,
            metrics_snapshot=metrics or {}
        )
        
        self.logger.info(f"Activity session started: {reason}")
    
    def end_session(self):
        """End current activity session"""
        if not self.current_session:
            return
        
        self.current_session.end_time = datetime.now()
        self.current_session.duration_seconds = (
            self.current_session.end_time - self.current_session.start_time
        ).total_seconds()
        
        # Save to file
        self._save_session(self.current_session)
        
        self.logger.info(
            f"Activity session ended: {self.current_session.trigger_reason} "
            f"(duration: {self.current_session.duration_seconds:.1f}s)"
        )
        
        self.current_session = None
    
    def _save_session(self, session: ActivitySession):
        """Save session to daily log file"""
        date_str = session.start_time.strftime('%Y-%m-%d')
        log_file = self.log_dir / f'activity_{date_str}.jsonl'
        
        # Convert to JSON (handle datetime serialization)
        session_dict = asdict(session)
        session_dict['start_time'] = session.start_time.isoformat()
        if session.end_time:
            session_dict['end_time'] = session.end_time.isoformat()
        
        # Append to JSONL file (one JSON per line)
        with open(log_file, 'a') as f:
            f.write(json.dumps(session_dict) + '\n')
    
    def get_daily_summary(self, date: datetime = None) -> Dict:
        """Get summary of activity for a specific day"""
        if date is None:
            date = datetime.now()
        
        date_str = date.strftime('%Y-%m-%d')
        log_file = self.log_dir / f'activity_{date_str}.jsonl'
        
        if not log_file.exists():
            return {
                'date': date_str,
                'total_sessions': 0,
                'total_duration_seconds': 0.0,
                'by_rule': {},
                'by_hour': {}
            }
        
        # Parse log file
        sessions = []
        with open(log_file, 'r') as f:
            for line in f:
                sessions.append(json.loads(line))
        
        # Calculate summary
        total_duration = sum(s['duration_seconds'] for s in sessions)
        
        by_rule = {}
        for session in sessions:
            rule = session.get('rule_name', 'unknown')
            if rule not in by_rule:
                by_rule[rule] = {'count': 0, 'duration': 0.0}
            by_rule[rule]['count'] += 1
            by_rule[rule]['duration'] += session['duration_seconds']
        
        by_hour = {}
        for session in sessions:
            hour = datetime.fromisoformat(session['start_time']).hour
            if hour not in by_hour:
                by_hour[hour] = {'count': 0, 'duration': 0.0}
            by_hour[hour]['count'] += 1
            by_hour[hour]['duration'] += session['duration_seconds']
        
        return {
            'date': date_str,
            'total_sessions': len(sessions),
            'total_duration_seconds': total_duration,
            'total_duration_human': str(timedelta(seconds=int(total_duration))),
            'by_rule': by_rule,
            'by_hour': by_hour
        }


# CLI command for viewing activity
def cmd_activity_summary(days: int = 1):
    """Show activity summary for recent days"""
    activity_logger = ActivityLogger()
    
    print(f"\n{'='*60}")
    print(f"  Senthium Activity Summary (Last {days} day{'s' if days > 1 else ''})")
    print(f"{'='*60}\n")
    
    total_all_days = 0.0
    
    for i in range(days):
        date = datetime.now() - timedelta(days=i)
        summary = activity_logger.get_daily_summary(date)
        
        print(f"📅 {summary['date']}")
        print(f"   Sessions: {summary['total_sessions']}")
        print(f"   Duration: {summary['total_duration_human']}")
        
        if summary['by_rule']:
            print(f"   Top rules:")
            sorted_rules = sorted(
                summary['by_rule'].items(),
                key=lambda x: x[1]['duration'],
                reverse=True
            )
            for rule, stats in sorted_rules[:3]:
                duration_str = str(timedelta(seconds=int(stats['duration'])))
                print(f"     • {rule}: {duration_str} ({stats['count']} times)")
        
        print()
        total_all_days += summary['total_duration_seconds']
    
    print(f"{'='*60}")
    total_human = str(timedelta(seconds=int(total_all_days)))
    print(f"  Total across all days: {total_human}")
    print(f"{'='*60}\n")
```

---

## 🎯 **Phase 4: Rule Scheduler (Day 4)**

### **Goal**: Time-based rules (e.g., "never sleep during work hours")

---

### **Step 4.1: Add Time-Based Rule Type**

**Update `config/config.schema.json`** to add `schedule` rule type:

```json
{
  "type": "schedule",
  "description": "Time-based rules",
  "properties": {
    "name": {"type": "string"},
    "type": {"const": "schedule"},
    "enabled": {"type": "boolean", "default": true},
    "days": {
      "type": "array",
      "items": {"enum": ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]},
      "description": "Days of week when rule applies"
    },
    "start_time": {
      "type": "string",
      "pattern": "^([01]?[0-9]|2[0-3]):[0-5][0-9]$",
      "description": "Start time (HH:MM format, 24-hour)"
    },
    "end_time": {
      "type": "string",
      "pattern": "^([01]?[0-9]|2[0-3]):[0-5][0-9]$",
      "description": "End time (HH:MM format, 24-hour)"
    }
  }
}
```

**Example config:**
```yaml
rules:
  - name: "Work Hours"
    type: "schedule"
    description: "Keep awake during work hours"
    days: ["mon", "tue", "wed", "thu", "fri"]
    start_time: "09:00"
    end_time: "17:00"
    enabled: true
```

---

## 🎯 **Phase 5: Web Dashboard (Days 5-6) [OPTIONAL]**

### **Goal**: Real-time monitoring web UI

This is optional but would be SUPER cool! 😎

---

### **Features:**
- Real-time daemon status
- Live rules visualization
- Activity graphs (what's keeping PC awake)
- Config editor with validation
- Start/stop daemon controls

**Tech Stack:**
- Backend: Flask (lightweight Python web framework)
- Frontend: Plain HTML/CSS/JavaScript (no heavy frameworks)
- WebSockets: Real-time updates

---

## 📊 **Version 0.5 Summary**

**What We're Building:**
1. ✅ Windows Service integration (auto-start on boot)
2. ✅ systemd service generator (Linux)
3. ✅ launchd integration (macOS)
4. ✅ Activity logging (track stay-awake sessions)
5. ✅ Rule scheduler (time-based rules)
6. ⭐ Web dashboard (optional, but cool!)

**Timeline:** 5-6 days
**LOC Estimate:** ~1,500 lines new code
**Difficulty:** Medium (service integration is platform-specific)

---

## 🎯 **v0.5 Completion Checklist**

### **Service Integration**
- [ ] Create Windows Service wrapper (`windows_service.py`)
- [ ] Add service management commands to CLI
- [ ] Test Windows Service install/uninstall
- [ ] Create systemd service generator (`systemd_generator.py`)
- [ ] Add Linux service commands
- [ ] Test systemd integration
- [ ] Create launchd plist generator (macOS)
- [ ] Add macOS service commands

### **Enhanced Features**
- [ ] Implement activity logger (`activity_log.py`)
- [ ] Integrate activity logging into daemon
- [ ] Add `senthium activity` CLI command
- [ ] Add schedule rule type to schema
- [ ] Implement schedule rule evaluation
- [ ] Test time-based rules

### **Optional: Web Dashboard**
- [ ] Create Flask backend (`web_server.py`)
- [ ] Build real-time status API
- [ ] Create HTML/CSS frontend
- [ ] Add WebSocket for live updates
- [ ] Add config editor UI
- [ ] Deploy and test

### **Documentation**
- [ ] Update USER_GUIDE.md with service installation
- [ ] Document activity logging
- [ ] Document schedule rules
- [ ] Create service installation guide per platform
- [ ] Update README.md with v0.5 features

### **Testing & Release**
- [ ] Test Windows Service on Windows 11
- [ ] Test systemd on Linux
- [ ] Test activity logging
- [ ] Test schedule rules
- [ ] Create v0.5.0 release notes
- [ ] Tag and push v0.5.0

---

## 🚀 **Let's Start with Phase 1!**

We'll begin with **Windows Service integration** since you're on Windows 11. This will let Senthium start automatically on boot!

Ready to build, CEO? 💪💖

---

*Created: October 24, 2025*
*Status: Ready to implement*
