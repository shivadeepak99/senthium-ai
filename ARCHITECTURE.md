# Senthium AI Architecture

This document describes the technical architecture of the Senthium AI intelligent lock system.

## System Overview

Senthium AI is a Python-based intelligent lock system that combines multiple technologies to make smart decisions about when to lock or keep a computer awake based on:
- Active system processes
- Task criticality (detected via neural network)
- System resource usage
- Optional user presence (via face detection)

## Component Architecture

### 1. Process Monitor (`senthium_ai/monitors/process_monitor.py`)

**Purpose**: Monitors system processes to identify active and critical tasks.

**Key Features**:
- Tracks CPU and memory usage per process
- Identifies critical processes (compilers, build tools, backup utilities)
- Extracts system-wide metrics (CPU, memory, disk I/O, network I/O)
- Generates feature vectors for ML model

**Critical Process Patterns**:
- Development tools: python, node, java, gcc, make, cargo, rustc
- Build systems: npm, pip, gradle, maven
- Media processing: ffmpeg, convert
- Backup tools: backup, rsync, tar, gzip

### 2. Task Predictor - ANN (`senthium_ai/models/task_predictor.py`)

**Purpose**: Neural network that predicts task criticality level.

**Architecture**:
- Input layer: 8 features
  - System CPU percentage
  - System memory percentage
  - Number of active processes
  - Number of critical processes
  - Total CPU of active processes
  - Total memory of active processes
  - Average process uptime
  - Active process count
- Hidden layer: 16 neurons with ReLU activation
- Output layer: 3 classes (idle, moderate, critical) with softmax

**Training**:
- Uses backpropagation with cross-entropy loss
- Xavier weight initialization
- Configurable learning rate and epochs

**Output Classes**:
- **Idle** (0): No significant activity
- **Moderate** (1): Normal user activity
- **Critical** (2): Important background tasks running

### 3. Fuzzy Logic Controller (`senthium_ai/controllers/fuzzy_controller.py`)

**Purpose**: Determines optimal lock state using fuzzy logic.

**Input Variables**:
1. **Task Criticality** (0-100%): From ANN prediction
   - Low (0-50)
   - Medium (20-80)
   - High (50-100)

2. **System Load** (0-100%): Max of CPU/memory usage
   - Low (0-40)
   - Medium (20-80)
   - High (60-100)

3. **Presence Confidence** (0-100%): User presence probability
   - Absent (0-40)
   - Uncertain (20-80)
   - Present (60-100)

**Output Variable**:
- **Lock State** (0-100): Mapped to three states
  - Stay Awake (0-30)
  - Dim (31-70)
  - Full Lock (71-100)

**Fuzzy Rules** (Examples):
- IF criticality=high AND load=high THEN stay_awake
- IF criticality=low AND presence=absent THEN full_lock
- IF criticality=medium AND presence=present THEN stay_awake

### 4. Face Detector (`senthium_ai/detectors/face_detector.py`)

**Purpose**: Optional presence verification using computer vision.

**Technology**: OpenCV with Haar Cascade classifiers

**Features**:
- Face detection via webcam
- Confidence scoring based on face size
- Multi-sample averaging for stability
- Graceful degradation when disabled

**Confidence Calculation**:
- Larger faces = higher confidence
- Multiple detections = higher confidence
- Minimum 60% confidence when face detected
- 50% neutral confidence when disabled

### 5. Lock State Manager (`senthium_ai/lock_manager.py`)

**Purpose**: Coordinates all components and applies lock states.

**Responsibilities**:
- Initialize and manage all subsystems
- Coordinate data flow between components
- Apply lock states to the operating system
- Handle state transitions with stability buffer
- Provide callbacks for state changes

**State Stability**:
- Maintains history of last 5 state decisions
- Uses most common state to prevent flickering
- Ensures smooth transitions

**Platform Support**:
- **Linux**: xset, gnome-screensaver, xdg-screensaver, loginctl
- **macOS**: caffeinate, CGSession
- **Windows**: powercfg, rundll32

## Data Flow

```
1. Process Monitor
   ↓ (features)
2. Task Predictor (ANN)
   ↓ (task criticality)
3. Fuzzy Controller ← (system load)
   ↑ (presence confidence)
4. Face Detector
   ↓ (lock state decision)
5. Lock Manager
   ↓ (apply to OS)
6. System Lock State
```

## Configuration

### config.yaml Structure

```yaml
cpu_threshold: 5.0              # Process activity threshold
check_interval: 1.0             # Monitoring frequency
enable_face_detection: false    # Face detection toggle
camera_index: 0                 # Camera device
update_interval: 10             # Decision frequency
log_level: INFO                 # Logging verbosity
apply_lock_state: true          # Dry-run toggle
state_stability_samples: 5      # State history size
```

## Security Considerations

### Data Privacy
- All processing is local (no cloud/external services)
- Camera only accessed when explicitly enabled
- No data transmission or logging of sensitive info

### System Security
- Uses OS-native lock mechanisms
- No privilege escalation
- Graceful degradation on permission errors

### Code Security
- Input validation and sanitization
- Exception handling throughout
- No eval() or dynamic code execution
- Regular security scans (CodeQL)

## Performance

### Resource Usage
- **CPU**: <1% typical usage
- **Memory**: ~50-100 MB
- **Disk**: Minimal (logs only)
- **Network**: None

### Optimization
- Configurable check intervals
- Efficient process filtering
- Lazy initialization of optional components
- State caching to reduce computation

## Extensibility

### Adding New Critical Processes
Edit `CRITICAL_PROCESS_NAMES` in `process_monitor.py`

### Custom ML Models
Replace `TaskPredictor` class while maintaining same interface

### Additional Fuzzy Rules
Extend rules in `_setup_fuzzy_system()` method

### Platform-Specific Lock Methods
Add methods to `LockStateManager` for new platforms

## Testing

### Test Coverage
- Unit tests for each component
- Integration tests for data flow
- System tests for end-to-end behavior

### Test Files
- `test_senthium.py`: Automated test suite
- `example_demo.py`: Interactive demonstration
- Manual testing with `--dry-run` flag

## Future Enhancements

### Planned Features
- Machine learning model training on user data
- Configurable fuzzy rules via config file
- GUI for configuration and monitoring
- Plugin system for custom detectors
- Mobile app for remote monitoring

### Potential Improvements
- TensorFlow/PyTorch models
- Multiple face recognition
- Activity prediction
- Power consumption optimization
- Cloud backup of learning data

## Dependencies

### Core
- **numpy**: Numerical computing
- **psutil**: Process and system monitoring
- **scikit-fuzzy**: Fuzzy logic control
- **networkx**: Graph theory (required by scikit-fuzzy)

### Optional
- **opencv-python**: Face detection
- **scikit-learn**: ML utilities
- **pyyaml**: Configuration parsing

## Version History

- **1.0.0** (2025): Initial release
  - ANN task predictor
  - Fuzzy logic controller
  - Process monitoring
  - Optional face detection
  - Cross-platform support
