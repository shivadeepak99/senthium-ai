#!/usr/bin/env python3
"""
Demo script showing Senthium AI components in action.
This demonstrates the individual components without running the full system.
"""
import numpy as np
from senthium_ai import ProcessMonitor, TaskPredictor, FuzzyLockController

def demo_process_monitoring():
    """Demonstrate process monitoring capabilities."""
    print("\n" + "="*60)
    print("1. Process Monitoring Demo")
    print("="*60)
    
    monitor = ProcessMonitor(cpu_threshold=5.0)
    
    # Get active processes
    active_processes = monitor.get_active_processes()
    print(f"\nActive Processes (CPU > 5%): {len(active_processes)}")
    
    for proc in active_processes[:5]:  # Show first 5
        print(f"  - {proc['name']:<20s} CPU: {proc['cpu_percent']:5.1f}% "
              f"MEM: {proc['memory_percent']:5.1f}% "
              f"Critical: {proc['is_critical']}")
    
    # Get system metrics
    metrics = monitor.get_system_metrics()
    print(f"\nSystem Metrics:")
    print(f"  - CPU Usage: {metrics['cpu_percent']:.1f}%")
    print(f"  - Memory Usage: {metrics['memory_percent']:.1f}%")
    print(f"  - Active Processes: {metrics['active_process_count']}")
    
    # Extract features for ML
    features, raw_data = monitor.extract_features()
    print(f"\nExtracted Features for ANN: {len(features)} features")
    print(f"  - Critical process count: {raw_data['critical_count']}")

def demo_task_prediction():
    """Demonstrate ANN task prediction."""
    print("\n" + "="*60)
    print("2. ANN Task Prediction Demo")
    print("="*60)
    
    predictor = TaskPredictor()
    
    # Simulate different scenarios
    scenarios = [
        ([10, 20, 5, 0, 50, 30, 1, 100], "Light usage"),
        ([60, 70, 20, 5, 300, 150, 3, 200], "Heavy workload"),
        ([90, 85, 30, 10, 400, 200, 5, 300], "Critical tasks")
    ]
    
    print("\nPredicting task levels for different scenarios:\n")
    
    for features, description in scenarios:
        task_level, probabilities = predictor.predict(features)
        level_name = ['idle', 'moderate', 'critical'][task_level]
        
        print(f"{description}:")
        print(f"  Predicted Level: {level_name.upper()}")
        print(f"  Probabilities: Idle={probabilities[0]:.2%}, "
              f"Moderate={probabilities[1]:.2%}, Critical={probabilities[2]:.2%}")
        print()

def demo_fuzzy_logic():
    """Demonstrate fuzzy logic controller."""
    print("\n" + "="*60)
    print("3. Fuzzy Logic Controller Demo")
    print("="*60)
    
    controller = FuzzyLockController()
    
    # Test different input combinations
    test_cases = [
        (90, 80, 50, "High criticality, high load, no user detection"),
        (30, 40, 90, "Low criticality, low load, user present"),
        (50, 60, 20, "Medium criticality, medium load, user likely absent"),
        (80, 70, 100, "High criticality, high load, user confirmed present"),
        (10, 15, 30, "Idle system, user possibly away")
    ]
    
    print("\nFuzzy logic decisions for different scenarios:\n")
    
    for task_crit, sys_load, presence, description in test_cases:
        state, output = controller.decide_lock_state(task_crit, sys_load, presence)
        state_desc = controller.get_state_description(state)
        
        print(f"{description}")
        print(f"  Inputs: Criticality={task_crit}%, Load={sys_load}%, Presence={presence}%")
        print(f"  Decision: {state.upper().replace('_', ' ')}")
        print(f"  Description: {state_desc}")
        print(f"  Fuzzy Output: {output:.1f}")
        print()

def demo_integration():
    """Demonstrate integrated system flow."""
    print("\n" + "="*60)
    print("4. Integrated System Flow Demo")
    print("="*60)
    
    # Create components
    monitor = ProcessMonitor()
    predictor = TaskPredictor()
    controller = FuzzyLockController()
    
    print("\nSimulating full system evaluation...\n")
    
    # Get real system data
    features, raw_data = monitor.extract_features()
    
    print("Step 1: Process Monitoring")
    print(f"  - Active processes: {len(raw_data['active_processes'])}")
    print(f"  - Critical processes: {raw_data['critical_count']}")
    print(f"  - System CPU: {raw_data['system_metrics']['cpu_percent']:.1f}%")
    
    # Predict task level
    task_level, probabilities = predictor.predict(features)
    task_criticality = probabilities[2] * 100
    
    print("\nStep 2: ANN Task Prediction")
    print(f"  - Task level: {['idle', 'moderate', 'critical'][task_level]}")
    print(f"  - Critical probability: {task_criticality:.1f}%")
    
    # Decide lock state
    system_load = max(raw_data['system_metrics']['cpu_percent'],
                     raw_data['system_metrics']['memory_percent'])
    presence = 50.0  # No face detection in this demo
    
    state, output = controller.decide_lock_state(task_criticality, system_load, presence)
    
    print("\nStep 3: Fuzzy Logic Decision")
    print(f"  - System load: {system_load:.1f}%")
    print(f"  - Presence confidence: {presence:.1f}%")
    print(f"  - Lock state: {state.upper().replace('_', ' ')}")
    print(f"  - Fuzzy output: {output:.1f}")
    
    print("\nFinal Result:")
    print(f"  → {controller.get_state_description(state)}")

def main():
    """Run all demos."""
    print("\n" + "="*60)
    print("Senthium AI - Component Demonstration")
    print("="*60)
    print("This demo shows how each component works independently.")
    print("For the full integrated system, run: python senthium_ai.py")
    
    try:
        demo_process_monitoring()
        demo_task_prediction()
        demo_fuzzy_logic()
        demo_integration()
        
        print("\n" + "="*60)
        print("Demo Complete!")
        print("="*60)
        print("\nTo run the full system:")
        print("  python senthium_ai.py --dry-run")
        print("\nFor more options:")
        print("  python senthium_ai.py --help")
        print()
        
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
    except Exception as e:
        print(f"\nError during demo: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
