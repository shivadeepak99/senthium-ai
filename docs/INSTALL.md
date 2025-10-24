# Installation Guide

This guide covers platform-specific installation instructions for Senthium.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Quick Install (All Platforms)](#quick-install-all-platforms)
- [Windows Installation](#windows-installation)
- [Linux Installation](#linux-installation)
- [macOS Installation](#macos-installation)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

**All Platforms:**
- Python 3.9 or higher
- pip (Python package manager)
- Git (for cloning repository)

**Platform-Specific:**
- **Windows**: PowerShell 5.1+ or PowerShell Core 7+
- **Linux**: systemd (optional, for service installation)
- **macOS**: Xcode Command Line Tools

---

## Quick Install (All Platforms)

```bash
# Clone repository
git clone https://github.com/yourusername/senthium.git
cd senthium

# Install with pip
pip install -e .

# Verify installation
senthium --version
```

That's it! Jump to [Platform-Specific Setup](#platform-specific-setup) for advanced configurations.

---

## Windows Installation

### Option 1: PowerShell Install (Recommended)

```powershell
# Clone repository
git clone https://github.com/yourusername/senthium.git
cd senthium

# Create virtual environment (optional but recommended)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install Senthium
pip install -e .

# Verify installation
senthium --version
```

### Option 2: Install as Windows Service (Advanced)

**Note**: Windows service integration is planned for v0.5. For now, use Task Scheduler:

1. Open **Task Scheduler**
2. Create New Task:
   - **Name**: Senthium Daemon
   - **Trigger**: At log on
   - **Action**: Start a program
     - **Program**: `C:\Path\To\Python\Scripts\senthium.exe`
     - **Arguments**: `start`
   - **Conditions**: Uncheck "Start only if on AC power"
3. Save and test with "Run" button

### Troubleshooting Windows

**Issue: "senthium: command not found"**
```powershell
# Add Python Scripts to PATH
$env:Path += ";$env:LOCALAPPDATA\Programs\Python\Python39\Scripts"
# Or find your Python Scripts directory:
python -m site --user-site
# Navigate up to Scripts folder and add to PATH
```

**Issue: PowerShell execution policy**
```powershell
# Allow script execution
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Issue: Permission errors**
```powershell
# Run PowerShell as Administrator or install to user directory
pip install --user -e .
```

---

## Linux Installation

### Option 1: Standard Install

```bash
# Clone repository
git clone https://github.com/yourusername/senthium.git
cd senthium

# Create virtual environment (optional)
python3 -m venv venv
source venv/bin/activate

# Install Senthium
pip install -e .

# Verify installation
senthium --version
```

### Option 2: Install as systemd Service (Recommended)

**Step 1: Install Senthium**
```bash
cd senthium
pip install -e .
```

**Step 2: Create systemd service file**

Create `/etc/systemd/system/senthium.service`:
```ini
[Unit]
Description=Senthium Intelligent Power Management Daemon
After=network.target

[Service]
Type=forking
User=your-username
WorkingDirectory=/home/your-username/senthium
ExecStart=/usr/local/bin/senthium start
ExecStop=/usr/local/bin/senthium stop
ExecReload=/usr/local/bin/senthium restart
Restart=on-failure
RestartSec=10s

[Install]
WantedBy=multi-user.target
```

**Step 3: Enable and start service**
```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service (start on boot)
sudo systemctl enable senthium

# Start service now
sudo systemctl start senthium

# Check status
sudo systemctl status senthium

# View logs
journalctl -u senthium -f
```

### Troubleshooting Linux

**Issue: "senthium: command not found"**
```bash
# Add to PATH in ~/.bashrc or ~/.zshrc
export PATH="$HOME/.local/bin:$PATH"
source ~/.bashrc
```

**Issue: Permission errors**
```bash
# Install to user directory
pip install --user -e .
```

**Issue: systemd service fails**
```bash
# Check logs
journalctl -u senthium -n 50

# Verify paths in service file
which senthium

# Test manually first
senthium start
senthium status
```

---

## macOS Installation

### Option 1: Standard Install

```bash
# Install Xcode Command Line Tools (if not installed)
xcode-select --install

# Clone repository
git clone https://github.com/yourusername/senthium.git
cd senthium

# Create virtual environment (optional)
python3 -m venv venv
source venv/bin/activate

# Install Senthium
pip install -e .

# Verify installation
senthium --version
```

### Option 2: Homebrew Install (Coming Soon)

```bash
# Planned for v1.0
brew tap yourusername/senthium
brew install senthium
```

### Option 3: Install as launchd Service (Advanced)

**Step 1: Install Senthium**
```bash
cd senthium
pip install -e .
```

**Step 2: Create launchd plist**

Create `~/Library/LaunchAgents/com.senthium.daemon.plist`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.senthium.daemon</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/senthium</string>
        <string>start</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
    <key>StandardOutPath</key>
    <string>/tmp/senthium.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/senthium.err</string>
</dict>
</plist>
```

**Step 3: Load service**
```bash
# Load service
launchctl load ~/Library/LaunchAgents/com.senthium.daemon.plist

# Unload service
launchctl unload ~/Library/LaunchAgents/com.senthium.daemon.plist
```

### Troubleshooting macOS

**Issue: "senthium: command not found"**
```bash
# Add to PATH in ~/.zshrc (default shell on macOS)
export PATH="$HOME/.local/bin:$PATH"
source ~/.zshrc
```

**Issue: Permission denied**
```bash
# Install to user directory
pip install --user -e .

# Or use sudo (not recommended)
sudo pip install -e .
```

**Issue: launchd service fails**
```bash
# Check logs
cat /tmp/senthium.log
cat /tmp/senthium.err

# Verify paths
which senthium

# Test manually first
senthium start
senthium status
```

---

## Platform-Specific Setup

### Create Configuration

**All Platforms:**
```bash
# Use example config as starting point
cp config/examples/minimal.yaml config/config.yaml

# Edit config file
# Windows:
notepad config/config.yaml
# Linux/macOS:
nano config/config.yaml
```

See [docs/USER_GUIDE.md](USER_GUIDE.md) for configuration details.

### Verify Installation

```bash
# Check version
senthium --version

# Start daemon
senthium start

# Check status
senthium status

# View live info
senthium --info

# Stop daemon
senthium stop
```

---

## Troubleshooting

### Common Issues

**1. Import Errors**
```bash
# Missing dependencies
pip install -r requirements.txt

# Verify installation
pip show senthium
```

**2. Config File Not Found**
```bash
# Default location: ./config/config.yaml
# Create from example:
cp config/examples/minimal.yaml config/config.yaml
```

**3. Daemon Won't Start**
```bash
# Check logs (default: ./logs/senthium.log)
tail -f logs/senthium.log

# Check if already running
senthium status

# Force stop and restart
senthium stop
senthium start
```

**4. PID File Errors**
```bash
# Stale PID file (daemon crashed)
rm /tmp/senthium.pid  # Linux/macOS
del %TEMP%\senthium.pid  # Windows

# Then restart
senthium start
```

**5. Permission Errors**
```bash
# Install to user directory
pip install --user -e .

# Or run with appropriate permissions
# Linux/macOS: sudo senthium start
# Windows: Run PowerShell as Administrator
```

---

## Uninstallation

**Remove Senthium:**
```bash
# Uninstall package
pip uninstall senthium

# Remove configuration (optional)
rm -rf config/  # Linux/macOS
rmdir /s config  # Windows

# Remove logs (optional)
rm -rf logs/  # Linux/macOS
rmdir /s logs  # Windows
```

**Remove systemd Service (Linux):**
```bash
sudo systemctl stop senthium
sudo systemctl disable senthium
sudo rm /etc/systemd/system/senthium.service
sudo systemctl daemon-reload
```

**Remove launchd Service (macOS):**
```bash
launchctl unload ~/Library/LaunchAgents/com.senthium.daemon.plist
rm ~/Library/LaunchAgents/com.senthium.daemon.plist
```

---

## Next Steps

- 📖 Read the [User Guide](USER_GUIDE.md) for complete usage instructions
- 🎨 Check [Example Configurations](../config/examples/) for common scenarios
- 🐛 Report issues on [GitHub Issues](https://github.com/yourusername/senthium/issues)

---

**Need Help?** Open an issue or check the [FAQ](USER_GUIDE.md#faq) in the User Guide.
