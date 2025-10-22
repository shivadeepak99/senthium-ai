"""
Fuzzy Logic controller for deciding adaptive lock states.
"""
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
import logging

logger = logging.getLogger(__name__)


class FuzzyLockController:
    """
    Fuzzy Logic controller to determine adaptive lock states based on:
    - Task criticality
    - System load
    - User presence confidence
    """
    
    def __init__(self):
        """Initialize the fuzzy logic controller."""
        self._setup_fuzzy_system()
        
    def _setup_fuzzy_system(self):
        """Set up fuzzy variables and rules."""
        # Input variables
        # Task criticality (0-100): 0=idle, 100=critical
        self.task_criticality = ctrl.Antecedent(np.arange(0, 101, 1), 'task_criticality')
        self.task_criticality['low'] = fuzz.trimf(self.task_criticality.universe, [0, 0, 50])
        self.task_criticality['medium'] = fuzz.trimf(self.task_criticality.universe, [20, 50, 80])
        self.task_criticality['high'] = fuzz.trimf(self.task_criticality.universe, [50, 100, 100])
        
        # System load (0-100): CPU/memory usage percentage
        self.system_load = ctrl.Antecedent(np.arange(0, 101, 1), 'system_load')
        self.system_load['low'] = fuzz.trimf(self.system_load.universe, [0, 0, 40])
        self.system_load['medium'] = fuzz.trimf(self.system_load.universe, [20, 50, 80])
        self.system_load['high'] = fuzz.trimf(self.system_load.universe, [60, 100, 100])
        
        # User presence confidence (0-100): 0=absent, 100=present
        self.presence_confidence = ctrl.Antecedent(np.arange(0, 101, 1), 'presence_confidence')
        self.presence_confidence['absent'] = fuzz.trimf(self.presence_confidence.universe, [0, 0, 40])
        self.presence_confidence['uncertain'] = fuzz.trimf(self.presence_confidence.universe, [20, 50, 80])
        self.presence_confidence['present'] = fuzz.trimf(self.presence_confidence.universe, [60, 100, 100])
        
        # Output variable: Lock state (0-100)
        # 0-30: Stay awake, 31-70: Dim, 71-100: Full lock
        self.lock_state = ctrl.Consequent(np.arange(0, 101, 1), 'lock_state')
        self.lock_state['stay_awake'] = fuzz.trimf(self.lock_state.universe, [0, 0, 30])
        self.lock_state['dim'] = fuzz.trimf(self.lock_state.universe, [20, 50, 80])
        self.lock_state['full_lock'] = fuzz.trimf(self.lock_state.universe, [70, 100, 100])
        
        # Fuzzy rules
        rules = [
            # High criticality tasks - stay awake regardless of presence
            ctrl.Rule(self.task_criticality['high'] & self.system_load['high'], 
                     self.lock_state['stay_awake']),
            ctrl.Rule(self.task_criticality['high'] & self.system_load['medium'], 
                     self.lock_state['stay_awake']),
            
            # Medium criticality with user present - stay awake or dim
            ctrl.Rule(self.task_criticality['medium'] & self.presence_confidence['present'], 
                     self.lock_state['stay_awake']),
            ctrl.Rule(self.task_criticality['medium'] & self.presence_confidence['uncertain'], 
                     self.lock_state['dim']),
            ctrl.Rule(self.task_criticality['medium'] & self.presence_confidence['absent'], 
                     self.lock_state['full_lock']),
            
            # Low criticality - depend on user presence
            ctrl.Rule(self.task_criticality['low'] & self.presence_confidence['present'], 
                     self.lock_state['stay_awake']),
            ctrl.Rule(self.task_criticality['low'] & self.presence_confidence['uncertain'], 
                     self.lock_state['dim']),
            ctrl.Rule(self.task_criticality['low'] & self.presence_confidence['absent'], 
                     self.lock_state['full_lock']),
            
            # High system load with low criticality but user present
            ctrl.Rule(self.task_criticality['low'] & self.system_load['high'] & 
                     self.presence_confidence['present'], self.lock_state['dim']),
        ]
        
        # Create control system
        self.lock_ctrl = ctrl.ControlSystem(rules)
        self.simulation = ctrl.ControlSystemSimulation(self.lock_ctrl)
        
    def decide_lock_state(self, task_criticality: float, system_load: float, 
                         presence_confidence: float) -> tuple[str, float]:
        """
        Decide the lock state based on inputs.
        
        Args:
            task_criticality: Task criticality level (0-100)
            system_load: System load percentage (0-100)
            presence_confidence: User presence confidence (0-100)
            
        Returns:
            Tuple of (lock state name, raw output value)
        """
        try:
            # Set inputs
            self.simulation.input['task_criticality'] = np.clip(task_criticality, 0, 100)
            self.simulation.input['system_load'] = np.clip(system_load, 0, 100)
            self.simulation.input['presence_confidence'] = np.clip(presence_confidence, 0, 100)
            
            # Compute output
            self.simulation.compute()
            
            output_value = self.simulation.output['lock_state']
            
            # Map output to state names
            if output_value <= 30:
                state = 'stay_awake'
            elif output_value <= 70:
                state = 'dim'
            else:
                state = 'full_lock'
                
            logger.debug(f"Fuzzy decision: criticality={task_criticality:.1f}, "
                        f"load={system_load:.1f}, presence={presence_confidence:.1f} "
                        f"-> {state} ({output_value:.1f})")
            
            return state, output_value
            
        except Exception as e:
            logger.error(f"Error in fuzzy controller: {e}")
            # Default to safe state
            return 'dim', 50.0
    
    def get_state_description(self, state: str) -> str:
        """
        Get human-readable description of lock state.
        
        Args:
            state: Lock state name
            
        Returns:
            Description string
        """
        descriptions = {
            'stay_awake': 'Keep screen on - critical tasks running',
            'dim': 'Dim screen - moderate activity or uncertain presence',
            'full_lock': 'Full lock - idle system or user absent'
        }
        return descriptions.get(state, 'Unknown state')
