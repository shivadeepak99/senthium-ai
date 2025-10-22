"""
Process monitoring module to detect active and critical background tasks.
"""
import psutil
import time
from typing import List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class ProcessMonitor:
    """Monitor system processes to identify active and critical tasks."""
    
    # Critical process indicators
    CRITICAL_PROCESS_NAMES = [
        'python', 'node', 'java', 'gcc', 'make', 'cargo', 'docker',
        'npm', 'pip', 'gradle', 'maven', 'rustc', 'go', 'ruby',
        'backup', 'rsync', 'tar', 'gzip', 'ffmpeg', 'convert'
    ]
    
    def __init__(self, cpu_threshold: float = 5.0, check_interval: float = 1.0):
        """
        Initialize process monitor.
        
        Args:
            cpu_threshold: CPU usage percentage threshold for active processes
            check_interval: Time interval in seconds between checks
        """
        self.cpu_threshold = cpu_threshold
        self.check_interval = check_interval
        self.process_history: Dict[int, List[float]] = {}
        
    def get_active_processes(self) -> List[Dict]:
        """
        Get list of currently active processes with relevant metrics.
        
        Returns:
            List of dictionaries containing process information
        """
        active_processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 
                                         'status', 'create_time']):
            try:
                pinfo = proc.info
                cpu_percent = pinfo['cpu_percent']
                
                # Consider a process active if it's using significant CPU
                if cpu_percent and cpu_percent > self.cpu_threshold:
                    process_data = {
                        'pid': pinfo['pid'],
                        'name': pinfo['name'],
                        'cpu_percent': cpu_percent,
                        'memory_percent': pinfo['memory_percent'],
                        'status': pinfo['status'],
                        'uptime': time.time() - pinfo['create_time'],
                        'is_critical': self._is_critical_process(pinfo['name'])
                    }
                    active_processes.append(process_data)
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
                
        return active_processes
    
    def _is_critical_process(self, process_name: str) -> bool:
        """
        Determine if a process is critical based on its name.
        
        Args:
            process_name: Name of the process
            
        Returns:
            True if the process is considered critical
        """
        process_name_lower = process_name.lower()
        return any(critical in process_name_lower for critical in self.CRITICAL_PROCESS_NAMES)
    
    def get_system_metrics(self) -> Dict:
        """
        Get overall system metrics.
        
        Returns:
            Dictionary containing system-wide metrics
        """
        return {
            'cpu_percent': psutil.cpu_percent(interval=0.1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_io': psutil.disk_io_counters(),
            'network_io': psutil.net_io_counters(),
            'active_process_count': len([p for p in psutil.process_iter() 
                                        if p.status() == psutil.STATUS_RUNNING])
        }
    
    def extract_features(self) -> Tuple[List[float], Dict]:
        """
        Extract features for ML model prediction.
        
        Returns:
            Tuple of (feature vector, raw data dictionary)
        """
        active_processes = self.get_active_processes()
        system_metrics = self.get_system_metrics()
        
        # Calculate aggregate features
        total_cpu = sum(p['cpu_percent'] for p in active_processes)
        total_memory = sum(p['memory_percent'] for p in active_processes)
        critical_count = sum(1 for p in active_processes if p['is_critical'])
        avg_uptime = (sum(p['uptime'] for p in active_processes) / len(active_processes) 
                     if active_processes else 0)
        
        # Feature vector for ANN
        features = [
            system_metrics['cpu_percent'],
            system_metrics['memory_percent'],
            len(active_processes),
            critical_count,
            total_cpu,
            total_memory,
            avg_uptime / 3600.0,  # Convert to hours
            system_metrics['active_process_count']
        ]
        
        raw_data = {
            'active_processes': active_processes,
            'system_metrics': system_metrics,
            'critical_count': critical_count
        }
        
        return features, raw_data
