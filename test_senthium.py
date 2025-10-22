#!/usr/bin/env python3
"""
Basic tests for Senthium AI components.
Run with: python test_senthium.py
"""
import numpy as np
from senthium_ai import (
    ProcessMonitor,
    TaskPredictor,
    FuzzyLockController,
    FaceDetector
)

def test_process_monitor():
    """Test process monitoring functionality."""
    print("Testing ProcessMonitor...")
    
    monitor = ProcessMonitor(cpu_threshold=5.0)
    
    # Test getting active processes
    processes = monitor.get_active_processes()
    assert isinstance(processes, list), "Active processes should be a list"
    
    # Test system metrics
    metrics = monitor.get_system_metrics()
    assert 'cpu_percent' in metrics, "System metrics should include CPU"
    assert 'memory_percent' in metrics, "System metrics should include memory"
    assert 0 <= metrics['cpu_percent'] <= 100, "CPU should be 0-100%"
    assert 0 <= metrics['memory_percent'] <= 100, "Memory should be 0-100%"
    
    # Test feature extraction
    features, raw_data = monitor.extract_features()
    assert len(features) == 8, "Should extract 8 features"
    assert 'critical_count' in raw_data, "Should include critical count"
    
    print("  ✓ ProcessMonitor tests passed")
    return True

def test_task_predictor():
    """Test ANN task predictor."""
    print("Testing TaskPredictor...")
    
    predictor = TaskPredictor(input_size=8, hidden_size=16, output_size=3)
    
    # Test prediction with sample features
    features = [50.0, 60.0, 10, 2, 200, 100, 2.0, 150]
    task_level, probabilities = predictor.predict(features)
    
    assert isinstance(task_level, (int, np.integer)), "Task level should be an integer"
    assert 0 <= task_level <= 2, "Task level should be 0-2"
    assert len(probabilities) == 3, "Should return 3 probabilities"
    assert abs(sum(probabilities) - 1.0) < 0.01, "Probabilities should sum to ~1"
    
    # Test get_task_level
    level_name = predictor.get_task_level(features)
    assert level_name in ['idle', 'moderate', 'critical'], "Invalid level name"
    
    # Test training (small batch)
    X = np.random.rand(10, 8)
    y = np.random.randint(0, 3, 10)
    losses = predictor.train(X, y, epochs=10, learning_rate=0.01)
    assert len(losses) == 10, "Should return loss for each epoch"
    assert all(loss >= 0 for loss in losses), "Losses should be non-negative"
    
    print("  ✓ TaskPredictor tests passed")
    return True

def test_fuzzy_controller():
    """Test fuzzy logic controller."""
    print("Testing FuzzyLockController...")
    
    controller = FuzzyLockController()
    
    # Test various input combinations
    test_cases = [
        (90, 80, 50),  # High criticality, high load
        (30, 40, 90),  # Low criticality, user present
        (50, 60, 20),  # Medium criticality, user absent
    ]
    
    for task_crit, sys_load, presence in test_cases:
        state, output = controller.decide_lock_state(task_crit, sys_load, presence)
        
        assert state in ['stay_awake', 'dim', 'full_lock'], f"Invalid state: {state}"
        assert 0 <= output <= 100, f"Output should be 0-100, got {output}"
        
        # Test state description
        description = controller.get_state_description(state)
        assert isinstance(description, str), "Description should be a string"
        assert len(description) > 0, "Description should not be empty"
    
    print("  ✓ FuzzyLockController tests passed")
    return True

def test_face_detector():
    """Test face detector (without camera)."""
    print("Testing FaceDetector...")
    
    # Initialize without enabling camera
    detector = FaceDetector(camera_index=0)
    
    # Test that detector is not enabled by default
    assert not detector.enabled, "Detector should not be enabled initially"
    
    # Test detection when disabled (should return neutral confidence)
    present, confidence = detector.detect_presence()
    assert not present, "Should not detect presence when disabled"
    assert confidence == 50.0, "Should return neutral confidence when disabled"
    
    # Test cleanup
    detector.disable()
    
    print("  ✓ FaceDetector tests passed")
    return True

def test_integration():
    """Test integrated workflow."""
    print("Testing integrated workflow...")
    
    # Create components
    monitor = ProcessMonitor()
    predictor = TaskPredictor()
    controller = FuzzyLockController()
    
    # Get features from monitor
    features, raw_data = monitor.extract_features()
    assert len(features) > 0, "Should extract features"
    
    # Predict task level
    task_level, probabilities = predictor.predict(features)
    task_criticality = probabilities[2] * 100
    assert 0 <= task_criticality <= 100, "Criticality should be 0-100%"
    
    # Get lock state
    system_load = max(raw_data['system_metrics']['cpu_percent'],
                     raw_data['system_metrics']['memory_percent'])
    state, output = controller.decide_lock_state(task_criticality, system_load, 50.0)
    
    assert state in ['stay_awake', 'dim', 'full_lock'], "Should return valid state"
    
    print("  ✓ Integration tests passed")
    return True

def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("Running Senthium AI Tests")
    print("="*60 + "\n")
    
    tests = [
        test_process_monitor,
        test_task_predictor,
        test_fuzzy_controller,
        test_face_detector,
        test_integration
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
            failed += 1
    
    print("\n" + "="*60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("="*60 + "\n")
    
    return 0 if failed == 0 else 1

if __name__ == '__main__':
    import sys
    sys.exit(main())
