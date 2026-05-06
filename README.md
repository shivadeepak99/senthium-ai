# 🔒 Senthium AI Security System

<div align="center">

![Version](https://img.shields.io/badge/version-0.6.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-green.svg)
![OpenCV](https://img.shields.io/badge/OpenCV-4.8+-green.svg)
![DeepFace](https://img.shields.io/badge/DeepFace-0.0.79+-purple.svg)
![License](https://img.shields.io/badge/license-MIT-purple.svg)

**AI-powered face recognition security for your PC. Protect your system when you're away.**

[Features](#-features) • [Quick Start](#-quick-start) • [Screenshots](#-screenshots) • [Usage](#-usage) • [Configuration](#%EF%B8%8F-configuration)

</div>

---

## 🎯 The Problem

You need to leave your PC running (downloads, renders, backups), but you can't shut it down. Now you're stuck with:

- 🔓 **Leaving your PC unlocked** (anyone can access it!)
- 😴 **System sleep** (interrupts your tasks)
- ⚠️ **Unauthorized access** (no way to know if someone used it)

**Senthium AI Security solves this.**

---

## ✨ Features

### � **AI-Powered Security**
- **Face Detection**: OpenCV DNN - fast, accurate, no dlib dependency
- **Face Recognition**: DeepFace with Facenet/ArcFace models
- **Multi-face Detection**: Detect multiple people simultaneously
- **Real-time Monitoring**: Continuous background surveillance

### 📢 **Smart Alerts**
- **💜 Discord**: Instant webhook notifications with snapshots
- **✉️ Email**: SMTP alerts (Gmail, Outlook, Yahoo, custom)
- **💬 Telegram**: Bot notifications
- **🖥️ Windows Toast**: Desktop notifications
- **📝 Alert History**: Complete log with timestamps and photos

### 🎨 **Beautiful Web Dashboard**
- **Streamlit Interface**: Modern, responsive web UI
- **Face Enrollment**: Drag-and-drop photo upload
- **Manual Check**: One-click security scan
- **Settings Page**: Configure all options from GUI (Discord webhook, SMTP, etc.)
- **Live Stats**: Real-time monitoring dashboard

### 🤖 **Background Daemon**
- **24/7 Monitoring**: Runs silently in background
- **Auto-start**: Launch on system boot (Windows service)
- **Low Overhead**: Minimal CPU/RAM usage
- **Configurable**: Adjust check interval, tolerance, cooldown
- **Service Commands**: `senthium service install/start/stop/status`

### 📊 **Activity Logging** *(NEW!)*
- **Session Tracking**: Logs every stay-awake session with metrics
- **Analytics Engine**: Daily/weekly summaries, top rules, trigger breakdowns
- **JSONL Storage**: Efficient append-only logs
- **CLI Reporting**: `senthium activity --days 7`

### 🛡️ **Safe & Deterministic**
- **Failsafe Timer**: Max awake duration prevents infinite lock
- **State Machine**: Predictable behavior, no surprises
- **Graceful Shutdown**: Handles signals cleanly

### 🎮 **Flexible Control**
- **Daemon Mode**: Background service with auto-detection
- **Wrapper Mode**: Explicit `senthium run <command>` for guaranteed stay-awake
- **CLI Management**: Start, stop, restart, status commands

### ⚡ **Lightweight & Fast**
- **< 50MB RAM**: Minimal resource footprint
- **< 0.5% CPU**: Efficient polling (configurable intervals)
- **Cross-platform**: Windows, Linux, macOS support

---

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/shivadeepak99/senthium-ai.git
cd senthium-ai

# Install with pip
pip install -e .

# Verify installation
senthium --version
```

### Create Configuration

```bash
# Copy example config
cp config/examples/minimal.yaml config/config.yaml

# Edit config (or use examples for developer/downloads/media-server)
notepad config/config.yaml  # Windows
nano config/config.yaml     # Linux/macOS
```

### Start Daemon

```bash
# Start daemon (runs in background)
senthium start

# Check status
senthium status

# View live info
senthium --info

# Stop daemon
senthium stop
```

### Install as System Service *(NEW!)*

```bash
# Windows
senthium service install
senthium service start

# Linux
sudo senthium service install
sudo systemctl start senthium
```

### View Activity Logs *(NEW!)*

```bash
# Last 7 days of activity
senthium activity --days 7

# Today's activity
senthium activity --days 1
```

### Launch Web Dashboard *(NEW!)*

```bash
# Windows
launch_dashboard.bat

# Linux/macOS
./launch_dashboard.sh

# Then open http://localhost:3000
```

### Wrapper Mode (Explicit)

```bash
# Run command and guarantee stay-awake
senthium run npm run build

# Example: long compilation
senthium run cargo build --release

# Example: video encoding
senthium run ffmpeg -i input.mp4 output.mkv
```

**That's it!** Senthium will:
1. ✅ Monitor your configured processes/metrics
2. ✅ Keep PC awake when rules match
3. ✅ Let it sleep when idle
4. ✅ Respect max awake duration (failsafe)

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| **[User Guide](docs/USER_GUIDE.md)** | Complete usage guide with examples |
| **[Installation](docs/INSTALL.md)** | Platform-specific installation instructions |
| **[Configuration Reference](docs/CONFIG_REFERENCE.md)** | All config options explained |
| **[Why Senthium?](docs/WHY.md)** | The story behind this project |
| **[Development Plan](docs/DEVELOPMENT_PLAN.md)** | Roadmap and architecture |

---

## 🎨 Example Configurations

**Developer Workstation** (IDEs, builds, Docker)
```yaml
rules:
  - name: "Code Editors"
    type: "process"
    processes: ["code", "pycharm", "vim"]
  - name: "Build Systems"
    type: "process"
    processes: ["npm", "cargo", "make", "docker"]
```

**Download Manager** (Torrents, network activity)
```yaml
rules:
  - name: "BitTorrent"
    type: "process"
    processes: ["qbittorrent", "transmission"]
  - name: "High Network"
    type: "network"
    download_mbps: 5.0
    duration: 20
```

**Media Server** (Plex, transcoding)
```yaml
rules:
  - name: "Media Servers"
    type: "process"
    processes: ["Plex Media Server", "jellyfin"]
  - name: "Transcoding CPU"
    type: "cpu"
    threshold: 50
    duration: 60
```

**Work Hours Schedule** *(NEW!)*
```yaml
rules:
  - name: "Work Hours"
    type: "schedule"
    days: ["mon", "tue", "wed", "thu", "fri"]
    start_time: "09:00"
    end_time: "17:00"
```

👉 **See [config/examples/](config/examples/) for complete configs**

---

## 🌐 Web Dashboard

Senthium now includes a gorgeous modern web dashboard for real-time monitoring!

### Features
- 📊 **Live Daemon Status**: Real-time updates via WebSocket
- 📈 **System Metrics**: CPU, Disk I/O, Network, Processes
- 📅 **Activity Analytics**: 7-day session history
- 🎮 **Daemon Controls**: Start/Stop/Restart buttons
- 🎨 **Modern UI**: Gradient design with glassmorphism effects

### Launch Dashboard

```bash
# Windows
launch_dashboard.bat

# Linux/macOS
./launch_dashboard.sh
```

Then open **http://localhost:3000** in your browser!

### Architecture
- **Backend**: Go server with WebSocket support (Port 8080)
- **Frontend**: Next.js 16 + TypeScript + Tailwind CSS (Port 3000)
- **Communication**: REST API + WebSocket for real-time updates

### Manual Start

```bash
# Start backend (in terminal 1)
cd server
go run main.go

# Start frontend (in terminal 2)
cd dashboard
npm install
npm run dev
```

---

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# View coverage report
# Open htmlcov/index.html in browser
```

**Current Status**: 73/74 tests passing, 71% coverage

---

## 📁 Project Structure

```
senthium/
├── src/
│   ├── daemon/
│   │   ├── core.py          # Main daemon state machine ✅
│   │   ├── monitor.py       # System metrics collector ✅
│   │   └── control.py       # Daemon management (start/stop) ✅
│   ├── rules/
│   │   └── engine.py        # Rules evaluation engine ✅
│   ├── ipc/
│   │   ├── server.py        # IPC server (Unix socket/Named Pipe) ✅
│   │   └── client.py        # IPC client ✅
│   ├── cli/
│   │   ├── main.py          # CLI entry point ✅
│   │   └── wrapper.py       # Explicit wrapper mode ✅
│   └── utils/
│       ├── logger.py        # Logging ✅
│       └── pid.py           # PID file management ✅
├── config/
│   └── examples/            # Example configurations ✅
├── docs/                    # Documentation ✅
└── tests/                   # Test suite ✅
```

---

## 🗺️ Roadmap

- ✅ **v0.1**: System monitoring foundation
- ✅ **v0.2**: Rules engine (5 rule types)
- ✅ **v0.3**: Daemon core (state machine, power management)
- ✅ **v0.4**: IPC + CLI wrapper + daemon management
- ✅ **v0.5**: systemd/Windows service integration
- ✅ **v0.6**: Streamlit web dashboard + face recognition security (Current)
- 🚧 **v1.0**: Public release — packaging, onboarding, hardening

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details.

---

## 💖 Credits

Built with love by a developer who got tired of interrupted downloads 💪

**Tech Stack**: Python • OpenCV • DeepFace • psutil • Streamlit • Go (WebSocket server) • Next.js • pytest • colorlog • PyYAML

**Special Thanks**: Everyone who's had their PC sleep mid-compile 😅
