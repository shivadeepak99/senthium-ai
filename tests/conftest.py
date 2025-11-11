# Add src directory to Python path
import sys
import os
from pathlib import Path

# Get project root (parent of conftest.py location)
project_root = Path(__file__).parent
src_path = project_root / "src"

# Add src to Python path if not already there
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Enable IPC for integration tests
os.environ['SENTHIUM_ENABLE_IPC'] = 'true'
