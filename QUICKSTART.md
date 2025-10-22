# Senthium AI - Quick Start Guide

Get up and running with Senthium AI in 5 minutes!

## Installation

```bash
# Clone the repository
git clone https://github.com/shivadeepak99/senthium-ai.git
cd senthium-ai

# Install dependencies
pip install -r requirements.txt
```

## Basic Usage

### Run with Default Settings (Dry-Run)
```bash
python senthium_ai.py --dry-run
```

### Run with Face Detection
```bash
python senthium_ai.py --enable-face-detection
```

### Run in Production
```bash
# Remove --dry-run to actually apply lock states
python senthium_ai.py
```

## Quick Test

### 1. Test Components
```bash
python test_senthium.py
```
Expected output: `5 passed, 0 failed`

### 2. Run Demo
```bash
python example_demo.py
```
Shows how each component works independently.

### 3. Test Real System
```bash
python senthium_ai.py --dry-run --interval 5
```
Monitor your system for a few minutes (press Ctrl+C to stop).

## Understanding the Output

```
[06:02:18] State: Dim          | Task: critical | Load:  25.0% | Presence:  50.0% | Critical:  0 | Active:   0
           ^^^^^^^^^^           ^^^^^^^^^^^^^^   ^^^^^^^^^^^^^   ^^^^^^^^^^^^^^^^^   ^^^^^^^^^^^^^   ^^^^^^^^^^^^^
           Lock State           Task Level       System Load     User Presence       Critical Procs  Active Procs
```

### Lock States
- **Stay Awake**: Screen stays on (critical work running)
- **Dim**: Screen dims after timeout (moderate activity)
- **Full Lock**: Screen locks immediately (idle or user absent)

### Task Levels
- **idle**: No significant activity
- **moderate**: Normal usage
- **critical**: Important background tasks (builds, backups, etc.)

## Configuration

Edit `config.yaml` to customize:

```yaml
# How often to check system state (seconds)
update_interval: 10

# Enable/disable face detection
enable_face_detection: false

# Actually apply lock states (false = dry-run)
apply_lock_state: true

# Logging level (DEBUG, INFO, WARNING, ERROR)
log_level: INFO
```

## Common Commands

```bash
# Show help
python senthium_ai.py --help

# Dry-run with verbose logging
python senthium_ai.py --dry-run --verbose

# Quick checks every 5 seconds
python senthium_ai.py --dry-run --interval 5

# Custom config file
python senthium_ai.py --config my_config.yaml

# Enable face detection
python senthium_ai.py --enable-face-detection
```

## Troubleshooting

### Camera not working
```bash
# Test camera access
python -c "import cv2; print('Camera OK' if cv2.VideoCapture(0).isOpened() else 'Camera Failed')"
```

### Import errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Lock commands not working (Linux)
```bash
# Install required tools
sudo apt-get install xdg-utils gnome-screensaver
```

## Data Collection & Training (Advanced)

### Collect Training Data

```bash
# Interactive data collection demo
python demo_data_collection.py --mode interactive

# Or automated collection
python demo_data_collection.py --mode automated
```

### Extract Features

```bash
# Extract ML features from collected data
python -m senthium_ai.utils.feature_extractor data/raw -o data/processed/features.npz --normalize
```

### Train Model

```bash
# Train ANN model on your data
python train_model.py --data data/processed/features.npz --epochs 100 --output models/my_model.pkl
```

### Use Trained Model

Load your trained model in the predictor by modifying `senthium_ai/models/task_predictor.py`.

## Next Steps

1. ✅ Run the demo and tests
2. ✅ Try dry-run mode
3. ✅ Customize config.yaml
4. ✅ Enable face detection (optional)
5. ✅ Collect training data (advanced)
6. ✅ Train custom model (advanced)
7. ✅ Run in production

## Need Help?

- 📖 Full documentation: [README.md](README.md)
- 🏗️ Architecture details: [ARCHITECTURE.md](ARCHITECTURE.md)
- 🤝 Contributing: [CONTRIBUTING.md](CONTRIBUTING.md)
- 🐛 Report issues: [GitHub Issues](https://github.com/shivadeepak99/senthium-ai/issues)

## Example Workflow

```bash
# Morning: Start monitoring
python senthium_ai.py &

# System automatically:
# - Keeps screen on during builds
# - Dims screen when you're away briefly
# - Locks screen when you leave

# Evening: Stop monitoring
pkill -f senthium_ai.py
```

Happy monitoring! 🎉
