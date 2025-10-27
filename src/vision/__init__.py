"""
AI Vision & Security Module

Provides camera monitoring, face detection, and unauthorized access detection.
Your waifu is watching your PC babe! 💖🔒
"""

from .camera import CameraMonitor
from .detector import FaceDetector
from .recognizer import FaceRecognizer

__all__ = ['CameraMonitor', 'FaceDetector', 'FaceRecognizer']
