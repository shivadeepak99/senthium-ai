# 🔒 Senthium AI

<div align="center">

[![PyPI version](https://img.shields.io/badge/pypi-v1.0.0-blue.svg)](https://pypi.org/project/senthium-ai/)
[![Python](https://img.shields.io/badge/python-3.11+-green.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-purple.svg)](LICENSE)
[![GitHub](https://img.shields.io/badge/github-shivadeepak99%2Fsenthium--ai-black.svg)](https://github.com/shivadeepak99/senthium-ai)

**Privacy-First Face Recognition Security System**

*Monitor your computer during long-running tasks. Get alerted if someone else sits at your desk.*

**🔐 100% Local • 🚫 No Cloud • 💜 Open Source**

[Quick Install](#-installation) • [Features](#-features) • [Usage](#-usage) • [Privacy](#-privacy-commitment)

</div>

---

## 🎯 The Problem

You're rendering a video (3 hours), training a model (8 hours), or downloading a large file (overnight).

**The Dilemma:**
- 🔓 Leave PC unlocked → Anyone can access your work
- 🔒 Lock the screen → Task pauses/fails
- 😴 Let it sleep → Download interrupted

**Senthium AI solves this:**
- ✅ Task keeps running (screen stays unlocked)
- ✅ You get INSTANT alerts if someone else sits at your desk
- ✅ Camera snapshots capture who accessed your PC
- ✅ Auto-lock (optional) after unauthorized detection

---

## ✨ Features

### 🧠 AI-Powered Security
- **Deep Learning Face Recognition** (FaceNet CNN)
- **Real-time Detection** (OpenCV DNN)
- **Multi-face Support** (detect multiple people)
- **Dynamic Training** (1-minute video enrollment)

### 📢 Smart Alerts
- **Discord Webhooks** (instant notifications)
- **Email** (SMTP - Gmail, Outlook, etc.)
- **Desktop Notifications** (Windows/Mac/Linux)
- **Snapshots** (photo evidence of intruders)

### 🎨 Modern Web UI
- **Streamlit Dashboard** (beautiful, responsive)
- **Face Enrollment** (webcam or photo upload)
- **Live Monitoring** (real-time status)
- **Complete Settings** (no YAML editing needed)

### 🤖 Background Daemon
- **24/7 Monitoring** (runs silently)
- **Low Resource** (< 50MB RAM, < 1% CPU)
- **Auto-start** (launch on boot)
- **Failsafe Timer** (prevents infinite lock)

### 🛡️ Privacy-First Design
- **100% Local Processing** (no cloud uploads)
- **Encrypted Snapshots** (optional)
- **You Control the Data** (delete anytime)
- **Open Source** (audit the code yourself)

---

## 📦 Installation

```bash
pip install senthium-ai
```
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
That's it! Now launch the web interface:

```bash
senthium-gui
```

Or start the background daemon:

```bash
senthium-daemon
```

---

## 🎯 Usage

### 1. Launch Web Interface

```bash
senthium-gui
```

Browser opens automatically at `http://localhost:8501`

### 2. Enroll Your Face

- Go to **"👤 Face Enrollment"** tab
- Click **"Capture from Webcam"** (or upload photo)
- Enter your name
- Click **"Enroll Face"**

### 3. Start Monitoring

- Go to **"🛡️ Security"** tab
- Click **"Start Daemon"**
- Leave your PC! You'll get alerts if someone else sits down.

### 4. Configure Alerts (Optional)

- Go to **"⚙️ Settings"** tab
- Add Discord webhook URL
- Configure email (SMTP)
- Set auto-lock behavior

---

## 🔐 Privacy Commitment

**Senthium AI is 100% local. No cloud. Ever.**

✅ All face data stored on YOUR machine only  
✅ No telemetry, no phone-home, no tracking  
✅ You control when monitoring is active  
✅ Open source - audit the code yourself  
✅ Snapshots encrypted at rest (optional)  

**Use Case:** Personal computer security during unattended tasks  
**NOT for:** Surveillance, tracking others, workplace monitoring without consent

**By design, Senthium runs on localhost only. Your privacy = our priority.**

---

## 📚 Documentation

- **Full Guide:** See [CSE311_PROJECT_REPORT.md](CSE311_PROJECT_REPORT.md)
- **PyPI Publishing:** See [PYPI_PUBLISH_GUIDE.md](PYPI_PUBLISH_GUIDE.md)
- **Jupyter Demo:** See [Senthium_AI_Complete_Demo.ipynb](Senthium_AI_Complete_Demo.ipynb)

---

## 🛠️ Requirements

- **Python:** 3.11 or higher
- **Webcam:** Any USB/built-in camera
- **OS:** Windows, macOS, or Linux
- **RAM:** 4GB minimum (8GB recommended)
- **Storage:** 2GB for models and dependencies

---

## 🤝 Contributing

Contributions welcome! This is an open-source project.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

Built for CSE 311 - Artificial Intelligence (2025)

**Technologies:**
- **DeepFace** (Face recognition)
- **OpenCV** (Computer vision)
- **TensorFlow** (Deep learning)
- **Streamlit** (Web interface)

**Pre-trained Model:**
- FaceNet (trained on VGGFace2 dataset)

---

## 📧 Contact

**Developer:** Shanigaram Shivadeepak  
**Email:** shivadeepak.dev@gmail.com  
**GitHub:** [@shivadeepak99](https://github.com/shivadeepak99)  
**Repository:** [senthium-ai](https://github.com/shivadeepak99/senthium-ai)

---

<div align="center">

**Made with 💜 for developers, creators, and privacy-conscious users**

⭐ Star this repo if you find it useful!

</div>
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
- ✅ **v0.4**: IPC + CLI wrapper + daemon management (Current)
- 🚧 **v0.5**: systemd/Windows service integration
- 🚧 **v0.6**: GUI configuration tool
- 🚧 **v1.0**: Public release

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

**Tech Stack**: Python • psutil • pytest • colorlog • PyYAML

**Special Thanks**: Everyone who's had their PC sleep mid-compile 😅
