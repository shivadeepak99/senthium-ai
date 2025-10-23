"""
System Monitor Module
Collects system metrics using psutil for rule evaluation
"""

import psutil
import time
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class SystemMetrics:
    """Data class for system metrics snapshot"""
    timestamp: datetime
    cpu_percent: float
    disk_read_mbps: float
    disk_write_mbps: float
    net_sent_mbps: float
    net_recv_mbps: float
    processes: List[str]
    idle_time_seconds: float
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for logging/debugging"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'cpu_percent': round(self.cpu_percent, 2),
            'disk_read_mbps': round(self.disk_read_mbps, 2),
            'disk_write_mbps': round(self.disk_write_mbps, 2),
            'net_sent_mbps': round(self.net_sent_mbps, 2),
            'net_recv_mbps': round(self.net_recv_mbps, 2),
            'process_count': len(self.processes),
            'idle_time_seconds': round(self.idle_time_seconds, 1),
        }


class SystemMonitor:
    """
    Monitor system metrics for rule evaluation
    
    Uses psutil to collect CPU, disk, network, and process information.
    Calculates rates (MB/s) by comparing snapshots over time.
    """
    
    def __init__(self, poll_interval: float = 5.0):
        """
        Initialize system monitor
        
        Args:
            poll_interval: Time between polls in seconds (for rate calculations)
        """
        self.poll_interval = poll_interval
        self.logger = logging.getLogger(__name__)
        
        # Previous snapshots for rate calculation
        self._last_disk_io: Optional[psutil._common.sdiskio] = None
        self._last_net_io: Optional[psutil._common.snetio] = None
        self._last_poll_time: Optional[float] = None
        
        self.logger.info(f"SystemMonitor initialized (poll_interval={poll_interval}s)")
    
    def get_current_state(self) -> SystemMetrics:
        """
        Get current system state snapshot
        
        Returns:
            SystemMetrics object with all current metrics
        """
        current_time = time.time()
        
        # Calculate time delta for rates
        if self._last_poll_time:
            time_delta = current_time - self._last_poll_time
        else:
            time_delta = self.poll_interval
        
        self._last_poll_time = current_time
        
        # Take single snapshots for disk and net to keep deltas consistent
        current_disk = psutil.disk_io_counters()
        current_net = psutil.net_io_counters()
        
        # Gather all metrics using consistent snapshots
        metrics = SystemMetrics(
            timestamp=datetime.now(),
            cpu_percent=self._get_cpu_percent(),
            disk_read_mbps=self._calc_disk_read_mbps(current_disk, time_delta),
            disk_write_mbps=self._calc_disk_write_mbps(current_disk, time_delta),
            net_sent_mbps=self._calc_net_sent_mbps(current_net, time_delta),
            net_recv_mbps=self._calc_net_recv_mbps(current_net, time_delta),
            processes=self._get_process_list(),
            idle_time_seconds=self._get_idle_time(),
        )
        
        self.logger.debug(f"Metrics collected: {metrics.to_dict()}")
        return metrics
    
    def _get_cpu_percent(self) -> float:
        """Get system-wide CPU usage percentage (non-blocking)"""
        try:
            return psutil.cpu_percent(interval=0.0)
        except Exception:
            raise
    
    def _calc_disk_read_mbps(self, current_io: psutil._common.sdiskio, time_delta: float) -> float:
        """
        Calculate disk read rate in MB/s from snapshot
        
        Args:
            current_io: Current disk IO snapshot
            time_delta: Time since last measurement
            
        Returns:
            Read rate in MB/s
        """
        if self._last_disk_io is None:
            # No baseline yet - will be set after write calc
            return 0.0
        
        bytes_read = current_io.read_bytes - self._last_disk_io.read_bytes
        mbps = (bytes_read / time_delta) / (1024 * 1024)
        return max(0.0, mbps)
    
    def _calc_disk_write_mbps(self, current_io: psutil._common.sdiskio, time_delta: float) -> float:
        """
        Calculate disk write rate in MB/s from snapshot
        
        Args:
            current_io: Current disk IO snapshot
            time_delta: Time since last measurement
            
        Returns:
            Write rate in MB/s
        """
        if self._last_disk_io is None:
            self._last_disk_io = current_io
            return 0.0
        
        bytes_written = current_io.write_bytes - self._last_disk_io.write_bytes
        mbps = (bytes_written / time_delta) / (1024 * 1024)
        
        # Update baseline AFTER computing both read & write
        self._last_disk_io = current_io
        return max(0.0, mbps)
    
    def _calc_net_sent_mbps(self, current_io: psutil._common.snetio, time_delta: float) -> float:
        """
        Calculate network upload rate in MB/s from snapshot
        
        Args:
            current_io: Current network IO snapshot
            time_delta: Time since last measurement
            
        Returns:
            Upload rate in MB/s
        """
        if self._last_net_io is None:
            # No baseline yet - will be set after recv calc
            return 0.0
        
        bytes_sent = current_io.bytes_sent - self._last_net_io.bytes_sent
        mbps = (bytes_sent / time_delta) / (1024 * 1024)
        return max(0.0, mbps)
    
    def _calc_net_recv_mbps(self, current_io: psutil._common.snetio, time_delta: float) -> float:
        """
        Calculate network download rate in MB/s from snapshot
        
        Args:
            current_io: Current network IO snapshot
            time_delta: Time since last measurement
            
        Returns:
            Download rate in MB/s
        """
        if self._last_net_io is None:
            self._last_net_io = current_io
            return 0.0
        
        bytes_recv = current_io.bytes_recv - self._last_net_io.bytes_recv
        mbps = (bytes_recv / time_delta) / (1024 * 1024)
        
        # Update baseline AFTER computing both sent & recv
        self._last_net_io = current_io
        return max(0.0, mbps)
    
    def _get_process_list(self) -> List[str]:
        """
        Get list of all running process names
        
        Returns:
            List of process names (lowercase for case-insensitive matching)
        """
        processes = []
        for proc in psutil.process_iter(['name']):
            try:
                processes.append(proc.info['name'].lower())
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                # Process may have ended or we don't have permission
                pass
        
        return processes
    
    def _get_idle_time(self) -> float:
        """
        Get user idle time in seconds
        Platform-specific implementation
        
        Returns:
            Idle time in seconds (0.0 for now, will implement per-platform)
        """
        # TODO: Implement platform-specific idle time detection
        # - Windows: GetLastInputInfo via ctypes
        # - Linux: xprintidle or X11 (python-xlib) or Wayland
        # - macOS: IOKit/Quartz via pyobjc
        
        # For now, return 0 (will implement in later versions)
        return 0.0
    
    def process_is_running(self, process_name: str) -> bool:
        """
        Check if a specific process is running
        
        Args:
            process_name: Name of process to check (case-insensitive)
            
        Returns:
            True if process is running
        """
        process_name_lower = process_name.lower()
        current_processes = self._get_process_list()
        return process_name_lower in current_processes


