"""
Feature extraction module for converting raw telemetry CSV to ML-ready features.
Reads raw CSV telemetry and converts it into fixed-length sequence windows.
"""
import csv
import numpy as np
from pathlib import Path
from typing import List, Tuple, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class FeatureExtractor:
    """
    Extracts features from raw telemetry CSV files for ML model training.
    
    Converts raw time-series data into fixed-length sequence windows with
    aggregated features suitable for neural network input.
    """
    
    # Task label mapping
    TASK_LABELS = {
        'idle': 0,
        'moderate': 1,
        'download': 1,
        'transfer': 1,
        'critical': 2,
        'render': 2,
        'training': 2,
        'compile': 2,
        'backup': 2,
        'unknown': 0
    }
    
    def __init__(self, window_size: int = 6, stride: int = 1):
        """
        Initialize feature extractor.
        
        Args:
            window_size: Number of samples per sequence window
            stride: Step size for sliding window (1 = no overlap, window_size = no overlap)
        """
        self.window_size = window_size
        self.stride = stride
    
    def load_csv(self, filepath: str) -> List[Dict]:
        """
        Load raw telemetry from CSV file.
        
        Args:
            filepath: Path to CSV file
            
        Returns:
            List of dictionaries containing telemetry samples
        """
        samples = []
        
        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convert numeric fields
                sample = {
                    'timestamp': row['timestamp'],
                    'cpu_mean': float(row['cpu_mean']),
                    'cpu_std': float(row['cpu_std']),
                    'cpu_max': float(row['cpu_max']),
                    'mem_percent': float(row['mem_percent']),
                    'net_rx_rate': float(row['net_rx_rate']),
                    'net_tx_rate': float(row['net_tx_rate']),
                    'disk_read_rate': float(row['disk_read_rate']),
                    'disk_write_rate': float(row['disk_write_rate']),
                    'process_count': int(row['process_count']),
                    'top_proc_name': row['top_proc_name'],
                    'top_proc_cpu': float(row['top_proc_cpu']),
                    'top_proc_mem': float(row['top_proc_mem']),
                    'io_wait': float(row.get('io_wait', 0.0)),
                    'time_since_last_input': float(row.get('time_since_last_input', 0.0)),
                    'battery_percent': float(row['battery_percent']),
                    'plugged_bool': int(row['plugged_bool']),
                    'user_present': int(row['user_present']),
                    'task_label': row['task_label'],
                    'time_remaining_minutes': float(row['time_remaining_minutes'])
                }
                samples.append(sample)
        
        logger.info(f"Loaded {len(samples)} samples from {filepath}")
        return samples
    
    def extract_window_features(self, window: List[Dict]) -> np.ndarray:
        """
        Extract aggregated features from a window of samples.
        
        Args:
            window: List of telemetry samples (length = window_size)
            
        Returns:
            Feature vector as numpy array
        """
        features = []
        
        # CPU features (mean, std, max across window)
        cpu_means = [s['cpu_mean'] for s in window]
        features.extend([
            np.mean(cpu_means),
            np.std(cpu_means),
            np.max(cpu_means)
        ])
        
        # Memory features
        mem_percents = [s['mem_percent'] for s in window]
        features.extend([
            np.mean(mem_percents),
            np.std(mem_percents),
            np.max(mem_percents)
        ])
        
        # Network I/O features (bytes/sec)
        net_rx = [s['net_rx_rate'] for s in window]
        net_tx = [s['net_tx_rate'] for s in window]
        features.extend([
            np.mean(net_rx),
            np.max(net_rx),
            np.mean(net_tx),
            np.max(net_tx)
        ])
        
        # Disk I/O features
        disk_read = [s['disk_read_rate'] for s in window]
        disk_write = [s['disk_write_rate'] for s in window]
        features.extend([
            np.mean(disk_read),
            np.max(disk_read),
            np.mean(disk_write),
            np.max(disk_write)
        ])
        
        # Process count features
        proc_counts = [s['process_count'] for s in window]
        features.extend([
            np.mean(proc_counts),
            np.max(proc_counts)
        ])
        
        # Top process CPU/memory
        top_cpu = [s['top_proc_cpu'] for s in window]
        top_mem = [s['top_proc_mem'] for s in window]
        features.extend([
            np.mean(top_cpu),
            np.max(top_cpu),
            np.mean(top_mem),
            np.max(top_mem)
        ])
        
        # I/O wait
        io_waits = [s['io_wait'] for s in window]
        features.extend([
            np.mean(io_waits),
            np.max(io_waits)
        ])
        
        # Battery status (from last sample)
        features.extend([
            window[-1]['battery_percent'],
            window[-1]['plugged_bool']
        ])
        
        # User presence (from last sample)
        features.append(window[-1]['user_present'])
        
        return np.array(features, dtype=np.float32)
    
    def process_file(self, filepath: str) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Process a CSV file and extract features for all windows.
        
        Args:
            filepath: Path to CSV file
            
        Returns:
            Tuple of (X, y_class, y_time) where:
                X: Feature matrix (n_windows, n_features)
                y_class: Task class labels (n_windows,)
                y_time: Time remaining in minutes (n_windows,)
        """
        samples = self.load_csv(filepath)
        
        if len(samples) < self.window_size:
            logger.warning(f"File has only {len(samples)} samples, need at least {self.window_size}")
            return np.array([]), np.array([]), np.array([])
        
        X = []
        y_class = []
        y_time = []
        
        # Sliding window
        for i in range(0, len(samples) - self.window_size + 1, self.stride):
            window = samples[i:i + self.window_size]
            
            # Extract features
            features = self.extract_window_features(window)
            X.append(features)
            
            # Get label from last sample in window
            last_sample = window[-1]
            task_label = last_sample['task_label']
            task_class = self.TASK_LABELS.get(task_label, 0)
            
            y_class.append(task_class)
            y_time.append(last_sample['time_remaining_minutes'])
        
        X = np.array(X, dtype=np.float32)
        y_class = np.array(y_class, dtype=np.int32)
        y_time = np.array(y_time, dtype=np.float32)
        
        logger.info(f"Extracted {len(X)} windows with {X.shape[1]} features each")
        return X, y_class, y_time
    
    def process_directory(self, dirpath: str, pattern: str = '*.csv') -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Process all CSV files in a directory.
        
        Args:
            dirpath: Path to directory containing CSV files
            pattern: Glob pattern for CSV files
            
        Returns:
            Tuple of (X, y_class, y_time) concatenated from all files
        """
        directory = Path(dirpath)
        csv_files = list(directory.glob(pattern))
        
        if not csv_files:
            logger.warning(f"No CSV files found in {dirpath} matching {pattern}")
            return np.array([]), np.array([]), np.array([])
        
        logger.info(f"Processing {len(csv_files)} CSV files from {dirpath}")
        
        all_X = []
        all_y_class = []
        all_y_time = []
        
        for csv_file in csv_files:
            try:
                X, y_class, y_time = self.process_file(str(csv_file))
                
                if len(X) > 0:
                    all_X.append(X)
                    all_y_class.append(y_class)
                    all_y_time.append(y_time)
                    
            except Exception as e:
                logger.error(f"Error processing {csv_file}: {e}")
        
        if not all_X:
            return np.array([]), np.array([]), np.array([])
        
        # Concatenate all
        X = np.vstack(all_X)
        y_class = np.concatenate(all_y_class)
        y_time = np.concatenate(all_y_time)
        
        logger.info(f"Total: {len(X)} windows extracted from {len(csv_files)} files")
        return X, y_class, y_time
    
    def normalize_features(self, X: np.ndarray, mean: Optional[np.ndarray] = None, 
                          std: Optional[np.ndarray] = None) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Normalize features using z-score normalization.
        
        Args:
            X: Feature matrix
            mean: Pre-computed mean (if None, compute from X)
            std: Pre-computed std (if None, compute from X)
            
        Returns:
            Tuple of (X_normalized, mean, std)
        """
        if mean is None:
            mean = np.mean(X, axis=0)
        if std is None:
            std = np.std(X, axis=0)
            std[std == 0] = 1.0  # Avoid division by zero
        
        X_normalized = (X - mean) / std
        return X_normalized, mean, std
    
    def get_feature_names(self) -> List[str]:
        """
        Get names of all extracted features.
        
        Returns:
            List of feature names
        """
        return [
            'cpu_mean_mean', 'cpu_mean_std', 'cpu_mean_max',
            'mem_mean', 'mem_std', 'mem_max',
            'net_rx_mean', 'net_rx_max', 'net_tx_mean', 'net_tx_max',
            'disk_read_mean', 'disk_read_max', 'disk_write_mean', 'disk_write_max',
            'proc_count_mean', 'proc_count_max',
            'top_cpu_mean', 'top_cpu_max', 'top_mem_mean', 'top_mem_max',
            'io_wait_mean', 'io_wait_max',
            'battery_percent', 'plugged_bool',
            'user_present'
        ]


def main():
    """CLI interface for feature extraction."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Senthium AI Feature Extractor')
    parser.add_argument('input', help='Input CSV file or directory')
    parser.add_argument('--output', '-o', help='Output NPZ file (optional)')
    parser.add_argument('--window-size', '-w', type=int, default=6, help='Window size (default: 6)')
    parser.add_argument('--stride', '-s', type=int, default=1, help='Stride for sliding window (default: 1)')
    parser.add_argument('--normalize', '-n', action='store_true', help='Normalize features')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create extractor
    extractor = FeatureExtractor(window_size=args.window_size, stride=args.stride)
    
    # Process input
    input_path = Path(args.input)
    if input_path.is_file():
        X, y_class, y_time = extractor.process_file(str(input_path))
    elif input_path.is_dir():
        X, y_class, y_time = extractor.process_directory(str(input_path))
    else:
        print(f"Error: {args.input} is not a valid file or directory")
        return 1
    
    if len(X) == 0:
        print("No features extracted")
        return 1
    
    # Normalize if requested
    if args.normalize:
        X, mean, std = extractor.normalize_features(X)
        print(f"Features normalized (mean subtracted, divided by std)")
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"Feature Extraction Summary")
    print(f"{'='*60}")
    print(f"Input: {args.input}")
    print(f"Windows extracted: {len(X)}")
    print(f"Features per window: {X.shape[1]}")
    print(f"Window size: {args.window_size}")
    print(f"Stride: {args.stride}")
    print(f"\nClass distribution:")
    for class_idx, class_name in enumerate(['idle', 'moderate', 'critical']):
        count = np.sum(y_class == class_idx)
        print(f"  {class_name}: {count} ({count/len(y_class)*100:.1f}%)")
    print(f"\nTime remaining stats:")
    print(f"  Mean: {np.mean(y_time):.2f} min")
    print(f"  Std: {np.std(y_time):.2f} min")
    print(f"  Min: {np.min(y_time):.2f} min")
    print(f"  Max: {np.max(y_time):.2f} min")
    print(f"{'='*60}\n")
    
    # Save if output specified
    if args.output:
        save_dict = {
            'X': X,
            'y_class': y_class,
            'y_time': y_time,
            'feature_names': extractor.get_feature_names()
        }
        
        if args.normalize:
            save_dict['mean'] = mean
            save_dict['std'] = std
        
        np.savez(args.output, **save_dict)
        print(f"Saved features to {args.output}")
    
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
