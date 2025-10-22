"""
Senthium AI - Intelligent Task-Aware Lock System
"""
from .lock_manager import LockStateManager
from .monitors import ProcessMonitor
from .monitors.data_logger import DataLogger
from .models import TaskPredictor
from .controllers import FuzzyLockController
from .controllers.lock_controller import LockController
from .detectors import FaceDetector
from .utils import FeatureExtractor

__version__ = '1.0.0'
__all__ = [
    'LockStateManager',
    'ProcessMonitor',
    'DataLogger',
    'TaskPredictor',
    'FuzzyLockController',
    'LockController',
    'FaceDetector',
    'FeatureExtractor'
]
