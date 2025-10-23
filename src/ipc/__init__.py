"""
IPC module - Inter-process communication between daemon and CLI.

Provides cross-platform IPC mechanisms for daemon-CLI communication:
- Unix Domain Sockets (Linux/macOS)
- Named Pipes (Windows)
"""

from .channel import IPCServer, IPCClient, IPCMessage, IPCResponse

__all__ = ["IPCServer", "IPCClient", "IPCMessage", "IPCResponse"]
