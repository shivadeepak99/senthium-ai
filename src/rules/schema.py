"""
Configuration schema validation
Validates YAML config files against JSON schema
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
import jsonschema
from jsonschema import validate, ValidationError
import yaml


class ConfigValidationError(Exception):
    """Raised when config file validation fails"""
    pass


class ConfigSchema:
    """
    Configuration schema validator
    Validates Senthium config files against JSON schema
    """
    
    def __init__(self, schema_path: Optional[Path] = None):
        """
        Initialize schema validator
        
        Args:
            schema_path: Path to JSON schema file (default: config/config.schema.json)
        """
        self.logger = logging.getLogger(__name__)
        
        if schema_path is None:
            # Default to config/config.schema.json
            schema_path = Path(__file__).parent.parent.parent / 'config' / 'config.schema.json'
        
        self.schema_path = schema_path
        self.schema = self._load_schema()
    
    def _load_schema(self) -> Dict:
        """Load JSON schema from file"""
        try:
            with open(self.schema_path, 'r', encoding='utf-8') as f:
                schema = json.load(f)
            self.logger.debug(f"Schema loaded from {self.schema_path}")
            return schema
        except FileNotFoundError:
            raise ConfigValidationError(f"Schema file not found: {self.schema_path}")
        except json.JSONDecodeError as e:
            raise ConfigValidationError(f"Invalid JSON in schema file: {e}")
    
    def validate_config(self, config_data: Dict) -> bool:
        """
        Validate config data against schema
        
        Args:
            config_data: Parsed YAML config as dictionary
            
        Returns:
            True if valid
            
        Raises:
            ConfigValidationError: If validation fails
        """
        try:
            validate(instance=config_data, schema=self.schema)
            self.logger.info("Configuration validated successfully")
            return True
        except ValidationError as e:
            error_path = " -> ".join(str(p) for p in e.path) if e.path else "root"
            error_msg = f"Validation error at {error_path}: {e.message}"
            self.logger.error(error_msg)
            raise ConfigValidationError(error_msg)
    
    def load_and_validate(self, config_path: Path) -> Dict:
        """
        Load YAML config file and validate
        
        Args:
            config_path: Path to YAML config file
            
        Returns:
            Validated config dictionary
            
        Raises:
            ConfigValidationError: If file not found or validation fails
        """
        # Load YAML file
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
        except FileNotFoundError:
            raise ConfigValidationError(f"Config file not found: {config_path}")
        except yaml.YAMLError as e:
            raise ConfigValidationError(f"Invalid YAML: {e}")
        
        # Validate against schema
        self.validate_config(config_data)
        
        return config_data


# Example usage
if __name__ == '__main__':
    from utils.logger import setup_logger
    
    logger = setup_logger('senthium.schema', level='DEBUG')
    
    # Test schema validator
    validator = ConfigSchema()
    
    # Try to load example config
    example_config_path = Path(__file__).parent.parent.parent / 'config' / 'config.example.yaml'
    
    try:
        config = validator.load_and_validate(example_config_path)
        print("✅ Example config is valid!")
        print(f"   Version: {config['senthium']['version']}")
        print(f"   Rules: {len(config['senthium']['rules'])}")
    except ConfigValidationError as e:
        print(f"❌ Validation failed: {e}")
