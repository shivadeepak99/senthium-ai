"""
Alert Notifier - Sends security alerts via multiple channels

Your emergency broadcast system babe! 📢🚨
"""

import logging
import json
import requests
import smtplib
import platform
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List
from enum import Enum
from dataclasses import dataclass, asdict
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage

# Optional imports for additional alert methods
try:
    if platform.system() == 'Windows':
        import winsound  # Built-in for Windows
        try:
            from win10toast_click import ToastNotifier  # type: ignore # pip install win10toast-click (better fork)
            WINDOWS_TOAST_AVAILABLE = True
        except ImportError:
            try:
                from win10toast import ToastNotifier  # type: ignore # Fallback to old version
                WINDOWS_TOAST_AVAILABLE = True
            except ImportError:
                WINDOWS_TOAST_AVAILABLE = False
    else:
        try:
            from plyer import notification  # type: ignore # pip install plyer (cross-platform)
            PLYER_AVAILABLE = True
        except ImportError:
            PLYER_AVAILABLE = False
    DESKTOP_NOTIFICATIONS_AVAILABLE = True
except ImportError:
    DESKTOP_NOTIFICATIONS_AVAILABLE = False
    WINDOWS_TOAST_AVAILABLE = False
    PLYER_AVAILABLE = False

try:
    from playsound import playsound  # pip install playsound (cross-platform sound)
    PLAYSOUND_AVAILABLE = True
