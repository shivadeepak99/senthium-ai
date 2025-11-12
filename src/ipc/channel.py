"""
Cross-platform IPC channel for daemon-CLI communication.

Handles platform-specific communication mechanisms:
- Unix Domain Sockets (Linux/macOS): /tmp/senthium.sock
- Named Pipes (Windows): \\\\.\\pipe\\senthium

Protocol: JSON messages with command/response structure
"""

import json
import logging
import platform
import socket
import os
import time
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Platform detection
IS_WINDOWS = platform.system() == "Windows"

# Initialize Windows-specific imports
# pyright: reportOptionalMemberAccess=false
# type: ignore - pywin32 optional dependency, suppress all type warnings
win32pipe = None  # type: ignore
win32file = None  # type: ignore
win32event = None  # type: ignore
pywintypes = None  # type: ignore

if IS_WINDOWS:
    try:
        import win32pipe  # type: ignore
        import win32file  # type: ignore
        import win32event  # type: ignore
        import pywintypes  # type: ignore
    except ImportError as e:
        # Windows-only dependencies - will fail on Linux/macOS or if pywin32 not installed
        logger.warning(f"Failed to import Windows-specific modules: {e}")
        logger.warning("Install pywin32 for IPC support: pip install pywin32")


class IPCMessage:
    """Serializable IPC message format"""
    
    def __init__(self, command: str, data: Optional[Dict[str, Any]] = None):
        """
        Create IPC message.
        
        Args:
            command: Command type (ACQUIRE_LOCK, RELEASE_LOCK, STATUS, etc.)
            data: Optional command data
        """
        self.command = command
        self.data = data or {}
        
    def to_json(self) -> str:
        """Serialize to JSON string"""
        return json.dumps({
            "command": self.command,
            "data": self.data
        })
    
    @staticmethod
    def from_json(json_str: str) -> "IPCMessage":
        """Deserialize from JSON string"""
        obj = json.loads(json_str)
        return IPCMessage(obj["command"], obj.get("data", {}))
    
    def __repr__(self) -> str:
        return f"IPCMessage(command='{self.command}', data={self.data})"


class IPCResponse:
    """IPC response format"""
    
    def __init__(self, success: bool, message: str = "", data: Optional[Dict[str, Any]] = None):
        """
        Create IPC response.
        
        Args:
            success: Whether command succeeded
            message: Human-readable message
            data: Optional response data
        """
        self.success = success
        self.message = message
        self.data = data or {}
        
    def to_json(self) -> str:
        """Serialize to JSON string"""
        return json.dumps({
            "success": self.success,
            "message": self.message,
            "data": self.data
        })
    
    @staticmethod
    def from_json(json_str: str) -> "IPCResponse":
        """Deserialize from JSON string"""
        obj = json.loads(json_str)
        return IPCResponse(obj["success"], obj.get("message", ""), obj.get("data", {}))
    
    def __repr__(self) -> str:
        return f"IPCResponse(success={self.success}, message='{self.message}', data={self.data})"


# ============================================================================
# Unix Socket Implementation (Linux/macOS)
# ============================================================================

class UnixSocketServer:
    """Unix domain socket server for daemon"""
    
    def __init__(self, socket_path: str = "/tmp/senthium.sock"):
        """
        Initialize Unix socket server.
        
        Args:
            socket_path: Path to socket file
        """
        self.socket_path = socket_path
        self.socket: Optional[socket.socket] = None
        
    def start(self) -> None:
        """Start listening on socket"""
        # Remove existing socket file
        if os.path.exists(self.socket_path):
            os.unlink(self.socket_path)
            
        # Create Unix socket
        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.socket.bind(self.socket_path)
        self.socket.listen(5)
        
        # Set non-blocking mode for accept() (won't block daemon loop)
        self.socket.setblocking(False)
        
        # Restrict permissions to current user only
        os.chmod(self.socket_path, 0o600)
        
        logger.info(f"IPC server listening on {self.socket_path}")
        
    def accept_connection(self) -> Optional[socket.socket]:
        """
        Accept incoming connection (non-blocking).
        
        Returns:
            Client socket if connection available, None otherwise
        """
        if not self.socket:
            return None
            
        try:
            client_socket, _ = self.socket.accept()
            return client_socket
        except BlockingIOError:
            # No connection available
            return None
        except Exception as e:
            logger.error(f"Error accepting connection: {e}")
            return None
    
    def receive_message(self, client_socket: socket.socket) -> Optional[IPCMessage]:
        """
        Receive message from client.
        
        Args:
            client_socket: Connected client socket
            
        Returns:
            Parsed IPCMessage or None on error
        """
        try:
            # Receive data (max 4KB)
            data = client_socket.recv(4096)
            if not data:
                return None
                
            message_str = data.decode("utf-8")
            return IPCMessage.from_json(message_str)
        except Exception as e:
            logger.error(f"Error receiving message: {e}")
            return None
    
    def send_response(self, client_socket: socket.socket, response: IPCResponse) -> bool:
        """
        Send response to client.
        
        Args:
            client_socket: Connected client socket
            response: Response to send
            
        Returns:
            True if sent successfully
        """
        try:
            response_str = response.to_json()
            client_socket.sendall(response_str.encode("utf-8"))
            return True
        except Exception as e:
            logger.error(f"Error sending response: {e}")
            return False
    
    def stop(self) -> None:
        """Stop server and cleanup"""
        if self.socket:
            self.socket.close()
            
        if os.path.exists(self.socket_path):
            os.unlink(self.socket_path)
            
        logger.info("IPC server stopped")


