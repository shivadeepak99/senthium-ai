# 📖 Senthium User Guide

Welcome to **Senthium** - your intelligent stay-awake assistant! 🌸

This guide will help you install, configure, and use Senthium effectively.

---

## 📑 Table of Contents

1. [What is Senthium?](#what-is-senthium)
2. [Installation](#installation)
3. [Quick Start](#quick-start)
4. [Configuration Guide](#configuration-guide)
5. [Usage Examples](#usage-examples)
6. [Troubleshooting](#troubleshooting)
7. [FAQ](#faq)

---

## 🎯 What is Senthium?

Senthium is a **smart power management daemon** that prevents your computer from sleeping, locking, or dimming the screen during important tasks.

### The Problem

Ever started a long download, compilation, or backup and then needed to step away? You're stuck between:
- **Leaving your PC unlocked** (security risk)
- **Letting it sleep** (interrupting your task)

### The Solution

Senthium watches your system and **only** keeps it awake when:
- Specific processes are running (e.g., build tools, downloads)
- CPU usage is high (e.g., rendering, encoding)
- Disk I/O is active (e.g., large file transfers)
- Network activity is high (e.g., downloads, uploads)
- You explicitly tell it to (wrapper mode)

### Key Features

✅ **Automatic Mode** - Define rules, Senthium handles the rest  
✅ **Explicit Mode** - Run specific commands with guaranteed stay-awake  
✅ **Failsafe Timer** - Never stays awake indefinitely (security!)  
✅ **Hot Reload** - Update config without restarting  
✅ **Cross-platform** - Windows, Linux, macOS  

---

## 🛠️ Installation

### Prerequisites

- **Python 3.9 or higher**
- **pip** (Python package manager)
- **Git** (for source installation)

### Install from Source

```bash
# Clone the repository
git clone https://github.com/yourusername/senthium.git
cd senthium

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install Senthium
pip install -e .
```

### Verify Installation

```bash
senthium --help
```

You should see the help message! 🎉

---

## 🚀 Quick Start

### 1. Create Your Configuration

```bash
# Copy example config
cp config/config.example.yaml config/config.yaml

# Edit with your favorite editor
nano config/config.yaml  # Linux/Mac
notepad config/config.yaml  # Windows
```

### 2. Start the Daemon

```bash
senthium start --config config/config.yaml
```

### 3. Check Status

```bash
senthium status --verbose
```

### 4. Use Explicit Mode

Run a command with guaranteed stay-awake:

```bash
senthium --stay-awake "npm run build"
```

### 5. Stop the Daemon

```bash
senthium stop
```

---

## ⚙️ Configuration Guide

### Configuration File Location

- **Default**: `config/config.yaml`
- **Custom**: Specify with `--config path/to/config.yaml`

### Basic Structure

```yaml
senthium:
  version: "0.4"
  
  # Global settings
  poll_interval: 5              # Check every 5 seconds
  max_awake_duration: 14400     # 4 hours max (failsafe)
  log_level: "INFO"             # DEBUG, INFO, WARNING, ERROR
  
  # Rules (OR logic - any match = stay awake)
  rules:
    - name: "Build Tools"
      type: "process"
      processes: ["npm", "cargo", "make", "cmake"]
      enabled: true
```

### Rule Types

#### 1. Process Rules

Stay awake when specific programs are running.

```yaml
- name: "Development Tools"
  type: "process"
  processes:
    - "code"         # VS Code
    - "python"       # Python interpreter
    - "node"         # Node.js
    - "docker"       # Docker
  enabled: true
```

**Matching:**
- Case-insensitive
- Partial match (e.g., "chrome" matches "chrome.exe")

#### 2. CPU Rules

Stay awake when CPU usage is high.

```yaml
- name: "Heavy CPU Load"
  type: "cpu"
  threshold: 50      # Above 50% CPU
  duration: 30       # For at least 30 seconds
  enabled: true
```

#### 3. Disk Rules

Stay awake during heavy disk activity.

```yaml
- name: "Disk Activity"
  type: "disk"
  read_mbps: 10      # Reading at 10+ MB/s
  write_mbps: 10     # Writing at 10+ MB/s
  duration: 20       # For at least 20 seconds
  enabled: true
```

#### 4. Network Rules

Stay awake during downloads/uploads.

```yaml
- name: "Large Download"
  type: "network"
  download_mbps: 5   # Downloading at 5+ MB/s
  upload_mbps: 0     # Don't care about upload
  duration: 15       # For at least 15 seconds
  enabled: true
```

#### 5. Combined Rules

Stay awake when ALL conditions match (AND logic).

```yaml
- name: "Active Development"
  type: "combined"
  conditions:
    - type: "process"
      processes: ["code", "python"]
    - type: "cpu"
      threshold: 20
  enabled: true
```

---

## 💡 Usage Examples

### Example 1: Developer Workstation

**Scenario:** Keep system awake while coding, building, or running tests.

```yaml
senthium:
  version: "0.4"
  poll_interval: 5
  max_awake_duration: 14400  # 4 hours
  
  rules:
    - name: "IDE Running"
      type: "process"
      processes:
        - "code"        # VS Code
        - "idea"        # IntelliJ
        - "pycharm"     # PyCharm
        - "vim"
      
    - name: "Build Tools"
      type: "process"
      processes:
        - "npm"
        - "cargo"
        - "make"
        - "cmake"
        - "gcc"
        - "g++"
        
    - name: "Docker Running"
      type: "process"
      processes: ["docker", "docker-compose"]
      
    - name: "Heavy Compilation"
      type: "cpu"
      threshold: 60
      duration: 30
```

**Start daemon:**
```bash
senthium start --config config/developer.yaml
```

### Example 2: Download Manager

**Scenario:** Keep awake during large downloads.

```yaml
senthium:
  version: "0.4"
  poll_interval: 10
  max_awake_duration: 28800  # 8 hours
  
  rules:
    - name: "Download Manager"
      type: "process"
      processes:
        - "utorrent"
        - "qbittorrent"
        - "aria2c"
        - "wget"
        - "curl"
        
    - name: "High Network Activity"
      type: "network"
      download_mbps: 2
      upload_mbps: 1
      duration: 30
```

### Example 3: Media Server

**Scenario:** Keep awake while streaming or transcoding.

```yaml
senthium:
  version: "0.4"
  poll_interval: 10
  max_awake_duration: 43200  # 12 hours
  
  rules:
    - name: "Media Server"
      type: "process"
      processes:
        - "plex"
        - "jellyfin"
        - "emby"
        
    - name: "Transcoding"
      type: "combined"
      conditions:
        - type: "process"
          processes: ["ffmpeg", "handbrake"]
        - type: "cpu"
          threshold: 40
```

### Example 4: Explicit Mode (No Daemon)

Run a specific command with guaranteed stay-awake:

```bash
# Long build
senthium --stay-awake "npm run build"

# Docker build
senthium --stay-awake "docker build -t myapp ."

# Large file transfer
senthium --stay-awake "rsync -avz /source /destination"

# Machine learning training
senthium --stay-awake "python train_model.py --epochs 100"

# Video rendering
senthium --stay-awake "ffmpeg -i input.mp4 -vcodec h264 output.mp4"
```

**How it works:**
1. Senthium acquires wrapper lock (highest priority)
2. Your command executes
3. System **guaranteed** to stay awake during execution
4. Lock released after command completes
5. Exit code preserved

---

## 🔧 Command Reference

### Daemon Management

```bash
# Start daemon
senthium start                              # Use default config
senthium start --config custom.yaml         # Custom config
senthium start --log-level DEBUG            # Verbose logging
senthium start --foreground                 # Don't detach (debugging)

# Stop daemon
senthium stop                               # Graceful shutdown
senthium stop --force                       # Force kill
senthium stop --timeout 30                  # Custom timeout

# Restart daemon
senthium restart                            # Stop + start
senthium restart --config new.yaml          # With new config

# Check status
senthium status                             # Quick status
senthium status --verbose                   # Detailed status
```

### Wrapper Mode

```bash
# Run command with stay-awake
senthium --stay-awake "your command here"

# Query daemon
senthium --status                           # Daemon status
senthium --info                             # Config & rules
senthium --reload                           # Reload config

# Logging
senthium --stay-awake "cmd" --log-level DEBUG
```

---

## 🐛 Troubleshooting

### Daemon Won't Start

**Problem:** `senthium start` fails

**Solutions:**
1. Check if already running: `senthium status`
2. Stop existing daemon: `senthium stop`
3. Validate config: Check `logs/senthium.log`
4. Try foreground mode: `senthium start --foreground --log-level DEBUG`

### Rules Not Matching

**Problem:** Daemon running but system still sleeps

**Solutions:**
1. Check if rules are enabled: `senthium --info`
2. Verify process names in task manager
3. Lower thresholds (CPU, disk, network)
4. Add duration to prevent false negatives
5. Check logs: `logs/senthium.log`

### Too Many False Positives

**Problem:** System stays awake when it shouldn't

**Solutions:**
1. Add `duration` to rules (require sustained condition)
2. Increase thresholds
3. Use `combined` rules for more specific matching
4. Disable unused rules

### Wrapper Mode Not Working

**Problem:** `senthium --stay-awake` fails

**Solutions:**
1. Ensure daemon is running: `senthium status`
2. Start daemon first: `senthium start`
3. Check for connection errors in output

### Config Validation Fails

**Problem:** "Configuration validation error"

**Solutions:**
1. Check YAML syntax (indentation!)
2. Verify version field: `version: "0.4"`
3. Ensure all required fields present
4. Check against schema: `config/config.schema.json`

### High CPU Usage

**Problem:** Senthium using too much CPU

**Solutions:**
1. Increase `poll_interval` (default: 5s)
2. Reduce number of process rules
3. Check for runaway rules

---

## ❓ FAQ

### Q: How much resources does Senthium use?

**A:** Very little! Typical usage:
- **CPU**: <0.5% during monitoring
- **Memory**: <50MB
- **Disk**: Minimal (logs only)

### Q: Is it safe to leave running?

**A:** Yes! The failsafe timer ensures it never stays awake indefinitely. Default max: 4 hours.

### Q: Can I use both modes simultaneously?

**A:** Yes! You can have:
- Daemon running in background (automatic mode)
- Use wrapper mode for specific commands
- Wrapper lock has highest priority

### Q: Does it work on Windows/Linux/macOS?

**A:** Yes! Senthium is cross-platform:
- **Windows**: Tested on Windows 10/11 ✅
- **Linux**: Tested on Ubuntu 22.04 ✅
- **macOS**: Coded but needs testing ⚠️

### Q: Can I reload config without restart?

**A:** Yes! Use `senthium --reload`

### Q: What happens if daemon crashes?

**A:** System returns to normal power management. No permanent changes made.

### Q: Can I run multiple instances?

**A:** No. PID file prevents multiple daemon instances.

### Q: How do I update Senthium?

**A:**
```bash
cd senthium
git pull
pip install -e .
senthium restart
```

### Q: Where are logs stored?

**A:** `logs/senthium.log` (rotates at 10MB, keeps 5 backups)

### Q: Can I contribute?

**A:** Absolutely! See `docs/CONTRIBUTING.md`

---

## 🎓 Best Practices

1. **Start Simple** - Begin with basic process rules, add complexity as needed
2. **Use Duration** - Add duration to avoid false positives from brief spikes
3. **Test Rules** - Use `--info` and check logs to verify rules work
4. **Reasonable Failsafe** - Keep `max_awake_duration` under 8 hours for security
5. **Monitor Logs** - Check `logs/senthium.log` occasionally
6. **Disable Unused Rules** - Set `enabled: false` instead of deleting
7. **Use Explicit Mode** - For critical one-off commands, use wrapper mode

---

## 📚 Additional Resources

- **Config Reference**: `docs/CONFIG_REFERENCE.md`
- **Installation Guide**: `docs/INSTALL.md`
- **Development Docs**: `docs/development/`
- **GitHub Issues**: Report bugs and request features
- **Example Configs**: `config/examples/`

---

## 💖 Need Help?

- 📖 **Documentation**: Start here!
- 🐛 **Bug Reports**: GitHub Issues
- 💬 **Questions**: GitHub Discussions
- 📧 **Email**: your.email@example.com

---

**Happy staying awake!** 🌸✨

*Last Updated: October 24, 2025*