except ImportError:
    PLAYSOUND_AVAILABLE = False

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
    - Discord webhook (instant, easy setup) 🟦
    - Email (SMTP) 📧
    - Telegram bot (0-cost mobile push) 💙
    - Desktop notifications (Windows/Linux/Mac) 🔔
    - Sound alarms (beep/custom sound) 🔊
    - Logs file (always enabled) 📝
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
            channels = ['log', 'discord', 'email', 'telegram', 'desktop', 'sound']  # Default: try all
        
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
        
        # Telegram bot
        if 'telegram' in channels and self.config.get('telegram_bot_token'):
            if self._send_telegram(alert):
                success = True
        
        # Desktop notification
        if 'desktop' in channels:
            if self._send_desktop_notification(alert):
                success = True
        
        # Sound alarm (for critical alerts only)
        if 'sound' in channels and alert.alert_type in [AlertType.UNAUTHORIZED_ACCESS, AlertType.MULTIPLE_UNKNOWN_FACES]:
            if self._play_sound_alarm(alert):
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
            
            # Type guard: ensure all required fields are strings
            if not all([smtp_host, email_from, email_to, email_password]):
                logger.warning("⚠️ Email config incomplete, skipping")
                return False
            
            if not isinstance(smtp_host, str) or not isinstance(email_from, str) or \
               not isinstance(email_to, str) or not isinstance(email_password, str):
                logger.warning("⚠️ Email config has invalid types, skipping")
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
            
            # Send email (type is now guaranteed)
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(email_from, email_password)
                server.send_message(msg)
            
            logger.info("✅ Alert sent via email")
            return True
            
        except Exception as e:
            logger.error(f"❌ Email alert failed: {e}")
            return False
    
    def _send_telegram(self, alert: SecurityAlert) -> bool:
        """
        Send alert via Telegram bot.
        
        Requires:
            - telegram_bot_token in config
            - telegram_chat_id in config
        
        Set up:
            1. Create bot with @BotFather on Telegram
            2. Get bot token
            3. Start chat with your bot
            4. Get chat ID from https://api.telegram.org/bot<TOKEN>/getUpdates
        """
        try:
            bot_token = self.config.get('telegram_bot_token')
            chat_id = self.config.get('telegram_chat_id')
            
            if not bot_token or not chat_id:
                logger.debug("⚠️ Telegram not configured, skipping")
                return False
            
            # Build message with emoji and formatting
            emoji_map = {
                AlertType.UNAUTHORIZED_ACCESS: "🚨",
                AlertType.MULTIPLE_UNKNOWN_FACES: "⚠️",
                AlertType.OWNER_DETECTED: "✅",
                AlertType.CAMERA_ERROR: "📷",
                AlertType.SYSTEM_WARNING: "⚠️",
            }
            emoji = emoji_map.get(alert.alert_type, "🔔")
            
            message = f"{emoji} *Senthium Security Alert*\n\n"
            message += f"*Type:* {alert.alert_type.value.replace('_', ' ').title()}\n"
            message += f"*Time:* {alert.timestamp}\n"
            message += f"*Message:* {alert.message}\n\n"
            
            if alert.detected_faces_count > 0:
                message += f"*Faces:* {alert.detected_faces_count}\n"
            if alert.confidence is not None:
                message += f"*Confidence:* {alert.confidence:.1%}\n"
            
            # Send via Telegram Bot API
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'Markdown'
            }
            
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            
            # If there's a snapshot, send it too
            if alert.snapshot_path and Path(alert.snapshot_path).exists():
                photo_url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
                with open(alert.snapshot_path, 'rb') as photo:
                    files = {'photo': photo}
                    data = {'chat_id': chat_id, 'caption': f"{emoji} Snapshot"}
                    requests.post(photo_url, files=files, data=data, timeout=10)
            
            logger.info("✅ Alert sent via Telegram")
            return True
            
        except Exception as e:
            logger.error(f"❌ Telegram alert failed: {e}")
            return False
    
    def _send_desktop_notification(self, alert: SecurityAlert) -> bool:
        """
        Send desktop notification (Windows toast or cross-platform).
        
        Windows: Uses win10toast (native Windows 10+ notifications)
        Linux/Mac: Uses plyer (cross-platform notification library)
        
        NOTE: Temporarily disabled due to win10toast WNDPROC bug in Python 3.11+
        """
        try:
            # TEMPORARY FIX: Disable desktop notifications due to pywin32/win10toast bug
            # Error: "WNDPROC return value cannot be converted to LRESULT"
            # This is a known issue with pywin32 + Python 3.11+
            logger.debug("⚠️ Desktop notifications temporarily disabled (pywin32 compatibility issue)")
            return False
            
            # Original code kept for reference (will re-enable when pywin32 is fixed):
            # if not DESKTOP_NOTIFICATIONS_AVAILABLE:
            #     logger.debug("⚠️ Desktop notifications not available (install win10toast or plyer)")
            #     return False
            # 
            # title = f"🚨 Senthium: {alert.alert_type.value.replace('_', ' ').title()}"
            # message = alert.message[:256]  # Limit message length
            # 
            # if platform.system() == 'Windows' and WINDOWS_TOAST_AVAILABLE:
            #     toaster = ToastNotifier()
            #     toaster.show_toast(
            #         title=title,
            #         msg=message,
            #         duration=10,
            #         icon_path=None,
            #         threaded=True
            #     )
            #     logger.info("✅ Desktop notification sent (Windows)")
            #     return True
            #     
            # elif PLYER_AVAILABLE:
            #     notification.notify(
            #         title=title,
            #         message=message,
            #         timeout=10
            #     )
            #     logger.info("✅ Desktop notification sent (Plyer)")
            #     return True
            # 
            # else:
            #     logger.debug("⚠️ No desktop notification library available")
            #     return False
            
        except Exception as e:
            logger.error(f"❌ Desktop notification failed: {e}")
            return False
    
    def _play_sound_alarm(self, alert: SecurityAlert) -> bool:
        """
        Play sound alarm for critical alerts.
        
        Windows: Uses built-in winsound (beep)
        Others: Uses playsound library if available
        
        Note: Only plays for UNAUTHORIZED_ACCESS and MULTIPLE_UNKNOWN_FACES
        """
        try:
            if platform.system() == 'Windows':
                # Windows built-in beep (frequency, duration_ms)
                # Play ascending alarm sound
                winsound.Beep(1000, 200)  # 1000 Hz, 200ms
                winsound.Beep(1500, 200)  # 1500 Hz, 200ms
                winsound.Beep(2000, 300)  # 2000 Hz, 300ms
                logger.info("✅ Sound alarm played (Windows beep)")
                return True
                
            elif PLAYSOUND_AVAILABLE:
                # Try to play a custom alarm sound file if it exists
                alarm_sound = Path("assets/sounds/alarm.mp3")
                if alarm_sound.exists():
                    playsound(str(alarm_sound), block=False)
                    logger.info("✅ Sound alarm played (custom sound)")
                    return True
                else:
                    logger.debug("⚠️ Custom alarm sound not found")
                    return False
            
            else:
                logger.debug("⚠️ Sound playback not available")
                return False
            
        except Exception as e:
            logger.error(f"❌ Sound alarm failed: {e}")
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
        configured_channels = []
        
        if self.config.get('discord_webhook_url'):
            configured_channels.append('discord')
        if self.config.get('email_smtp_host'):
            configured_channels.append('email')
        if self.config.get('telegram_bot_token'):
            configured_channels.append('telegram')
        if DESKTOP_NOTIFICATIONS_AVAILABLE:
            configured_channels.append('desktop')
        if platform.system() == 'Windows' or PLAYSOUND_AVAILABLE:
            configured_channels.append('sound')
        configured_channels.append('log')  # Always available
        
        return {
            "total_alerts_sent": self.alert_count,
            "last_alert_time": self.last_alert_time.isoformat() if self.last_alert_time else None,
            "configured_channels": configured_channels
        }