class UnixSocketClient:
    """Unix domain socket client for CLI"""
    
    def __init__(self, socket_path: str = "/tmp/senthium.sock", timeout: float = 5.0):
        """
        Initialize Unix socket client.
        
        Args:
            socket_path: Path to socket file
            timeout: Connection timeout in seconds
        """
        self.socket_path = socket_path
        self.timeout = timeout
        
    def send_command(self, message: IPCMessage) -> IPCResponse:
        """
        Send command to daemon and get response.
        
        Args:
            message: Command message
            
        Returns:
            Response from daemon
            
        Raises:
            ConnectionError: If cannot connect to daemon
        """
        # Check if socket exists
        if not os.path.exists(self.socket_path):
            raise ConnectionError(
                "Daemon not running. Start daemon first: senthiumd --daemon"
            )
        
        # Connect to daemon
        client_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client_socket.settimeout(self.timeout)
        
        try:
            client_socket.connect(self.socket_path)
            
            # Send message
            message_str = message.to_json()
            client_socket.sendall(message_str.encode("utf-8"))
            
            # Receive response
            data = client_socket.recv(4096)
            response_str = data.decode("utf-8")
            
            return IPCResponse.from_json(response_str)
            
        except socket.timeout:
            raise ConnectionError("Daemon did not respond in time")
        except Exception as e:
            raise ConnectionError(f"Failed to communicate with daemon: {e}")
        finally:
            client_socket.close()


# ============================================================================
# Named Pipe Implementation (Windows)
# ============================================================================

