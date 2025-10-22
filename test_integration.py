#!/usr/bin/env python3
"""
Integration tests for new Senthium AI modules.
Tests DataLogger, FeatureExtractor, LockController, and training pipeline.
"""
import os
import tempfile
import shutil
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from senthium_ai import DataLogger, FeatureExtractor, LockController


def test_data_logger():
    """Test DataLogger functionality."""
    print("Testing DataLogger...")
    
    # Create temp directory
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = DataLogger(output_dir=tmpdir, sampling_interval=1.0)
        
        # Start session
        filepath = logger.start_session(
            session_id='test_session',
            task_label='idle',
            time_remaining_minutes=1.0,
            user_present=True,
            notes='Test session'
        )
        
        assert Path(filepath).exists(), "CSV file should be created"
        
        # Log a few samples
        for i in range(3):
            sample = logger.log_sample()
            assert 'timestamp' in sample, "Sample should have timestamp"
            assert 'cpu_mean' in sample, "Sample should have CPU metrics"
            assert sample['task_label'] == 'idle', "Task label should match"
        
        # Update labels
        logger.update_labels(task_label='download', time_remaining_minutes=2.0)
        sample = logger.log_sample()
        assert sample['task_label'] == 'download', "Label should be updated"
        
        # End session
        logger.end_session()
        assert logger.csv_writer is None, "Session should be closed"
        
        # Verify file exists and has content
        with open(filepath, 'r') as f:
            lines = f.readlines()
            assert len(lines) > 1, "CSV should have header + data"
    
    print("  ✓ DataLogger tests passed")
    return True


def test_feature_extractor():
    """Test FeatureExtractor functionality."""
    print("Testing FeatureExtractor...")
    
    # Create temp directory with sample CSV
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a logger and collect some data
        logger = DataLogger(output_dir=tmpdir, sampling_interval=0.1)
        filepath = logger.start_session(
            session_id='feature_test',
            task_label='critical',
            time_remaining_minutes=5.0
        )
        
        # Log enough samples for feature extraction
        for i in range(10):
            logger.log_sample()
        
        logger.end_session()
        
        # Test feature extraction
        extractor = FeatureExtractor(window_size=6, stride=1)
        
        # Test single file
        X, y_class, y_time = extractor.process_file(filepath)
        
        assert len(X) > 0, "Should extract features"
        assert X.shape[1] == 25, "Should have 25 features"
        assert len(X) == len(y_class) == len(y_time), "Arrays should match"
        assert all(y_class == 2), "Critical should be class 2"
        
        # Test feature names
        feature_names = extractor.get_feature_names()
        assert len(feature_names) == 25, "Should have 25 feature names"
        
        # Test normalization
        X_norm, mean, std = extractor.normalize_features(X)
        assert X_norm.shape == X.shape, "Normalized shape should match"
        assert len(mean) == 25, "Mean should have 25 values"
        assert len(std) == 25, "Std should have 25 values"
        
        # Test directory processing
        X_dir, y_dir, t_dir = extractor.process_directory(tmpdir)
        assert len(X_dir) > 0, "Should process directory"
        assert len(X_dir) == len(X), "Should match single file"
    
    print("  ✓ FeatureExtractor tests passed")
    return True


def test_lock_controller():
    """Test LockController functionality."""
    print("Testing LockController...")
    
    # Test in dry-run mode
    controller = LockController(dry_run=True)
    
    # Test keep_awake
    result = controller.keep_awake()
    assert result is True, "Keep awake should succeed in dry-run"
    
    # Test delay_lock
    result = controller.delay_lock(minutes=5)
    assert result is True, "Delay lock should succeed"
    
    # Test full_lock
    result = controller.full_lock()
    assert result is True, "Full lock should succeed"
    
    # Test screen_off
    result = controller.screen_off()
    assert result is True, "Screen off should succeed"
    
    # Test dim_screen
    result = controller.dim_screen(brightness=50)
    assert result is True, "Dim screen should succeed"
    
    # Test restore
    result = controller.restore()
    assert result is True, "Restore should succeed"
    
    # Test cleanup
    controller.cleanup()
    
    print("  ✓ LockController tests passed")
    return True


def test_end_to_end_pipeline():
    """Test complete data collection -> training pipeline."""
    print("Testing end-to-end pipeline...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Step 1: Collect data
        logger = DataLogger(output_dir=tmpdir, sampling_interval=0.1)
        
        # Collect multiple sessions
        for task_label in ['idle', 'moderate', 'critical']:
            filepath = logger.start_session(
                session_id=f'test_{task_label}',
                task_label=task_label,
                time_remaining_minutes=1.0
            )
            
            # Log samples
            for i in range(15):
                logger.log_sample()
            
            logger.end_session()
        
        # Step 2: Extract features
        extractor = FeatureExtractor(window_size=6, stride=1)
        X, y_class, y_time = extractor.process_directory(tmpdir)
        
        assert len(X) > 0, "Should extract features from all sessions"
        
        # Verify we have all classes
        unique_classes = np.unique(y_class)
        assert len(unique_classes) >= 2, "Should have multiple classes"
        
        # Step 3: Normalize
        X_norm, mean, std = extractor.normalize_features(X)
        
        # Step 4: Test we can train with this data (using correct input size)
        from senthium_ai.models import TaskPredictor
        
        # Create model with correct input size (25 features from FeatureExtractor)
        model = TaskPredictor(input_size=25, hidden_size=16, output_size=3)
        
        # Train for a few epochs
        if len(X_norm) >= 20:
            losses = model.train(X_norm[:20], y_class[:20], epochs=5, learning_rate=0.01)
            assert len(losses) == 5, "Should train for 5 epochs"
        
        # Test that model structure is correct
        assert model.W1.shape[0] == 25, "Input weights should match feature count"
        assert model.W2.shape[0] == 16, "Hidden weights should match hidden size"
        assert model.W2.shape[1] == 3, "Output weights should have 3 classes"
    
    print("  ✓ End-to-end pipeline tests passed")
    return True


def main():
    """Run all integration tests."""
    print("\n" + "="*60)
    print("Running Senthium AI Integration Tests")
    print("="*60 + "\n")
    
    tests = [
        test_data_logger,
        test_feature_extractor,
        test_lock_controller,
        test_end_to_end_pipeline
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except AssertionError as e:
            print(f"  ✗ Test failed: {e}")
            failed += 1
        except Exception as e:
            print(f"  ✗ Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "="*60)
    print(f"Integration Test Results: {passed} passed, {failed} failed")
    print("="*60 + "\n")
    
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
