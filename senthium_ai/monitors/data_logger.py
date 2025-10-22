"""
Data Logger & Labeler module for telemetry collection and dataset creation.
Logs system telemetry with human labels during data collection sessions.
"""
import csv
import os
import time
import logging
from datetime import datetime
from typing import Optional, Dict, List
from pathlib import Path
import psutil

logger = logging.getLogger(__name__)


class DataLogger:
    """
    Logs system telemetry with task labels for training dataset creation.
    
    Features logged:
    - CPU usage (mean, std, max per core)
    - Memory usage
    - Network I/O rates
    - Disk I/O rates
    - Process information
    - Battery status
    - Input activity
    - Task labels and timestamps
    """
    
    CSV_HEADERS = [
        'timestamp',
        'cpu_mean',
        'cpu_std',
        'cpu_max',
        'cpu_per_core',
        'mem_percent',
        'net_rx_rate',
        'net_tx_rate',
        'disk_read_rate',
        'disk_write_rate',
        'process_count',
        'top_proc_name',
        'top_proc_cpu',
        'top_proc_mem',
        'io_wait',
        'time_since_last_input',
        'battery_percent',
        'plugged_bool',
        'user_present',
        'task_label',
        'time_remaining_minutes',
        'session_id',
        'notes'
    ]
    
    def __init__(self, output_dir: str = 'data/raw', sampling_interval: float = 5.0):
        """
        Initialize data logger.
        
        Args:
            output_dir: Directory to save CSV files
            sampling_interval: Time between samples in seconds
        """
        self.output_dir = Path(output_dir)
        self.sampling_interval = sampling_interval
        self.current_file = None
        self.csv_writer = None
        self.file_handle = None
        
        # Previous network/disk counters for rate calculation
        self.prev_net_counters = None
        self.prev_disk_counters = None
        self.prev_time = None
        
        # Current session info
        self.session_id = None
        self.task_label = 'unknown'
        self.time_remaining_minutes = 0.0
        self.user_present = False
        self.notes = ''
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"DataLogger initialized - output: {self.output_dir}")
    
    def start_session(self, session_id: str, task_label: str = 'unknown', 
                     time_remaining_minutes: float = 0.0, user_present: bool = False,
                     notes: str = '') -> str:
        """
        Start a new logging session.
        
        Args:
            session_id: Unique identifier for this session
            task_label: Type of task (idle, download, render, training, transfer, etc.)
            time_remaining_minutes: Expected time remaining for task
            user_present: Whether user is physically present
            notes: Additional notes about the session
            
        Returns:
            Path to the created CSV file
        """
        self.session_id = session_id
        self.task_label = task_label
        self.time_remaining_minutes = time_remaining_minutes
        self.user_present = user_present
        self.notes = notes
        
        # Create filename with timestamp and session ID
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"session_{session_id}_{timestamp}.csv"
        self.current_file = self.output_dir / filename
        
        # Open file and create CSV writer
        self.file_handle = open(self.current_file, 'w', newline='')
        self.csv_writer = csv.DictWriter(self.file_handle, fieldnames=self.CSV_HEADERS)
        self.csv_writer.writeheader()
        self.file_handle.flush()
        
        # Reset counters
        self.prev_net_counters = psutil.net_io_counters()
        self.prev_disk_counters = psutil.disk_io_counters()
        self.prev_time = time.time()
        
        logger.info(f"Started session '{session_id}' - task: {task_label}, file: {self.current_file}")
        return str(self.current_file)
    
    def log_sample(self) -> Dict:
        """
        Log a single telemetry sample.
        
        Returns:
            Dictionary containing the logged data
        """
        if not self.csv_writer:
            raise RuntimeError("No active session. Call start_session() first.")
        
        current_time = time.time()
        
        # CPU metrics
        cpu_percents = psutil.cpu_percent(interval=0.1, percpu=True)
        cpu_mean = sum(cpu_percents) / len(cpu_percents) if cpu_percents else 0.0
        cpu_std = (sum((x - cpu_mean) ** 2 for x in cpu_percents) / len(cpu_percents)) ** 0.5 if cpu_percents else 0.0
        cpu_max = max(cpu_percents) if cpu_percents else 0.0
        
        # Memory
        mem = psutil.virtual_memory()
        
        # Network I/O rates
        net_counters = psutil.net_io_counters()
        time_delta = current_time - self.prev_time
        net_rx_rate = (net_counters.bytes_recv - self.prev_net_counters.bytes_recv) / time_delta if time_delta > 0 else 0
        net_tx_rate = (net_counters.bytes_sent - self.prev_net_counters.bytes_sent) / time_delta if time_delta > 0 else 0
        
        # Disk I/O rates
        disk_counters = psutil.disk_io_counters()
        disk_read_rate = (disk_counters.read_bytes - self.prev_disk_counters.read_bytes) / time_delta if time_delta > 0 else 0
        disk_write_rate = (disk_counters.write_bytes - self.prev_disk_counters.write_bytes) / time_delta if time_delta > 0 else 0
        
        # Process information
        processes = list(psutil.process_iter(['name', 'cpu_percent', 'memory_percent']))
        process_count = len(processes)
        
        # Find top process by CPU
        top_proc = max(processes, key=lambda p: p.info['cpu_percent'] or 0, default=None)
        top_proc_name = top_proc.info['name'] if top_proc else 'none'
        top_proc_cpu = top_proc.info['cpu_percent'] if top_proc else 0.0
        top_proc_mem = top_proc.info['memory_percent'] if top_proc else 0.0
        
        # I/O wait (approximate using CPU stats)
        io_wait = psutil.cpu_times_percent().iowait if hasattr(psutil.cpu_times_percent(), 'iowait') else 0.0
        
        # Time since last input (placeholder - difficult to track cross-platform)
        time_since_last_input = 0  # Would need platform-specific implementation
        
        # Battery status
        battery = psutil.sensors_battery()
        battery_percent = battery.percent if battery else 100.0
        plugged_bool = battery.power_plugged if battery else True
        
        # Create row
        row = {
            'timestamp': datetime.now().isoformat(),
            'cpu_mean': round(cpu_mean, 2),
            'cpu_std': round(cpu_std, 2),
            'cpu_max': round(cpu_max, 2),
            'cpu_per_core': ','.join(str(round(p, 1)) for p in cpu_percents),
            'mem_percent': round(mem.percent, 2),
            'net_rx_rate': round(net_rx_rate, 0),
            'net_tx_rate': round(net_tx_rate, 0),
            'disk_read_rate': round(disk_read_rate, 0),
            'disk_write_rate': round(disk_write_rate, 0),
            'process_count': process_count,
            'top_proc_name': top_proc_name,
            'top_proc_cpu': round(top_proc_cpu, 2),
            'top_proc_mem': round(top_proc_mem, 2),
            'io_wait': round(io_wait, 2),
            'time_since_last_input': time_since_last_input,
            'battery_percent': round(battery_percent, 1),
            'plugged_bool': 1 if plugged_bool else 0,
            'user_present': 1 if self.user_present else 0,
            'task_label': self.task_label,
            'time_remaining_minutes': round(self.time_remaining_minutes, 2),
            'session_id': self.session_id,
            'notes': self.notes
        }
        
        # Write to CSV
        self.csv_writer.writerow(row)
        self.file_handle.flush()
        
        # Update counters
        self.prev_net_counters = net_counters
        self.prev_disk_counters = disk_counters
        self.prev_time = current_time
        
        return row
    
    def update_labels(self, task_label: Optional[str] = None,
                     time_remaining_minutes: Optional[float] = None,
                     user_present: Optional[bool] = None,
                     notes: Optional[str] = None):
        """
        Update labels for subsequent samples.
        
        Args:
            task_label: New task label
            time_remaining_minutes: Updated time remaining
            user_present: Updated presence status
            notes: Updated notes
        """
        if task_label is not None:
            self.task_label = task_label
        if time_remaining_minutes is not None:
            self.time_remaining_minutes = time_remaining_minutes
        if user_present is not None:
            self.user_present = user_present
        if notes is not None:
            self.notes = notes
        
        logger.debug(f"Updated labels - task: {self.task_label}, remaining: {self.time_remaining_minutes}min")
    
    def end_session(self):
        """End the current logging session and close the file."""
        if self.file_handle:
            self.file_handle.close()
            self.file_handle = None
            self.csv_writer = None
            logger.info(f"Ended session '{self.session_id}' - saved to {self.current_file}")
        
        self.session_id = None
    
    def run_continuous(self, duration_seconds: Optional[float] = None):
        """
        Run continuous logging for a specified duration.
        
        Args:
            duration_seconds: Duration to log (None for infinite)
        """
        if not self.csv_writer:
            raise RuntimeError("No active session. Call start_session() first.")
        
        start_time = time.time()
        sample_count = 0
        
        try:
            while True:
                # Log sample
                self.log_sample()
                sample_count += 1
                
                # Check duration
                if duration_seconds and (time.time() - start_time) >= duration_seconds:
                    logger.info(f"Completed logging - {sample_count} samples collected")
                    break
                
                # Wait for next sample
                time.sleep(self.sampling_interval)
                
        except KeyboardInterrupt:
            logger.info(f"Logging interrupted - {sample_count} samples collected")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.end_session()


