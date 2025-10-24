"""
Web Dashboard Module
Real-time monitoring and control interface for Senthium
"""

from .server import create_app, socketio

__all__ = ['create_app', 'socketio']
