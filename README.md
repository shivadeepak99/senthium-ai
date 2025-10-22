# Senthium AI - Intelligent Task-Aware Lock System

An intelligent lock system that uses an Artificial Neural Network (ANN) to predict active/critical background tasks and a Fuzzy Logic controller to decide adaptive lock states (stay awake / dim / full lock), with optional face-based presence verification. Protects long-running processes while securing the machine.

## Features

- **🧠 ANN-based Task Prediction**: Uses a neural network to classify system activity into idle, moderate, or critical states
- **🎯 Fuzzy Logic Controller**: Intelligently decides lock states based on task criticality, system load, and user presence
- **📹 Optional Face Detection**: Verifies user presence via webcam for enhanced decision-making
- **🔒 Adaptive Lock States**:
  - **Stay Awake**: Keeps screen on during critical tasks (builds, backups, data processing)
  - **Dim**: Reduces screen brightness for moderate activity or uncertain presence
  - **Full Lock**: Locks the system when idle or user is absent
- **⚡ Process Monitoring**: Tracks CPU usage, memory, and identifies critical background processes
- **🖥️ Cross-Platform**: Supports Linux, macOS, and Windows

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Senthium AI System                       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   Process    │───>│     ANN      │    │    Face      │  │
│  │   Monitor    │    │   Predictor  │    │   Detector   │  │
│  └──────────────┘    └──────┬───────┘    └──────┬───────┘  │
│         │                    │                    │          │
│         └────────────────────┴────────────────────┘          │
│                              │                                │
│                    ┌─────────▼─────────┐                     │
│                    │  Fuzzy Logic      │                     │
│                    │  Controller       │                     │
│                    └─────────┬─────────┘                     │
│                              │                                │
│                    ┌─────────▼─────────┐                     │
│                    │  Lock State       │                     │
│                    │  Manager          │                     │
│                    └───────────────────┘                     │
│                              │                                │
│         ┌────────────────────┼────────────────────┐          │
│         │                    │                    │          │
│    ┌────▼────┐          ┌───▼────┐          ┌───▼────┐     │
│    │  Stay   │          │  Dim   │          │  Full  │     │
│    │  Awake  │          │ Screen │          │  Lock  │     │
│    └─────────┘          └────────┘          └────────┘     │
└─────────────────────────────────────────────────────────────┘
```

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager
- (Optional) Webcam for face detection

### Setup

1. Clone the repository:
```bash
git clone https://github.com/shivadeepak99/senthium-ai.git
cd senthium-ai
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. (Optional) Test the installation:
```bash
python senthium_ai.py --help
```

## Usage

### Basic Usage

Run with default configuration:
```bash
python senthium_ai.py
```

### Advanced Options

```bash
# Run in dry-run mode (doesn't apply lock states)
python senthium_ai.py --dry-run

# Enable face detection for presence verification
python senthium_ai.py --enable-face-detection

# Use custom configuration file
python senthium_ai.py --config my_config.yaml

# Set custom update interval (in seconds)
python senthium_ai.py --interval 5

# Enable verbose logging
python senthium_ai.py --verbose
```

### Configuration

Edit `config.yaml` to customize behavior:

```yaml
# Process monitoring settings
cpu_threshold: 5.0          # CPU usage threshold (%) to consider a process active
check_interval: 1.0         # Time interval (seconds) between checks

# Face detection settings
enable_face_detection: false  # Enable/disable face-based presence verification
camera_index: 0              # Camera device index (0 for default camera)

# Update frequency
update_interval: 10          # Seconds between lock state evaluations

# Logging
log_level: INFO             # DEBUG, INFO, WARNING, ERROR, CRITICAL
log_file: senthium_ai.log   # Log file path (null for console only)

# Lock behavior
apply_lock_state: true      # Actually apply lock states (false for dry-run)
state_stability_samples: 5  # Number of samples for state stability
```

## How It Works

### 1. Process Monitoring
The system continuously monitors:
- CPU usage per process
- Memory usage
- Process names to identify critical tasks (compilers, build tools, backup utilities, etc.)
- System-wide metrics

### 2. Task Prediction (ANN)
A neural network analyzes process features to classify activity:
- **Idle**: No significant activity
- **Moderate**: Normal user activity
- **Critical**: Important background tasks running (builds, backups, data processing)

Features used:
- System CPU percentage
- System memory percentage
- Number of active processes
- Number of critical processes
- Total CPU usage of active processes
- Average process uptime

### 3. Fuzzy Logic Decision
A fuzzy logic controller determines the optimal lock state based on:
- **Task Criticality** (from ANN): How important are current tasks?
- **System Load**: CPU and memory usage
- **User Presence** (optional): Is the user at the computer?

Fuzzy rules example:
- High criticality + High load → Stay Awake
- Medium criticality + User present → Stay Awake
- Low criticality + User absent → Full Lock

### 4. Lock State Application
The system applies one of three states:
- **Stay Awake**: Prevents screen sleep/lock during critical tasks
- **Dim**: Reduces brightness, allows sleep after timeout
- **Full Lock**: Immediately locks the screen

## Platform-Specific Behavior

### Linux
- Uses `xset` for screen management
- Supports `gnome-screensaver`, `xdg-screensaver`, or `loginctl` for locking

### macOS
- Uses `caffeinate` utility (recommended to run manually for stay awake)
- Uses CGSession for screen locking

### Windows
- Uses `powercfg` for power management
- Uses `rundll32` for workstation locking

## Use Cases

- **Software Development**: Keeps screen awake during long compilations
- **Data Processing**: Protects machine during ETL jobs or data analysis
- **Media Encoding**: Monitors video/audio encoding tasks
- **Backup Operations**: Prevents interruption of system backups
- **Remote Work**: Locks screen when you step away (with face detection)
- **Security**: Automatically secures workstation when idle

## Security Considerations

- Face detection is **optional** and runs locally (no cloud processing)
- All processing happens on your machine
- No data is transmitted externally
- Camera is only accessed when face detection is enabled
- Lock states are applied using OS-native commands

## Troubleshooting

### Camera Access Issues
If face detection fails:
```bash
# Test camera access
python -c "import cv2; print(cv2.VideoCapture(0).isOpened())"
```

### Lock Commands Not Working (Linux)
Install required utilities:
```bash
# For GNOME
sudo apt-get install gnome-screensaver

# For generic X11
sudo apt-get install xdg-utils
```

### Permission Issues
Some lock commands may require additional permissions. Run with appropriate privileges or configure your system's security settings.

## Development

### Project Structure
```
senthium-ai/
├── senthium_ai/
│   ├── __init__.py
│   ├── lock_manager.py          # Main coordinator
│   ├── models/
│   │   ├── __init__.py
│   │   └── task_predictor.py    # ANN model
│   ├── controllers/
│   │   ├── __init__.py
│   │   └── fuzzy_controller.py  # Fuzzy logic
│   ├── monitors/
│   │   ├── __init__.py
│   │   └── process_monitor.py   # Process tracking
│   └── detectors/
│       ├── __init__.py
│       └── face_detector.py     # Face detection
├── senthium_ai.py                # Main application
├── config.yaml                   # Configuration
├── requirements.txt              # Dependencies
└── README.md                     # Documentation
```

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

This project is open source and available under the MIT License.

## Acknowledgments

- Uses scikit-fuzzy for fuzzy logic control
- Uses OpenCV for face detection
- Uses psutil for process monitoring