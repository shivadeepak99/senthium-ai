"""
Configuration Manager - Save and load settings from config.yaml
Handles GUI → YAML persistence for user settings
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class ConfigManager:
    """
    Manages reading and writing configuration to config.yaml
    Thread-safe singleton for settings persistence
    """
    
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config_path = Path(config_path)
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self._config: Optional[Dict] = None
    
    def load(self) -> Dict:
        """Load configuration from YAML file"""
        if not self.config_path.exists():
            logger.warning(f"Config file not found: {self.config_path}")
            self._config = self._get_default_config()
            return self._config
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f)
            logger.info(f"✅ Loaded config from {self.config_path}")
            return self._config if self._config is not None else self._get_default_config()
        except Exception as e:
            logger.error(f"❌ Failed to load config: {e}")
            self._config = self._get_default_config()
            return self._config
    
    def save(self, config: Optional[Dict] = None) -> bool:
        """Save configuration to YAML file"""
        if config is not None:
            self._config = config
        
        if self._config is None:
            logger.error("No config to save")
            return False
        
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.safe_dump(self._config, f, default_flow_style=False, sort_keys=False)
            logger.info(f"💾 Saved config to {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to save config: {e}")
            return False
    
    def update_discord(self, webhook_url: str, enabled: bool) -> bool:
        """Update Discord alert settings"""
        if self._config is None:
            self._config = self.load()
        
        try:
            alerts = self._config['senthium']['security']['alerts']
            alerts['discord'] = {
                'enabled': enabled,
                'webhook_url': webhook_url
            }
            return self.save()
        except KeyError as e:
            logger.error(f"❌ Config structure error: {e}")
            return False
    
    def update_email(self, smtp_server: str, smtp_port: int, username: str, 
                    password: str, recipient: str, enabled: bool) -> bool:
        """Update Email/SMTP alert settings"""
        if self._config is None:
            self._config = self.load()
        
        try:
            alerts = self._config['senthium']['security']['alerts']
            alerts['email'] = {
                'enabled': enabled,
                'smtp_server': smtp_server,
                'smtp_port': smtp_port,
                'username': username,
                'password': password,
                'recipient': recipient,
                'use_tls': True
            }
            return self.save()
        except KeyError as e:
            logger.error(f"❌ Config structure error: {e}")
            return False
    
    def update_telegram(self, bot_token: str, chat_id: str, enabled: bool) -> bool:
        """Update Telegram bot alert settings"""
        if self._config is None:
            self._config = self.load()
        
        try:
            alerts = self._config['senthium']['security']['alerts']
            alerts['telegram'] = {
                'enabled': enabled,
                'bot_token': bot_token,
                'chat_id': chat_id
            }
            return self.save()
        except KeyError as e:
            logger.error(f"❌ Config structure error: {e}")
            return False
    
    def update_monitoring(self, check_interval: int, recognition_tolerance: float,
                         camera_index: int, alert_cooldown: int) -> bool:
        """Update monitoring parameters"""
        if self._config is None:
            self._config = self.load()
        
        try:
            security = self._config['senthium']['security']
            security['check_interval_seconds'] = check_interval
            security['recognition_tolerance'] = recognition_tolerance
            security['camera_index'] = camera_index
            security['alert_cooldown_seconds'] = alert_cooldown
            return self.save()
        except KeyError as e:
            logger.error(f"❌ Config structure error: {e}")
            return False
    
    def update_desktop_alerts(self, desktop_notif: bool, sound_alert: bool, log_to_file: bool) -> bool:
        """Update desktop notification settings"""
        if self._config is None:
            self._config = self.load()
        
        try:
            alerts = self._config['senthium']['security']['alerts']
            alerts['desktop_notification'] = desktop_notif
            alerts['sound_alert'] = sound_alert
            alerts['log_to_file'] = log_to_file
            return self.save()
        except KeyError as e:
            logger.error(f"❌ Config structure error: {e}")
            return False
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get config value by dot-separated path
        Example: get('senthium.security.alerts.discord.enabled')
        """
        if self._config is None:
            self._config = self.load()
        
        keys = key_path.split('.')
        value = self._config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def _get_default_config(self) -> Dict:
        """Return default configuration structure"""
        return {
            'senthium': {
                'security': {
                    'enable_security': False,
                    'camera_index': 0,
                    'detection_model': 'dnn',
                    'recognition_tolerance': 0.6,
                    'check_interval_seconds': 10,
                    'alert_cooldown_seconds': 300,
                    'snapshot_dir': 'logs/security/snapshots',
                    'authorized_faces_file': 'config/faces/authorized.json',
                    'alerts': {
                        'desktop_notification': True,
                        'sound_alert': False,
                        'log_to_file': True,
                        'discord': {
                            'enabled': False,
                            'webhook_url': ''
                        },
                        'email': {
                            'enabled': False,
                            'smtp_server': '',
                            'smtp_port': 587,
                            'username': '',
                            'password': '',
                            'recipient': '',
                            'use_tls': True
                        },
                        'telegram': {
                            'enabled': False,
                            'bot_token': '',
                            'chat_id': ''
                        }
                    }
                }
            }
        }
