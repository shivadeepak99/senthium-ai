"""
Senthium AI - Intelligent Task-Aware Lock System
"""
from .lock_manager import LockStateManager
from .monitors import ProcessMonitor
from .models import TaskPredictor
from .controllers import FuzzyLockController
from .detectors import FaceDetector

__version__ = '1.0.0'
__all__ = [
    'LockStateManager',
    'ProcessMonitor',
    'TaskPredictor',
    'FuzzyLockController',
    'FaceDetector'
]
