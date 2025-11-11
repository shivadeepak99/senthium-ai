"""
Unit tests for Rules Engine
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime
from src.rules.engine import RulesEngine, RuleMatch
from src.rules.schema import ConfigSchema, ConfigValidationError
from src.daemon.monitor import SystemMetrics


class TestConfigSchema:
    """Test suite for configuration schema validation"""
    
    def test_schema_loads(self):
        """Test that schema file loads correctly"""
        validator = ConfigSchema()
        assert validator.schema is not None
        assert 'definitions' in validator.schema
    
    def test_valid_minimal_config(self):
        """Test validation of minimal valid config"""
        valid_config = {
            'senthium': {
                'version': '0.2',
                'rules': [
                    {
                        'name': 'Test Rule',
                        'type': 'cpu',
                        'threshold': 50
                    }
                ]
            }
        }
        
        validator = ConfigSchema()
        assert validator.validate_config(valid_config) is True
    
    def test_invalid_version_format(self):
        """Test that invalid version format is rejected"""
        invalid_config = {
            'senthium': {
                'version': 'invalid',  # Should be X.Y format
                'rules': []
            }
        }
        
        validator = ConfigSchema()
        with pytest.raises(ConfigValidationError):
            validator.validate_config(invalid_config)
    
    def test_missing_required_fields(self):
        """Test that missing required fields are rejected"""
        invalid_config = {
            'senthium': {
                'version': '0.2'
                # Missing 'rules' field
            }
        }
        
        validator = ConfigSchema()
        with pytest.raises(ConfigValidationError):
            validator.validate_config(invalid_config)
    
    def test_invalid_rule_type(self):
        """Test that invalid rule type is rejected"""
        invalid_config = {
            'senthium': {
                'version': '0.2',
                'rules': [
                    {
                        'name': 'Test',
                        'type': 'invalid_type'  # Not in enum
                    }
                ]
            }
        }
        
        validator = ConfigSchema()
        with pytest.raises(ConfigValidationError):
            validator.validate_config(invalid_config)


class TestRulesEngine:
    """Test suite for RulesEngine"""
    
    def create_test_config(self, rules):
        """Helper to create temporary config file"""
        config = {
            'senthium': {
                'version': '0.2',
                'max_awake_duration': 14400,
                'poll_interval': 5,
                'log_level': 'INFO',
                'rules': rules
            }
        }
        
        # Create temporary YAML file
        import yaml
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        yaml.dump(config, temp_file)
        temp_file.close()
        
        return Path(temp_file.name)
    
    def create_test_metrics(self, **kwargs):
        """Helper to create test metrics"""
        defaults = {
            'timestamp': datetime.now(),
            'cpu_percent': 10.0,
            'disk_read_mbps': 0.0,
            'disk_write_mbps': 0.0,
            'net_sent_mbps': 0.0,
            'net_recv_mbps': 0.0,
            'processes': ['python.exe', 'explorer.exe'],
            'idle_time_seconds': 0.0
        }
        defaults.update(kwargs)
        return SystemMetrics(**defaults)
    
    def test_engine_initialization(self):
        """Test that engine initializes with valid config"""
        config_path = self.create_test_config([
            {'name': 'Test', 'type': 'cpu', 'threshold': 50}
        ])
        
        try:
            engine = RulesEngine(config_path)
            assert len(engine.rules) == 1
            assert engine.senthium_config['version'] == '0.2'
        finally:
            config_path.unlink()
    
    def test_process_rule_matches(self):
        """Test that process rule matches when process is running"""
        config_path = self.create_test_config([
            {
                'name': 'Python Running',
                'type': 'process',
                'processes': ['python.exe', 'python']
            }
        ])
        
        try:
            engine = RulesEngine(config_path)
            metrics = self.create_test_metrics(processes=['python.exe', 'chrome.exe'])
            
            assert engine.evaluate(metrics) is True
        finally:
            config_path.unlink()
    
    def test_process_rule_no_match(self):
        """Test that process rule doesn't match when process not running"""
        config_path = self.create_test_config([
            {
                'name': 'Docker Running',
                'type': 'process',
                'processes': ['docker']
            }
        ])
        
        try:
            engine = RulesEngine(config_path)
            metrics = self.create_test_metrics(processes=['python.exe', 'chrome.exe'])
            
            assert engine.evaluate(metrics) is False
        finally:
            config_path.unlink()
    
    def test_cpu_rule_above_threshold(self):
        """Test CPU rule matches when above threshold"""
        config_path = self.create_test_config([
            {
                'name': 'High CPU',
                'type': 'cpu',
                'threshold': 50
            }
        ])
        
        try:
            engine = RulesEngine(config_path)
            metrics = self.create_test_metrics(cpu_percent=75.0)
            
            assert engine.evaluate(metrics) is True
        finally:
            config_path.unlink()
    
    def test_cpu_rule_below_threshold(self):
        """Test CPU rule doesn't match when below threshold"""
        config_path = self.create_test_config([
            {
                'name': 'High CPU',
                'type': 'cpu',
                'threshold': 50
            }
        ])
        
        try:
            engine = RulesEngine(config_path)
            metrics = self.create_test_metrics(cpu_percent=25.0)
            
            assert engine.evaluate(metrics) is False
        finally:
            config_path.unlink()
    
    def test_disk_rule_matches(self):
        """Test disk rule matches when I/O exceeds threshold"""
        config_path = self.create_test_config([
            {
                'name': 'High Disk I/O',
                'type': 'disk',
                'read_mbps': 10.0,
                'write_mbps': 5.0
            }
        ])
        
        try:
            engine = RulesEngine(config_path)
            metrics = self.create_test_metrics(
                disk_read_mbps=15.0,
                disk_write_mbps=10.0
            )
            
            assert engine.evaluate(metrics) is True
        finally:
            config_path.unlink()
    
    def test_network_rule_matches(self):
        """Test network rule matches when traffic exceeds threshold"""
        config_path = self.create_test_config([
            {
                'name': 'High Network',
                'type': 'network',
                'download_mbps': 1.0,
                'upload_mbps': 0.5
            }
        ])
        
        try:
            engine = RulesEngine(config_path)
            metrics = self.create_test_metrics(
                net_recv_mbps=5.0,
                net_sent_mbps=2.0
            )
            
            assert engine.evaluate(metrics) is True
        finally:
            config_path.unlink()
    
    def test_disabled_rule_not_evaluated(self):
        """Test that disabled rules don't trigger"""
        config_path = self.create_test_config([
            {
                'name': 'Disabled Rule',
                'type': 'cpu',
                'threshold': 1,  # Very low threshold
                'enabled': False
            }
        ])
        
        try:
            engine = RulesEngine(config_path)
            metrics = self.create_test_metrics(cpu_percent=100.0)
            
            # Should not match because rule is disabled
            assert engine.evaluate(metrics) is False
        finally:
            config_path.unlink()
    
    def test_multiple_rules_or_logic(self):
        """Test that multiple rules use OR logic"""
        config_path = self.create_test_config([
            {
                'name': 'Rule 1',
                'type': 'cpu',
                'threshold': 90  # Won't match
            },
            {
                'name': 'Rule 2',
                'type': 'process',
                'processes': ['python.exe']  # Will match
            }
        ])
        
        try:
            engine = RulesEngine(config_path)
            metrics = self.create_test_metrics(
                cpu_percent=50.0,
                processes=['python.exe']
            )
            
            # Should match because Rule 2 matches (OR logic)
            assert engine.evaluate(metrics) is True
        finally:
            config_path.unlink()
    
    def test_combined_rule_and_logic(self):
        """Test that combined rule uses AND logic for conditions"""
        config_path = self.create_test_config([
            {
                'name': 'Download Active',
                'type': 'combined',
                'conditions': [
                    {
                        'type': 'process',
                        'processes': ['chrome.exe']
                    },
                    {
                        'type': 'network',
                        'download_mbps': 1.0
                    }
                ]
            }
        ])
        
        try:
            engine = RulesEngine(config_path)
            
            # Test: Both conditions met
            metrics1 = self.create_test_metrics(
                processes=['chrome.exe'],
                net_recv_mbps=5.0
            )
            assert engine.evaluate(metrics1) is True
            
            # Test: Only one condition met
            metrics2 = self.create_test_metrics(
                processes=['chrome.exe'],
                net_recv_mbps=0.1  # Below threshold
            )
            assert engine.evaluate(metrics2) is False
            
        finally:
            config_path.unlink()
    
    def test_get_config_value(self):
        """Test getting config values"""
        config_path = self.create_test_config([
            {'name': 'Dummy', 'type': 'cpu', 'threshold': 50}  # Need at least 1 rule
        ])
        
        try:
            engine = RulesEngine(config_path)
            
            assert engine.get_config_value('version') == '0.2'
            assert engine.get_config_value('poll_interval') == 5
            assert engine.get_config_value('nonexistent', 'default') == 'default'
        finally:
            config_path.unlink()
    
    def test_process_partial_match(self):
        """Test that process matching works with partial names"""
        config_path = self.create_test_config([
            {
                'name': 'Chrome',
                'type': 'process',
                'processes': ['chrome']  # No .exe
            }
        ])
        
        try:
            engine = RulesEngine(config_path)
            metrics = self.create_test_metrics(processes=['chrome.exe'])
            
            # Should match because 'chrome' is in 'chrome.exe'
            assert engine.evaluate(metrics) is True
        finally:
            config_path.unlink()
    
    def test_empty_rules_list(self):
        """Test that disabled rules don't trigger evaluation"""
        config = {
            'senthium': {
                'version': '0.2',
                'rules': [
                    {
                        'name': 'Dummy',
                        'type': 'cpu',
                        'threshold': 99,  # Very high (valid threshold)
                        'enabled': False  # Disabled
                    }
                ]
            }
        }
        
        import yaml
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        yaml.dump(config, temp_file)
        temp_file.close()
        config_path = Path(temp_file.name)
        
        try:
            engine = RulesEngine(config_path)
            metrics = self.create_test_metrics(cpu_percent=100.0)
            
            # Should return False when all rules disabled
            assert engine.evaluate(metrics) is False
        finally:
            config_path.unlink()


# Duration tests (may be slow)
@pytest.mark.slow
class TestRuleDuration:
    """Test duration-based rules"""
    
    def create_test_config(self, rules):
        """Helper to create temporary config file"""
        config = {
            'senthium': {
                'version': '0.2',
                'rules': rules
            }
        }
        
        import yaml
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        yaml.dump(config, temp_file)
        temp_file.close()
        
        return Path(temp_file.name)
    
    def test_duration_not_met(self):
        """Test that rule doesn't match if duration not sustained"""
        config_path = self.create_test_config([
            {
                'name': 'Sustained CPU',
                'type': 'cpu',
                'threshold': 50,
                'duration': 10  # Requires 10 seconds
            }
        ])
        
        try:
            engine = RulesEngine(config_path)
            metrics = SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=75.0,
                disk_read_mbps=0.0,
                disk_write_mbps=0.0,
                net_sent_mbps=0.0,
                net_recv_mbps=0.0,
                processes=[],
                idle_time_seconds=0.0
            )
            
            # First check - should not match yet
            assert engine.evaluate(metrics) is False
            
        finally:
            config_path.unlink()
