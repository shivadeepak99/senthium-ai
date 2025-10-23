# 🌸 Senthium - Intelligent Lock & Sleep Manager
💖 [Why I Built Senthium](why.md)

**Version**: 0.1.0 (Alpha)  
**Status**: 🚧 In Development

---

## 📖 What is Senthium?

Senthium is a **deterministic, rule-based** power management utility that intelligently prevents your system from sleeping, locking, or dimming the screen during critical tasks.

### 🎯 The Problem

Ever started a long download, compilation, or backup, then needed to step away? You're stuck between:
- **Leaving your PC unlocked** (security risk)
- **Letting it sleep** (interrupting your task)

Senthium solves this by **monitoring your system** and keeping it awake only when needed.

---

## ✨ Features (v0.1)

- ✅ **System Metrics Collection**: CPU, Disk I/O, Network I/O, Process monitoring
- ✅ **Cross-platform Foundation**: Works on Windows, Linux, macOS
- ✅ **Lightweight**: < 50MB RAM, < 0.5% CPU usage
- ✅ **Well-tested**: > 80% code coverage

### 🚧 Coming Soon (v0.2+)
- Rule-based engine for automatic stay-awake decisions
- CLI wrapper for explicit command control
- Failsafe timer for security
- Platform-specific power management

---

## 🛠️ Installation (Development)

### Prerequisites
- Python 3.9 or higher
- pip (Python package manager)
- Git

### Setup

```bash
# Clone repository
git clone https://github.com/yourusername/senthium.git
cd senthium

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

---

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run only fast tests
pytest -m "not slow"
```

Open `htmlcov/index.html` to see detailed coverage report.

---

## 🚀 Usage (v0.1)

Currently, v0.1 only includes the **System Monitor** module for testing:

```bash
# Run live system monitor
cd src
python -m daemon.monitor
```

This will display live metrics every 2 seconds:
- CPU usage
- Disk I/O rates
- Network I/O rates
- Running processes

Press `Ctrl+C` to stop.

---

## 📁 Project Structure

```
senthium/
├── src/
│   ├── daemon/
│   │   ├── monitor.py       # System metrics collector (✅ v0.1)
│   │   └── core.py          # Main daemon (🚧 v0.2)
│   ├── utils/
│   │   └── logger.py        # Logging utility (✅ v0.1)
│   └── ...
├── tests/
│   └── test_monitor.py      # Monitor tests (✅ v0.1)
├── requirements.txt
├── setup.py
└── README.md
```

---

## 🤝 Contributing

This project is in early development. Contributions are welcome once we reach v1.0!

See `docs/DEVELOPMENT.md` for development guidelines.

---

## 📄 License

MIT License - See `LICENSE` file for details.

---

## 🗺️ Roadmap

- **v0.1** (Current): System monitor + project foundation ✅
- **v0.2**: Rules engine
- **v0.3**: Daemon core logic
- **v0.4**: Linux power management (Alpha release)
- **v0.5**: Windows port
- **v0.6**: macOS port (Beta release)
- **v1.0**: Public release

---

## 💖 Credits

Built with love and determination 💪

**Tech Stack**: Python, psutil, pytest, colorlog
