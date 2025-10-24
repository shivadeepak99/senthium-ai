# Senthium v0.5.0 - "Modern Dashboard" Release 🎨

**Release Date**: October 24, 2025

A massive upgrade bringing enterprise-grade service integration, time-based scheduling, activity analytics, and a stunning modern web dashboard!

---

## 🎉 Major Features

### 🌐 Web Dashboard
The centerpiece of v0.5: a gorgeous, modern web interface for monitoring Senthium!

**Features**:
- **Real-time Monitoring**: Live daemon status with WebSocket updates (2s polling)
- **System Metrics**: CPU, Disk I/O, Network bandwidth, Process count
- **Activity Analytics**: 7-day session history with duration breakdowns
- **Daemon Controls**: Start/Stop/Restart buttons directly in UI
- **Modern Design**: Purple/blue gradient with glassmorphism effects
- **Responsive Layout**: Works on desktop and mobile

**Tech Stack**:
- Backend: Go 1.21+ with Gorilla Mux + WebSocket
- Frontend: Next.js 16 + TypeScript + Tailwind CSS
- Icons: Lucide React
- Communication: REST API + WebSocket

**Usage**:
```bash
# Windows
launch_dashboard.bat

# Linux/macOS
./launch_dashboard.sh

# Then open http://localhost:3000
```

### 🎛️ System Service Integration
Run Senthium as a system service that auto-starts on boot!

**Windows Service**:
- SCM (Service Control Manager) integration using pywin32
- Auto-start on boot with SERVICE_AUTO_START
- Config from `%LOCALAPPDATA%\Senthium\config.yaml`
- Service logging to AppData
- Commands: `senthium service install/uninstall/start/stop/restart/status`

**Linux systemd**:
- Security-hardened service file generation
- systemd journal logging with SyslogIdentifier
- Restart policy: on-failure with 10s delay
- Security features: NoNewPrivileges, PrivateTmp, ProtectSystem=strict
- Installation: `sudo senthium service install`

**Commands**:
```bash
# Install as service
senthium service install

# Start service
senthium service start

# Check status
senthium service status

# Stop and uninstall
senthium service stop
senthium service uninstall
```

### ⏰ Schedule Rules
Time-based rules for automatic stay-awake during specific hours!

**Features**:
- Days of week filtering (mon/tue/wed/thu/fri/sat/sun or 'all')
- Time ranges in HH:MM format (24-hour)
- Overnight schedule support (e.g., 22:00-06:00)
- Full integration with existing rules engine

**Example - Work Hours**:
```yaml
- name: "Work Hours"
  type: "schedule"
  description: "Stay awake during work hours"
  days: ["mon", "tue", "wed", "thu", "fri"]
  start_time: "09:00"
  end_time: "17:00"
```

**Example - Gaming Schedule**:
```yaml
- name: "Gaming Hours"
  type: "schedule"
  days: ["fri", "sat", "sun"]
  start_time: "19:00"
  end_time: "23:59"
```

**Example - 24/7 Server Mode**:
```yaml
- name: "Always On"
  type: "schedule"
  days: ["all"]
  start_time: "00:00"
  end_time: "23:59"
```

### 📊 Activity Logging
Comprehensive session tracking with analytics!

**Features**:
- Automatic session tracking (start/end times, duration, trigger)
- JSONL storage format (JSON Lines) - one file per day
- Metrics snapshots (CPU, disk I/O, network at session start)
- Daily and weekly summaries
- Breakdowns by: rule name, hour of day, trigger type
- Top 5 rules by duration

**Storage Location**:
- `logs/activity/activity_YYYY-MM-DD.jsonl`

**CLI Commands**:
```bash
# Last 7 days
senthium activity --days 7

# Today only
senthium activity --days 1
```

**Example Output**:
```
Activity Summary (Last 7 Days)

📅 2025-10-24 (Today)
   Sessions: 5
   Duration: 2:34:15
   Top rules: • Video Rendering: 1:45:30 (2x)
              • Build Tasks: 48:45 (3x)
   Triggers: • Rule Match: 2:10:00 (4x)
             • Wrapper Lock: 24:15 (1x)
```