# Example usage / testing
if __name__ == '__main__':
    from utils.logger import setup_logger
    
    # Setup logging
    logger = setup_logger('senthium.monitor', level='DEBUG')
    
    # Create monitor
    monitor = SystemMonitor(poll_interval=2.0)
    
    print("🔍 Senthium System Monitor - Live Metrics Test")
    print("=" * 60)
    print("Collecting metrics every 2 seconds. Press Ctrl+C to stop.\n")
    
    try:
        iteration = 1
        while True:
            metrics = monitor.get_current_state()
            
            print(f"\n📊 Iteration {iteration} - {metrics.timestamp.strftime('%H:%M:%S')}")
            print(f"  CPU: {metrics.cpu_percent:.1f}%")
            print(f"  Disk Read: {metrics.disk_read_mbps:.2f} MB/s")
            print(f"  Disk Write: {metrics.disk_write_mbps:.2f} MB/s")
            print(f"  Network Upload: {metrics.net_sent_mbps:.2f} MB/s")
            print(f"  Network Download: {metrics.net_recv_mbps:.2f} MB/s")
            print(f"  Running Processes: {len(metrics.processes)}")
            
            # Show some example processes
            example_procs = [p for p in metrics.processes if 'python' in p or 'chrome' in p or 'code' in p][:5]
            if example_procs:
                print(f"  Example Processes: {', '.join(example_procs)}")
            
            iteration += 1
            time.sleep(2.0)
            
    except KeyboardInterrupt:
        print("\n\n✅ Monitoring stopped. Monitor test complete!")