def main():
    """CLI interface for data logging."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Senthium AI Data Logger')
    parser.add_argument('--output', '-o', default='data/raw', help='Output directory')
    parser.add_argument('--interval', '-i', type=float, default=5.0, help='Sampling interval (seconds)')
    parser.add_argument('--session-id', '-s', required=True, help='Session identifier')
    parser.add_argument('--task', '-t', default='unknown', help='Task label (idle/download/render/training/transfer)')
    parser.add_argument('--duration', '-d', type=float, help='Duration in seconds (infinite if not specified)')
    parser.add_argument('--time-remaining', '-r', type=float, default=0.0, help='Expected time remaining (minutes)')
    parser.add_argument('--user-present', '-p', action='store_true', help='User is present')
    parser.add_argument('--notes', '-n', default='', help='Additional notes')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create logger and start session
    logger = DataLogger(output_dir=args.output, sampling_interval=args.interval)
    
    try:
        filepath = logger.start_session(
            session_id=args.session_id,
            task_label=args.task,
            time_remaining_minutes=args.time_remaining,
            user_present=args.user_present,
            notes=args.notes
        )
        
        print(f"\n{'='*60}")
        print(f"Data Logger - Session: {args.session_id}")
        print(f"{'='*60}")
        print(f"Task: {args.task}")
        print(f"Output: {filepath}")
        print(f"Interval: {args.interval}s")
        print(f"Duration: {args.duration}s" if args.duration else "Duration: Continuous (Ctrl+C to stop)")
        print(f"{'='*60}\n")
        print("Logging telemetry... Press Ctrl+C to stop\n")
        
        # Run logging
        logger.run_continuous(duration_seconds=args.duration)
        
    finally:
        logger.end_session()
        print("\nLogging session completed.")


if __name__ == '__main__':
    main()
