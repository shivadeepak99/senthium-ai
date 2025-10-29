# 🚀 Quick Installation Guide - Senthium AI Security

## For End Users (Simple)

### 1. Clone or Download
```bash
git clone <repo-url> senthium-ai
cd senthium-ai
```

### 2. Install Dependencies
```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Install Senthium AI
pip install -e .
```

### 3. Run!
```bash
# Option A: Streamlit GUI (Easy!)
streamlit run streamlit_app.py

# Option B: CLI (Advanced)
senthium --help
senthium enroll --name Owner --image face.jpg
senthium start  # Start daemon
```

---

## For Developers

### Install in Development Mode
```bash
# Clone repo
git clone <repo-url> senthium-ai
cd senthium-ai

# Create venv
python -m venv venv311
venv311\Scripts\activate  # Windows
source venv311/bin/activate  # Linux/Mac

# Install in editable mode with dev dependencies
pip install -e .[dev]

# Run tests (if available)
pytest
```

### Project Structure
```
senthium-ai-modern/
├── src/
│   ├── vision/         # Face detection & recognition
│   │   ├── detector.py        # OpenCV DNN face detector
│   │   ├── recognizer.py      # Face matching
│   │   ├── security_manager.py # Main coordinator
│   │   └── camera.py          # Webcam interface
│   ├── daemon/         # Background daemon
│   ├── alerts/         # Notification system
│   ├── cli/            # Command-line interface
│   └── utils/          # Utilities
├── config/             # Configuration files
├── models/             # DNN model weights (auto-downloaded)
├── streamlit_app.py    # GUI dashboard
├── setup.py            # Package configuration
├── requirements.txt    # Python dependencies
└── README.md           # Documentation
```

---

## Dependencies (Auto-Installed)

### Core
- `opencv-python` - Face detection & image processing
- `numpy` - Numerical operations
- `pillow` - Image handling

### GUI
- `streamlit` - Web dashboard

### System
- `psutil` - Process management
- `pywin32` - Windows integration
- `pyyaml` - Config files

### Optional
- `discord-webhook` - Discord alerts
- `win10toast` - Windows notifications

---

## Configuration

### Config File: `config/config.yaml`
```yaml
camera_index: 0  # Webcam device (0 = default)
detection_model: 'dnn'  # OpenCV DNN
recognition_tolerance: 0.6  # Lower = stricter
check_interval_seconds: 10  # How often to check
enable_security: false  # Master on/off switch
```

### Enrolled Faces: `config/faces/authorized.json`
Stores face encodings for authorized users. Created automatically on first enrollment.

---

## Troubleshooting

### Issue: Webcam not detected
**Solution:** Make sure no other app is using the webcam. Try changing `camera_index` in config.

### Issue: OpenCV DNN models not downloading
**Solution:** Download manually from:
- https://raw.githubusercontent.com/opencv/opencv/master/samples/dnn/face_detector/deploy.prototxt
- https://raw.githubusercontent.com/opencv/opencv_3rdparty/dnn_samples_face_detector_20170830/res10_300x300_ssd_iter_140000.caffemodel

Place in `models/` directory.

### Issue: Import errors
**Solution:** Make sure you activated the virtual environment and ran `pip install -e .`

### Issue: "senthium command not found"
**Solution:** Run `pip install -e .` to install the CLI entry point.

---

## Usage Examples

### Enroll Owner Face
```bash
# Via CLI
senthium enroll --name "John Doe" --image john_face.jpg

# Via Streamlit
# 1. Open http://localhost:8501
# 2. Go to "Enrollment" page
# 3. Upload photo
```

### Manual Security Check
```bash
# Via CLI
senthium security check

# Via Streamlit
# Click "Run Security Check Now" button
```

### Start Background Daemon
```bash
# Daemon will automatically check for unauthorized faces
senthium start

# Check status
senthium status

# Stop daemon
senthium stop
```

### Enable/Disable Security
```bash
# Via CLI
senthium security enable
senthium security disable

# Via Streamlit
# Use toggle in Settings page
```

---

## Advanced: Custom Face Recognition Model

Want better face embeddings? Replace the simple histogram+DCT in `detector.py` with:
- **FaceNet** (128-dim embeddings)
- **ArcFace** (state-of-the-art accuracy)
- **DeepFace** (multiple models)

```python
# Example: Using FaceNet
from deepface import DeepFace

def extract_face_encodings_advanced(image, face_locations):
    encodings = []
    for (top, right, bottom, left) in face_locations:
        face = image[top:bottom, left:right]
        # Use FaceNet model
        embedding = DeepFace.represent(
            face, 
            model_name='Facenet', 
            enforce_detection=False
        )[0]['embedding']
        encodings.append(np.array(embedding))
    return encodings
```

---

## Support

- **Docs:** See `REFACTOR_COMPLETE.md` for technical details
- **Issues:** Open on GitHub
- **Questions:** Check README.md

---

**Made with 💖 by your AI waifu dev**  
**Version:** 0.6.0  
**Status:** Production Ready
