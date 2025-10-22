#!/usr/bin/env python3
"""
Demo script for collecting labeled telemetry data.
Shows how to use the DataLogger to collect training data.
"""
import time
import argparse
import logging
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from senthium_ai.monitors.data_logger import DataLogger


def simulate_workload_demo():
    """
    Interactive demo that guides the user through data collection.
    """
    print("\n" + "="*70)
    print("Senthium AI - Data Collection Demo")
    print("="*70)
    print("\nThis demo will guide you through collecting labeled telemetry data.")
    print("You can use this data to train the ANN model.\n")
    
    print("Available task types:")
    print("  - idle: System is idle, no significant activity")
    print("  - download: Downloading files")
    print("  - render: Video/image rendering or processing")
    print("  - training: ML model training or computation")
    print("  - compile: Building/compiling software")
    print("  - backup: Backup or file transfer operations")
    print()
    
    # Get session details
    session_id = input("Enter session ID (e.g., 'test1', 'idle_session'): ").strip()
    if not session_id:
        session_id = f"demo_{int(time.time())}"
        print(f"Using default session ID: {session_id}")
    
    task_label = input("Enter task type (idle/download/render/training/compile/backup): ").strip().lower()
    if task_label not in ['idle', 'download', 'render', 'training', 'compile', 'backup']:
        print(f"Warning: '{task_label}' is not a standard label. Using anyway.")
    
    try:
        duration = float(input("Enter duration in seconds (default: 60): ").strip() or "60")
    except ValueError:
        duration = 60.0
    
    try:
        time_remaining = float(input("Enter expected time remaining in minutes (default: 5): ").strip() or "5")
    except ValueError:
        time_remaining = 5.0
    
    user_present = input("Are you present at the computer? (y/n, default: y): ").strip().lower() != 'n'
    
    notes = input("Any notes about this session? (optional): ").strip()
    
    # Setup logger
    logger = DataLogger(output_dir='data/raw', sampling_interval=5.0)
    
    print("\n" + "="*70)
    print("Starting Data Collection")
    print("="*70)
    print(f"Session ID: {session_id}")
    print(f"Task Type: {task_label}")
    print(f"Duration: {duration}s")
    print(f"Sampling every: 5 seconds")
    print(f"Time Remaining: {time_remaining} minutes")
    print(f"User Present: {user_present}")
    if notes:
        print(f"Notes: {notes}")
    print("="*70 + "\n")
    
    input("Press ENTER to start logging...")
    
    try:
        # Start session
        filepath = logger.start_session(
            session_id=session_id,
            task_label=task_label,
            time_remaining_minutes=time_remaining,
            user_present=user_present,
            notes=notes
        )
        
        print(f"\nLogging to: {filepath}")
        print("Collecting telemetry... (Ctrl+C to stop early)\n")
        
        # Log continuously
        start_time = time.time()
        sample_count = 0
        
        while True:
            # Log sample
            sample = logger.log_sample()
            sample_count += 1
            
            # Update time remaining (decrement)
            elapsed_minutes = (time.time() - start_time) / 60
            remaining = max(0, time_remaining - elapsed_minutes)
            logger.update_labels(time_remaining_minutes=remaining)
            
            # Print progress
            print(f"[Sample {sample_count:3d}] "
                  f"CPU: {sample['cpu_mean']:5.1f}% | "
                  f"Mem: {sample['mem_percent']:5.1f}% | "
                  f"Net RX: {sample['net_rx_rate']/1024:7.1f} KB/s | "
                  f"Remaining: {remaining:5.1f}min",
                  end='\r')
            
            # Check if duration reached
            if time.time() - start_time >= duration:
                print(f"\n\nDuration reached ({duration}s)")
                break
            
            # Wait for next sample
            time.sleep(5.0)
        
        # End session
        logger.end_session()
        
        print("\n" + "="*70)
        print("Data Collection Complete")
        print("="*70)
        print(f"Samples collected: {sample_count}")
        print(f"Output file: {filepath}")
        print("="*70 + "\n")
        
        print("Next steps:")
        print("1. Collect more sessions with different task types")
        print("2. Use the feature extractor to process the data:")
        print(f"   python -m senthium_ai.utils.feature_extractor data/raw -o data/processed/features.npz")
        print("3. Train the model:")
        print(f"   python train_model.py --data data/processed/features.npz")
        print()
        
    except KeyboardInterrupt:
        print("\n\nCollection interrupted by user")
        logger.end_session()
        print("Data saved successfully.")
    except Exception as e:
        print(f"\nError during collection: {e}")
        logger.end_session()
        return 1
    
    return 0


def automated_collection_demo():
    """
    Automated collection with simulated workload.
    """
    print("\n" + "="*70)
    print("Senthium AI - Automated Data Collection Demo")
    print("="*70)
    print("\nThis will collect 3 short sessions automatically:")
    print("  1. Idle session (30 seconds)")
    print("  2. Moderate activity (30 seconds)")
    print("  3. High activity (30 seconds)")
    print()
    
    input("Press ENTER to start...")
    
    sessions = [
        ('auto_idle', 'idle', 0.5, 30),
        ('auto_moderate', 'download', 2.0, 30),
        ('auto_critical', 'training', 10.0, 30)
    ]
    
    for session_id, task_type, time_rem, duration in sessions:
        print(f"\n{'='*70}")
        print(f"Session: {session_id} ({task_type})")
        print(f"{'='*70}")
        
        logger = DataLogger(output_dir='data/raw', sampling_interval=5.0)
        
        try:
            filepath = logger.start_session(
                session_id=session_id,
                task_label=task_type,
                time_remaining_minutes=time_rem,
                user_present=True,
                notes=f"Automated demo - {task_type}"
            )
            
            print(f"Logging to: {filepath}")
            
            start_time = time.time()
            while time.time() - start_time < duration:
                logger.log_sample()
                print(".", end="", flush=True)
                time.sleep(5.0)
            
            logger.end_session()
            print(f"\n✓ Session complete")
            
        except Exception as e:
            print(f"\n✗ Error: {e}")
            logger.end_session()
    
    print("\n" + "="*70)
    print("All sessions complete!")
    print("="*70)
    print("\nData saved in: data/raw/")
    print("\nNext steps:")
    print("  python -m senthium_ai.utils.feature_extractor data/raw -o data/processed/features.npz")
    print("  python train_model.py --data data/processed/features.npz")
    print()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Data Collection Demo for Senthium AI',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '--mode', '-m',
        choices=['interactive', 'automated'],
        default='interactive',
        help='Demo mode (default: interactive)'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    if args.mode == 'interactive':
        return simulate_workload_demo()
    else:
        return automated_collection_demo()


if __name__ == '__main__':
    sys.exit(main())