class NamedPipeServer:
    """Windows named pipe server for daemon"""
    
    def __init__(self, pipe_name: str = r"\\.\pipe\senthium"):
        """
        Initialize named pipe server.
        
        Args:
            pipe_name: Name of the pipe
        """
        self.pipe_name = pipe_name
        self.pipe_handle = None
        
    def start(self) -> None:
        """Start listening on named pipe"""
        print(f"[DEBUG PIPE] start() called, pipe_name={self.pipe_name}")
        
        if win32pipe is None or win32file is None:
            print("[DEBUG PIPE] ERROR: pywin32 not available!")
            raise RuntimeError("pywin32 not available. Install with: pip install pywin32")
        
        print("[DEBUG PIPE] Creating named pipe...")
        
        # Create named pipe in blocking mode with timeout
        # PIPE_WAIT + timeout is recommended over PIPE_NOWAIT on Windows
        # type: ignore on entire call due to pywin32 type stubs issues
        try:
            self.pipe_handle = win32pipe.CreateNamedPipe(  # type: ignore
                self.pipe_name,
                win32pipe.PIPE_ACCESS_DUPLEX,  # type: ignore
                win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_READMODE_MESSAGE | win32pipe.PIPE_WAIT,  # type: ignore
                win32pipe.PIPE_UNLIMITED_INSTANCES,  # type: ignore
                4096,  # Out buffer size
                4096,  # In buffer size
                100,   # Timeout in milliseconds (100ms for polling)
                None   # Security attributes (default)  # type: ignore
            )
            print(f"[DEBUG PIPE] Pipe handle created: {self.pipe_handle}")
            logger.info(f"IPC server listening on {self.pipe_name}")
            print(f"[DEBUG PIPE] Success! Listening on {self.pipe_name}")
        except Exception as e:
            print(f"[DEBUG PIPE] FAILED to create pipe: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def accept_connection(self) -> bool:
        """
        Try to connect pipe to client (non-blocking).
        
        Returns:
            True if client connected
        """
        if not self.pipe_handle:
            return False
            
        try:
            # Non-blocking connect (will return immediately)
            win32pipe.ConnectNamedPipe(self.pipe_handle, None)  # type: ignore
            return True
        except pywintypes.error as e:  # type: ignore
            if e.args[0] == 535:  # ERROR_PIPE_CONNECTED
                return True
            elif e.args[0] in [232, 233]:  # ERROR_NO_DATA, ERROR_PIPE_NOT_CONNECTED
                return False
            else:
                # Other errors - not connected
                return False
    
    def receive_message(self) -> Optional[IPCMessage]:
        """
        Receive message from client (with 100ms timeout).
        Pipe was created with 100ms timeout so this won't block forever.
        
        Returns:
            Parsed IPCMessage or None if no message/timeout
        """
        if not self.pipe_handle:
            return None
            
        try:
            # Blocking read with timeout (pipe created with 100ms timeout)
            result, data = win32file.ReadFile(self.pipe_handle, 4096)  # type: ignore
            
            if result == 0 and data:  # Success
                message_str = data.decode("utf-8")
                return IPCMessage.from_json(message_str)
                
        except pywintypes.error as e:  # type: ignore
            # Common errors:
            # 109 = ERROR_BROKEN_PIPE (client disconnected)
            # 232 = ERROR_NO_DATA (timeout - no data available)
            # 536 = ERROR_IO_INCOMPLETE (operation incomplete)
            if e.args[0] not in [109, 232, 536]:
                logger.debug(f"Pipe read error ({e.args[0]}): {e}")
                
        except Exception as e:
            logger.error(f"Error receiving message: {e}")
                
        return None
    
    def send_response(self, response: IPCResponse) -> bool:
        """
        Send response to client.
        
        Args:
            response: Response to send
            
        Returns:
            True if sent successfully
        """
        if not self.pipe_handle:
            return False
            
        try:
            response_str = response.to_json()
            win32file.WriteFile(self.pipe_handle, response_str.encode("utf-8"))  # type: ignore
            win32file.FlushFileBuffers(self.pipe_handle)  # type: ignore
            return True
        except Exception as e:
            logger.error(f"Error sending response: {e}")
            return False
    
    def disconnect_client(self) -> None:
        """Disconnect current client and prepare for next connection"""
        if self.pipe_handle:
            try:
                # Disconnect the client
                win32pipe.DisconnectNamedPipe(self.pipe_handle)  # type: ignore
                logger.debug("Client disconnected, pipe ready for next connection")
            except Exception as e:
                logger.debug(f"Error disconnecting client: {e}")
                # On error, recreate the pipe
                self._recreate_pipe()
    
    def _recreate_pipe(self) -> None:
        """Recreate the named pipe (needed after errors)"""
        if self.pipe_handle:
            try:
                win32file.CloseHandle(self.pipe_handle)  # type: ignore
            except:
                pass
        
        # Recreate pipe with same settings
        try:
            self.pipe_handle = win32pipe.CreateNamedPipe(  # type: ignore
                self.pipe_name,
                win32pipe.PIPE_ACCESS_DUPLEX,  # type: ignore
                win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_READMODE_MESSAGE | win32pipe.PIPE_WAIT,  # type: ignore
                win32pipe.PIPE_UNLIMITED_INSTANCES,  # type: ignore
                4096,  # Out buffer size
                4096,  # In buffer size
                100,   # Timeout in milliseconds (100ms for polling)
                None   # Security attributes (default)  # type: ignore
            )
            logger.debug("Pipe recreated successfully")
        except Exception as e:
            logger.error(f"Failed to recreate pipe: {e}")
            self.pipe_handle = None
    
    def stop(self) -> None:
        """Stop server and cleanup"""
        if self.pipe_handle:
            try:
                # CRITICAL: Must disconnect before closing on Windows!
                # Otherwise pipe stays in half-connected state and blocks next test
                win32pipe.DisconnectNamedPipe(self.pipe_handle)  # type: ignore
            except:
                pass  # Might not be connected
            
            try:
                win32file.CloseHandle(self.pipe_handle)  # type: ignore
            except:
                pass
            
            self.pipe_handle = None
            
        logger.info("IPC server stopped")


class NamedPipeClient:
    """Windows named pipe client for CLI"""
    
    def __init__(self, pipe_name: str = r"\\.\pipe\senthium", timeout: float = 5.0):
        """
        Initialize named pipe client.
        
        Args:
            pipe_name: Name of the pipe
            timeout: Connection timeout in seconds
        """
        self.pipe_name = pipe_name
        self.timeout = timeout
        
    def send_command(self, message: IPCMessage) -> IPCResponse:
        """
        Send command to daemon and get response.
        
        Args:
            message: Command message
            
        Returns:
            Response from daemon
            
        Raises:
            ConnectionError: If cannot connect to daemon
        """
        try:
            # Wait for pipe to be available
            timeout_ms = int(self.timeout * 1000)
            win32pipe.WaitNamedPipe(self.pipe_name, timeout_ms)  # type: ignore
            
            # Open pipe
            pipe_handle = win32file.CreateFile(  # type: ignore
                self.pipe_name,
                win32file.GENERIC_READ | win32file.GENERIC_WRITE,  # type: ignore
                0,  # No sharing
                None,  # Default security
                win32file.OPEN_EXISTING,  # type: ignore
                0,  # Default attributes
                None  # No template
            )
            
            try:
                # Set message mode (pywin32 type stubs are incomplete)
                win32pipe.SetNamedPipeHandleState(  # type: ignore
                    pipe_handle,  # type: ignore
                    win32pipe.PIPE_READMODE_MESSAGE,  # type: ignore
                    None,
                    None
                )
                
                # Send message
                message_str = message.to_json()
                win32file.WriteFile(pipe_handle, message_str.encode("utf-8"))  # type: ignore
                
                # Receive response
                result, data = win32file.ReadFile(pipe_handle, 4096)  # type: ignore
                response_str = data.decode("utf-8")
                
                return IPCResponse.from_json(response_str)
                
            finally:
                win32file.CloseHandle(pipe_handle)  # type: ignore
                
        except pywintypes.error as e:  # type: ignore
            if e.args[0] == 2:  # ERROR_FILE_NOT_FOUND
                raise ConnectionError(
                    "Daemon not running. Start daemon first: senthiumd --daemon"
                )
            else:
                raise ConnectionError(f"Failed to communicate with daemon: {e}")


# ============================================================================
# Cross-Platform Abstraction
# ============================================================================

class IPCServer:
    """Cross-platform IPC server for daemon"""
    
    def __init__(self):
        """Initialize platform-specific IPC server"""
        if IS_WINDOWS:
            self.impl = NamedPipeServer()
        else:
            self.impl = UnixSocketServer()
            
        self.running = False
        
    def start(self) -> None:
        """Start IPC server"""
        self.impl.start()
        self.running = True
        
    def poll(self) -> Optional[tuple[IPCMessage, Any]]:
        """
        Poll for incoming messages (non-blocking).
        
        Returns:
            Tuple of (message, client_context) if message received, None otherwise
        """
        if IS_WINDOWS:
            # Windows named pipe
            impl = self.impl  # Type: NamedPipeServer
            if impl.accept_connection():  # type: ignore
                message = impl.receive_message()  # type: ignore
                if message:
                    return (message, None)  # No separate client context
            return None
        else:
            # Unix socket
            impl = self.impl  # Type: UnixSocketServer
            client_socket = impl.accept_connection()  # type: ignore
            if client_socket and isinstance(client_socket, socket.socket):
                message = impl.receive_message(client_socket)  # type: ignore
                if message:
                    return (message, client_socket)
                else:
                    client_socket.close()
            return None
    
    def send_response(self, response: IPCResponse, client_context: Any = None) -> bool:
        """
        Send response to client.
        
        Args:
            response: Response to send
            client_context: Client context from poll() (Unix socket only)
            
        Returns:
            True if sent successfully
        """
        if IS_WINDOWS:
            impl = self.impl  # Type: NamedPipeServer
            success = impl.send_response(response)  # type: ignore
            impl.disconnect_client()  # type: ignore
            return success
        else:
            impl = self.impl  # Type: UnixSocketServer
            if client_context and isinstance(client_context, socket.socket):
                success = impl.send_response(client_context, response)  # type: ignore
                client_context.close()
                return success
            return False
    
    def stop(self) -> None:
        """Stop IPC server"""
        self.running = False
        self.impl.stop()


class IPCClient:
    """Cross-platform IPC client for CLI"""
    
    def __init__(self, timeout: float = 5.0):
        """
        Initialize platform-specific IPC client.
        
        Args:
            timeout: Connection timeout in seconds
        """
        if IS_WINDOWS:
            self.impl = NamedPipeClient(timeout=timeout)
        else:
            self.impl = UnixSocketClient(timeout=timeout)
    
    def send_command(self, command: str, data: Optional[Dict[str, Any]] = None) -> IPCResponse:
        """
        Send command to daemon.
        
        Args:
            command: Command type
            data: Optional command data
            
        Returns:
            Response from daemon
            
        Raises:
            ConnectionError: If cannot connect to daemon
        """
        message = IPCMessage(command, data)
        return self.impl.send_command(message)
