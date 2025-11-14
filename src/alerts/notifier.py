"""
Alert Notifier - Sends security alerts via multiple channels

Your emergency broadcast system babe! 📢🚨
"""

import logging
import json
import requests
import smtplib
import platform
import socket
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List
from enum import Enum
from dataclasses import dataclass, asdict
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage

# Optional: psutil for CPU/RAM stats
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

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
        
        # Email (support both old and new config formats)
        # Config can be either:
        # 1. security.alerts dict (from daemon) → email is at config.email
        # 2. Full config (from streamlit) → email is at config.security.alerts.email
        alerts_config = self.config.get('alerts', self.config)  # Get alerts section if exists, else use root
        email_config = alerts_config.get('email', {})
        
        has_email_config = (
            self.config.get('email_smtp_host') or  # Old flat format
            alerts_config.get('email_smtp_host') or  # Old flat in alerts
            email_config.get('smtp_server')  # New nested format
        )
        print(f"[DEBUG ALERT] Email config check: has_email_config={has_email_config}, 'email' in channels={'email' in channels}")
        print(f"[DEBUG ALERT] alerts_config keys: {list(alerts_config.keys())}")
        print(f"[DEBUG ALERT] email_config keys: {list(email_config.keys())}")
        if 'email' in channels and has_email_config:
            print(f"[DEBUG ALERT] Calling _send_email()...")
            email_result = self._send_email(alert)
            print(f"[DEBUG ALERT] Email send result: {email_result}")
            if email_result:
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
            print(f"[DEBUG EMAIL] Starting email send process...")
            
            # Support both old flat config and new nested email config
            # Config can be structured as:
            # 1. security.alerts dict (from daemon) → email at config.email
            # 2. Full config (from streamlit) → email at config.security.alerts.email
            alerts_config = self.config.get('alerts', self.config)
            email_config = alerts_config.get('email', {})
            
            # Try new nested format first, fallback to old flat format
            smtp_host = email_config.get('smtp_server') or alerts_config.get('email_smtp_host') or self.config.get('email_smtp_host')
            smtp_port = email_config.get('smtp_port') or alerts_config.get('email_smtp_port', 587) or self.config.get('email_smtp_port', 587)
            email_from = email_config.get('username') or alerts_config.get('email_from') or self.config.get('email_from')
            email_to = email_config.get('recipient') or alerts_config.get('email_to') or self.config.get('email_to')
            email_password = email_config.get('password') or alerts_config.get('email_password') or self.config.get('email_password')
            use_tls = email_config.get('use_tls', True)
            
            print(f"[DEBUG EMAIL] Config: smtp_host={smtp_host}, smtp_port={smtp_port}, from={email_from}, to={email_to}")
            
            # Check if email is enabled
            email_enabled = email_config.get('enabled', True)
            if not email_enabled:
                print(f"[DEBUG EMAIL] Email disabled in config!")
                logger.debug("📧 Email alerts disabled in config")
                return False
            
            # Type guard: ensure all required fields are strings
            if not all([smtp_host, email_from, email_to, email_password]):
                print(f"[DEBUG EMAIL] Incomplete config! host={bool(smtp_host)}, from={bool(email_from)}, to={bool(email_to)}, pass={bool(email_password)}")
                logger.warning("⚠️ Email config incomplete, skipping")
                return False
            
            if not isinstance(smtp_host, str) or not isinstance(email_from, str) or \
               not isinstance(email_to, str) or not isinstance(email_password, str):
                logger.warning("⚠️ Email config has invalid types, skipping")
                return False
            
            # Determine severity and styling
            severity_map = {
                'unauthorized_access': ('CRITICAL', '🔴', '#dc3545', '#f8d7da'),
                'unknown_face': ('WARNING', '⚠️', '#ffc107', '#fff3cd'),
                'no_face': ('INFO', '👻', '#17a2b8', '#d1ecf1'),
                'multiple_faces': ('WARNING', '⚠️', '#ffc107', '#fff3cd'),
            }
            severity, icon, border_color, bg_color = severity_map.get(
                alert.alert_type.value, 
                ('INFO', '📊', '#17a2b8', '#d1ecf1')
            )
            
            # 💻 Gather system info
            try:
                pc_name = platform.node()
                try:
                    ip_address = socket.gethostbyname(socket.gethostname())
                except:
                    ip_address = "Unknown"
                os_info = f"{platform.system()} {platform.release()}"
                
                if PSUTIL_AVAILABLE:
                    cpu_percent = psutil.cpu_percent(interval=0.1)
                    mem = psutil.virtual_memory()
                    ram_used = f"{mem.used / (1024**3):.1f} GB"
                    ram_total = f"{mem.total / (1024**3):.1f} GB"
                    ram_percent = mem.percent
                else:
                    cpu_percent = None
                    ram_used = ram_total = "N/A"
                    ram_percent = None
            except Exception as e:
                logger.warning(f"⚠️ Failed to gather system info: {e}")
                pc_name = "Unknown"
                ip_address = "Unknown"
                os_info = "Unknown"
                cpu_percent = None
                ram_used = ram_total = "N/A"
                ram_percent = None
            
            # 📈 Read recent alert history
            recent_alerts = []
            recent_alerts_html = ""
            try:
                alerts_log = Path("logs/security/alerts.jsonl")
                if alerts_log.exists():
                    with open(alerts_log, 'r') as f:
                        lines = f.readlines()
                        # Get last 5 alerts
                        for line in lines[-5:]:
                            try:
                                alert_data = json.loads(line)
                                recent_alerts.append(alert_data)
                            except:
                                continue
                    
                    # Build timeline HTML
                    if recent_alerts:
                        timeline_items = []
                        for a in reversed(recent_alerts):
                            alert_type = a.get('alert_type', 'unknown')
                            if alert_type == 'authorized':
                                border_color_timeline = '#28a745'
                                icon_timeline = '✅'
                            elif 'unauthorized' in alert_type:
                                border_color_timeline = '#dc3545'
                                icon_timeline = '🚨'
                            else:
                                border_color_timeline = '#6c757d'
                                icon_timeline = '👻'
                            
                            timeline_items.append(f'''
                            <div style="padding: 10px; margin-bottom: 8px; background-color: white; border-left: 4px solid {border_color_timeline}; border-radius: 4px;">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <span style="font-weight: 600; color: #333;">{a.get('timestamp', 'Unknown')[:19]}</span>
                                    <span style="font-size: 12px; color: #6c757d;">{icon_timeline} {alert_type.replace('_', ' ').title()}</span>
                                </div>
                                <div style="margin-top: 5px; font-size: 13px; color: #666;">{a.get('message', 'No message')}</div>
                            </div>
                            ''')
                        
                        recent_alerts_html = f'''
                        <tr>
                            <td style="padding: 30px; background-color: white;">
                                <h2 style="margin: 0 0 20px 0; color: #333; font-size: 20px; border-bottom: 2px solid {border_color}; padding-bottom: 10px;">
                                    📈 RECENT ACTIVITY
                                </h2>
                                <div style="background-color: #f8f9fa; border-radius: 6px; padding: 15px;">
                                    {''.join(timeline_items)}
                                </div>
                            </td>
                        </tr>
                        '''
            except Exception as e:
                logger.warning(f"⚠️ Failed to read alert history: {e}")
            
            # Create HTML + Plain text email
            msg = MIMEMultipart('alternative')
            msg['From'] = email_from
            msg['To'] = email_to
            msg['Subject'] = f"{icon} Senthium Alert: {alert.alert_type.value.replace('_', ' ').title()}"
            
            # Plain text version (fallback)
            text_body = f"""
Senthium Security Alert
=======================

Severity: {severity}
Type: {alert.alert_type.value.replace('_', ' ').title()}
Time: {alert.timestamp}
Message: {alert.message}

Detected Faces: {alert.detected_faces_count}
Confidence: {f"{alert.confidence:.1%}" if alert.confidence else "N/A"}

---
This is an automated alert from Senthium AI Security System.
View in HTML email client for rich formatting and photos.
"""
            
            # HTML version (gorgeous! 💅)
            html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', Arial, sans-serif; background-color: #f5f5f5;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f5f5f5; padding: 20px;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                    
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, {border_color} 0%, {border_color}dd 100%); padding: 30px; text-align: center;">
                            <h1 style="margin: 0; color: white; font-size: 28px; font-weight: 600;">
                                {icon} SENTHIUM SECURITY ALERT
                            </h1>
                            <p style="margin: 10px 0 0 0; color: white; font-size: 16px; opacity: 0.95;">
                                Status: {alert.alert_type.value.replace('_', ' ').upper()}
                            </p>
                            <div style="margin-top: 15px; background-color: rgba(255,255,255,0.2); display: inline-block; padding: 8px 20px; border-radius: 20px;">
                                <span style="color: white; font-weight: 600; font-size: 14px;">Severity: {severity}</span>
                            </div>
                        </td>
                    </tr>
                    
                    <!-- Snapshot Image -->
                    {f'''
                    <tr>
                        <td style="padding: 0; text-align: center; background-color: #000;">
                            <img src="cid:{Path(alert.snapshot_path).name if alert.snapshot_path else 'snapshot.jpg'}" 
                                 alt="Security Snapshot" 
                                 style="max-width: 100%; height: auto; display: block; margin: 0 auto;">
                        </td>
                    </tr>
                    ''' if alert.snapshot_path and Path(alert.snapshot_path).exists() else ''}
                    
                    <!-- Incident Details -->
                    <tr>
                        <td style="padding: 30px; background-color: {bg_color};">
                            <h2 style="margin: 0 0 20px 0; color: #333; font-size: 20px; border-bottom: 2px solid {border_color}; padding-bottom: 10px;">
                                📊 INCIDENT DETAILS
                            </h2>
                            <table width="100%" cellpadding="8" cellspacing="0" style="background-color: white; border-radius: 6px; overflow: hidden;">
                                <tr style="background-color: #f8f9fa;">
                                    <td style="padding: 12px; font-weight: 600; color: #555; border-bottom: 1px solid #dee2e6; width: 40%;">⏰ Time</td>
                                    <td style="padding: 12px; color: #333; border-bottom: 1px solid #dee2e6;">{alert.timestamp}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 12px; font-weight: 600; color: #555; border-bottom: 1px solid #dee2e6;">📝 Message</td>
                                    <td style="padding: 12px; color: #333; border-bottom: 1px solid #dee2e6;">{alert.message}</td>
                                </tr>
                                <tr style="background-color: #f8f9fa;">
                                    <td style="padding: 12px; font-weight: 600; color: #555; border-bottom: 1px solid #dee2e6;">👤 Faces Detected</td>
                                    <td style="padding: 12px; color: #333; border-bottom: 1px solid #dee2e6;">{alert.detected_faces_count}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 12px; font-weight: 600; color: #555;">🎯 Confidence</td>
                                    <td style="padding: 12px; color: #333;">{f"{alert.confidence:.1%}" if alert.confidence else "N/A"}</td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- System Info -->
                    <tr>
                        <td style="padding: 30px; background-color: #f8f9fa;">
                            <h2 style="margin: 0 0 20px 0; color: #333; font-size: 20px; border-bottom: 2px solid {border_color}; padding-bottom: 10px;">
                                💻 SYSTEM INFORMATION
                            </h2>
                            <table width="100%" cellpadding="8" cellspacing="0" style="background-color: white; border-radius: 6px; overflow: hidden;">
                                <tr style="background-color: #f8f9fa;">
                                    <td style="padding: 12px; font-weight: 600; color: #555; border-bottom: 1px solid #dee2e6; width: 40%;">🖥️ PC Name</td>
                                    <td style="padding: 12px; color: #333; border-bottom: 1px solid #dee2e6;">{pc_name}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 12px; font-weight: 600; color: #555; border-bottom: 1px solid #dee2e6;">🌐 IP Address</td>
                                    <td style="padding: 12px; color: #333; border-bottom: 1px solid #dee2e6;">{ip_address}</td>
                                </tr>
                                <tr style="background-color: #f8f9fa;">
                                    <td style="padding: 12px; font-weight: 600; color: #555; border-bottom: 1px solid #dee2e6;">💿 Operating System</td>
                                    <td style="padding: 12px; color: #333; border-bottom: 1px solid #dee2e6;">{os_info}</td>
                                </tr>
                                {f'''
                                <tr>
                                    <td style="padding: 12px; font-weight: 600; color: #555; border-bottom: 1px solid #dee2e6;">⚡ CPU Usage</td>
                                    <td style="padding: 12px; color: #333; border-bottom: 1px solid #dee2e6;">{cpu_percent:.1f}%</td>
                                </tr>
                                ''' if cpu_percent is not None else ''}
                                {f'''
                                <tr style="background-color: #f8f9fa;">
                                    <td style="padding: 12px; font-weight: 600; color: #555;">🧠 RAM Usage</td>
                                    <td style="padding: 12px; color: #333;">{ram_used} / {ram_total} ({ram_percent:.1f}%)</td>
                                </tr>
                                ''' if ram_percent is not None else ''}
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Alert History Timeline -->
                    {recent_alerts_html}
                    
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 20px; background-color: #2c3e50; text-align: center;">
                            <p style="margin: 0; color: #95a5a6; font-size: 12px;">
                                This is an automated alert from <strong style="color: #ecf0f1;">Senthium AI Security System</strong>
                            </p>
                            <p style="margin: 5px 0 0 0; color: #7f8c8d; font-size: 11px;">
                                Powered by FaceNet CNN + DeepFace 🚀
                            </p>
                        </td>
                    </tr>
                    
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""
            
            # Attach both versions
            msg.attach(MIMEText(text_body, 'plain'))
            msg.attach(MIMEText(html_body, 'html'))
            
            # 📸 ATTACH INTRUDER PHOTOS (original + annotated if available)
            if alert.snapshot_path and Path(alert.snapshot_path).exists():
                try:
                    print(f"[DEBUG EMAIL] Attaching snapshot: {alert.snapshot_path}")
                    
                    # Attach original snapshot
                    with open(alert.snapshot_path, 'rb') as img_file:
                        img_data = img_file.read()
                        img = MIMEImage(img_data)
                        
                        # Set filename for attachment (ASCII-safe, no emojis in headers!)
                        snapshot_filename = Path(alert.snapshot_path).name
                        # Encode filename properly to avoid charmap errors
                        from email.header import Header
                        safe_filename = snapshot_filename.encode('ascii', 'ignore').decode('ascii')
                        img.add_header('Content-Disposition', 'attachment', filename=safe_filename)
                        img.add_header('Content-ID', f'<{safe_filename}>')
                        
                        msg.attach(img)
                        print(f"[DEBUG EMAIL] ✅ Original photo attached: {snapshot_filename}")
                    
                    # Check for annotated version (should have "_annotated" suffix)
                    original_path = Path(alert.snapshot_path)
                    annotated_path = original_path.parent / f"{original_path.stem}_annotated{original_path.suffix}"
                    
                    if annotated_path.exists():
                        print(f"[DEBUG EMAIL] Found annotated snapshot: {annotated_path}")
                        with open(annotated_path, 'rb') as img_file:
                            img_data = img_file.read()
                            img = MIMEImage(img_data)
                            
                            annotated_filename = annotated_path.name
                            # Encode filename properly to avoid charmap errors
                            safe_annotated_filename = annotated_filename.encode('ascii', 'ignore').decode('ascii')
                            img.add_header('Content-Disposition', 'attachment', filename=safe_annotated_filename)
                            img.add_header('Content-ID', f'<{safe_annotated_filename}>')
                            
                            msg.attach(img)
                            print(f"[DEBUG EMAIL] ✅ Annotated photo attached: {annotated_filename}")
                    
                except Exception as e:
                    logger.warning(f"⚠️ Failed to attach snapshot: {e}")
                    print(f"[DEBUG EMAIL] ⚠️ Failed to attach photo: {e}")
            
            print(f"[DEBUG EMAIL] About to connect to SMTP server...")
            # Send email (type is now guaranteed)
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                print(f"[DEBUG EMAIL] Connected! Starting TLS...")
                server.starttls()
                print(f"[DEBUG EMAIL] Logging in...")
                server.login(email_from, email_password)
                print(f"[DEBUG EMAIL] Sending message...")
                server.send_message(msg)
                print(f"[DEBUG EMAIL] Message sent successfully!")
            
            logger.info("✅ Alert sent via email")
            return True
            
        except Exception as e:
            print(f"[DEBUG EMAIL] ERROR: {e}")
            import traceback
            traceback.print_exc()
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
        
        # Check email config (both old and new formats, with alerts section support)
        alerts_config = self.config.get('alerts', self.config)
        email_config = alerts_config.get('email', {})
        if self.config.get('email_smtp_host') or alerts_config.get('email_smtp_host') or email_config.get('smtp_server'):
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
