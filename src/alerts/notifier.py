"""
Alert Notifier - Sends security alerts via multiple channels

Your emergency broadcast system babe! 📢🚨
"""

import logging
import json
import requests
import smtplib
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List
from enum import Enum
from dataclasses import dataclass, asdict
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage


logger = logging.getLogger(__name__)


class AlertType(Enum):
    """Types of security alerts"""
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    MULTIPLE_UNKNOWN_FACES = "multiple_unknown_faces"
    OWNER_DETECTED = "owner_detected"  # For testing/confirmation
    CAMERA_ERROR = "camera_error"
    SYSTEM_WARNING = "system_warning"


@dataclass
class SecurityAlert:
    """Represents a security alert event"""
    timestamp: str
    alert_type: AlertType
    message: str
    confidence: Optional[float] = None
    snapshot_path: Optional[str] = None
    detected_faces_count: int = 0
    
    def to_dict(self) -> dict:
        """Convert to dict for JSON serialization"""
        data = asdict(self)
        data['alert_type'] = self.alert_type.value
        return data


class AlertNotifier:
    """
    Sends security alerts through multiple channels.
    
    Can send via:
    - Discord webhook (instant, easy setup)
    - Email (SMTP)
    - Telegram bot (future)
    - Logs file (always enabled)
    """
    
    def __init__(
        self,
        alerts_log_file: str = "logs/security/alerts.jsonl",
        config: Optional[Dict] = None
    ):
        """
        Initialize alert notifier.
        
        Args:
            alerts_log_file: Path to JSONL file for alert logging
            config: Alert configuration dict with keys:
                    - discord_webhook_url
                    - email_smtp_host, email_smtp_port, email_from, email_to, email_password
        """
        self.alerts_log_file = Path(alerts_log_file)
        self.config = config or {}
        self.alert_count = 0
        self.last_alert_time: Optional[datetime] = None
        
        # Ensure log directory exists
        self.alerts_log_file.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info("🚨 Alert notifier initialized")
    
    def send_alert(
        self,
        alert: SecurityAlert,
        channels: Optional[List[str]] = None
    ) -> bool:
        """
        Send security alert through configured channels.
        
        Args:
            alert: SecurityAlert object to send
            channels: List of channels to use (default: all configured)
                      Options: 'discord', 'email', 'log'
        
        Returns:
            True if at least one channel succeeded
        """
        if channels is None:
            channels = ['log', 'discord', 'email']  # Default: try all
        
        self.alert_count += 1
        self.last_alert_time = datetime.now()
        
        success = False
        
        # Always log to file
        if 'log' in channels:
            if self._log_to_file(alert):
                success = True
        
        # Discord webhook
        if 'discord' in channels and self.config.get('discord_webhook_url'):
            if self._send_discord(alert):
                success = True
        
        # Email
        if 'email' in channels and self.config.get('email_smtp_host'):
            if self._send_email(alert):
                success = True
        
        return success
    
    def _log_to_file(self, alert: SecurityAlert) -> bool:
        """Log alert to JSONL file."""
        try:
            with open(self.alerts_log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(alert.to_dict()) + '\n')
            
            logger.debug(f"📝 Alert logged to {self.alerts_log_file.name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to log alert: {e}")
            return False
    
    def _send_discord(self, alert: SecurityAlert) -> bool:
        """Send alert via Discord webhook."""
        try:
            webhook_url = self.config.get('discord_webhook_url')
            if not webhook_url:
                return False
            
            # Build Discord embed (fancy message)
            color = {
                AlertType.UNAUTHORIZED_ACCESS: 0xFF0000,  # Red
                AlertType.MULTIPLE_UNKNOWN_FACES: 0xFF6600,  # Orange
                AlertType.OWNER_DETECTED: 0x00FF00,  # Green
                AlertType.CAMERA_ERROR: 0xFFFF00,  # Yellow
                AlertType.SYSTEM_WARNING: 0xFFFF00,  # Yellow
            }.get(alert.alert_type, 0x0099FF)  # Blue default
            
            embed = {
                "title": f"🚨 {alert.alert_type.value.replace('_', ' ').title()}",
                "description": alert.message,
                "color": color,
                "timestamp": alert.timestamp,
                "fields": []
            }
            
            if alert.confidence is not None:
                embed["fields"].append({
                    "name": "Confidence",
                    "value": f"{alert.confidence:.1%}",
                    "inline": True
                })
            
            if alert.detected_faces_count > 0:
                embed["fields"].append({
                    "name": "Faces Detected",
                    "value": str(alert.detected_faces_count),
                    "inline": True
                })
            
            payload = {
                "embeds": [embed],
                "username": "Senthium Security"
            }
            
            # Send webhook
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            
            logger.info("✅ Alert sent via Discord")
            return True
            
        except Exception as e:
            logger.error(f"❌ Discord webhook failed: {e}")
            return False
    
    def _send_email(self, alert: SecurityAlert) -> bool:
        """Send alert via email (SMTP)."""
        try:
            smtp_host = self.config.get('email_smtp_host')
            smtp_port = self.config.get('email_smtp_port', 587)
            email_from = self.config.get('email_from')
            email_to = self.config.get('email_to')
            email_password = self.config.get('email_password')
            
            if not all([smtp_host, email_from, email_to, email_password]):
                logger.warning("⚠️ Email config incomplete, skipping")
                return False
            
            # Create email
            msg = MIMEMultipart()
            msg['From'] = email_from
            msg['To'] = email_to
            msg['Subject'] = f"🚨 Senthium Alert: {alert.alert_type.value.replace('_', ' ').title()}"
            
            # Email body
            body = f"""
Senthium Security Alert
=======================

Type: {alert.alert_type.value.replace('_', ' ').title()}
Time: {alert.timestamp}
Message: {alert.message}

Detected Faces: {alert.detected_faces_count}
Confidence: {f"{alert.confidence:.1%}" if alert.confidence else "N/A"}

---
This is an automated alert from Senthium AI Security System.
"""
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(email_from, email_password)
                server.send_message(msg)
            
            logger.info("✅ Alert sent via email")
            return True
            
        except Exception as e:
            logger.error(f"❌ Email alert failed: {e}")
            return False
    
    def should_send_alert(self, cooldown_seconds: int = 300) -> bool:
        """
        Check if enough time has passed since last alert (prevents spam).
        
        Args:
            cooldown_seconds: Minimum seconds between alerts (default: 5 minutes)
        
        Returns:
            True if alert should be sent
        """
        if self.last_alert_time is None:
            return True
        
        elapsed = (datetime.now() - self.last_alert_time).total_seconds()
        return elapsed >= cooldown_seconds
    
    def get_recent_alerts(self, max_count: int = 50) -> List[Dict]:
        """
        Get recent alerts from log file.
        
        Args:
            max_count: Maximum number of alerts to return
        
        Returns:
            List of alert dicts (most recent first)
        """
        if not self.alerts_log_file.exists():
            return []
        
        try:
            alerts = []
            with open(self.alerts_log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        alerts.append(json.loads(line))
            
            # Return most recent first
            return alerts[-max_count:][::-1]
            
        except Exception as e:
            logger.error(f"❌ Failed to read alerts: {e}")
            return []
    
    def get_stats(self) -> dict:
        """Get alert statistics."""
        return {
            "total_alerts_sent": self.alert_count,
            "last_alert_time": self.last_alert_time.isoformat() if self.last_alert_time else None,
            "configured_channels": [
                'discord' if self.config.get('discord_webhook_url') else None,
                'email' if self.config.get('email_smtp_host') else None,
                'log'
            ]
        }