---

## ✨ Enhancements

### Config Schema
- Added `schedule` rule type to schema validation
- Days array with enum validation
- Time string pattern validation (HH:MM format)
- 3 new example schedule rules in config.example.yaml

### CLI
- Added `senthium service` subcommand group
- Added `senthium activity` command with --days option
- Platform detection for Windows vs Linux service operations

### Documentation
- Updated README with v0.5 features
- Added Web Dashboard section
- Added schedule rule examples
- Updated version badges

---

## 🛠️ Technical Changes

### New Files
- `server/main.go` - Go backend server (270+ lines)
- `server/go.mod` - Go module definition
- `dashboard/` - Complete Next.js application
- `dashboard/app/page.tsx` - Main dashboard UI (310+ lines)
- `src/service/windows_service.py` - Windows Service wrapper (300+ lines)
- `src/service/systemd_generator.py` - systemd service generator (250+ lines)
- `src/utils/activity_log.py` - Activity logging system (350+ lines)
- `src/web/server.py` - Flask alternative backend (280+ lines)
- `launch_dashboard.bat` - Windows launcher script
- `launch_dashboard.sh` - Linux/macOS launcher script

### Modified Files
- `src/cli/main.py` - Added service and activity command handlers
- `src/daemon/core.py` - Integrated activity logging (4 integration points)
- `src/rules/engine.py` - Added _evaluate_schedule_rule() method
- `config/config.schema.json` - Added schedule rule type + properties
- `config/config.example.yaml` - Added 3 example schedule rules
- `README.md` - Updated with v0.5 features

### Dependencies
- **Go**: gorilla/mux v1.8.1, gorilla/websocket v1.5.1, rs/cors v1.10.1
- **Node.js**: next@16.0.0, react@19, tailwindcss@3, lucide-react
- **Python**: No new dependencies (pywin32 already required for Windows)

---

## 📊 Statistics

- **Lines of Code Added**: ~3,500+ lines
- **New Features**: 4 major (dashboard, service, schedule, activity)
- **Files Created**: 24 new files
- **Files Modified**: 6 existing files
- **Commits**: 4 feature commits

---

## 🚀 Upgrade Instructions

### From v0.4.x

1. **Pull latest code**:
```bash
git pull origin main
```

2. **Update dependencies**:
```bash
pip install -e .
```

3. **Install Go (for dashboard)**:
```bash
# Download from https://go.dev/dl/
# Verify: go version
```

4. **Install Node.js (for dashboard)**:
```bash
# Download from https://nodejs.org/
# Verify: node --version
```

5. **Optional: Install as service**:
```bash
# Windows
senthium service install

# Linux
sudo senthium service install
sudo systemctl enable senthium
```

6. **Optional: Add schedule rules**:
```yaml
# Edit config/config.yaml
rules:
  - name: "My Schedule"
    type: "schedule"
    days: ["all"]
    start_time: "09:00"
    end_time: "17:00"
```

---

## 🐛 Known Issues

- Activity logging requires daemon restart to see updates in web dashboard
- Go server must be started before Next.js frontend for WebSocket connection
- macOS launchd service integration not yet implemented (Linux/Windows only)
- Config editor in web dashboard not yet implemented (read-only for now)

---

## 🙏 Credits

Developed with 💖 by your dev waifu

Special thanks to:
- **Gorilla Toolkit** - Excellent Go web libraries
- **Vercel** - Next.js framework
- **Tailwind Labs** - Beautiful CSS framework
- **Lucide** - Clean, consistent icons

---

## 📝 What's Next?

### v0.6.0 (Future)
- Config editor in web dashboard
- Activity graphs and visualizations
- Rule testing and dry-run mode
- macOS launchd service integration
- Mobile app for remote monitoring
- Email/webhook notifications

---

**Enjoy Senthium v0.5.0!** 🎉

If you encounter any issues, please report them on GitHub Issues.
