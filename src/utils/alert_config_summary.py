"""
Alert Configuration Summary Generator
Saves a human-readable summary of all alert settings
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any


class AlertConfigSummary:
    """Generates and saves alert configuration summaries"""
    
    def __init__(self, summary_file: str = "config/alert_settings_summary.json"):
        self.summary_file = Path(summary_file)
        self.summary_file.parent.mkdir(parents=True, exist_ok=True)
    
    def generate_summary(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a human-readable summary of alert configurations
        
        Args:
            config: Full Senthium config dict
            
        Returns:
            Summary dict with alert channel statuses
        """
        alerts_config = config.get('senthium', {}).get('security', {}).get('alerts', {})
        
        summary = {
            "generated_at": datetime.now().isoformat(),
            "version": config.get('senthium', {}).get('version', 'unknown'),
            "alert_channels": {}
        }
        
        # Discord
        discord = alerts_config.get('discord', {})
        summary['alert_channels']['discord'] = {
            "enabled": discord.get('enabled', False),
            "configured": bool(discord.get('webhook_url', '')),
            "webhook_set": "Yes" if discord.get('webhook_url') else "No"
        }
        
        # Email
        email = alerts_config.get('email', {})
        summary['alert_channels']['email'] = {
            "enabled": email.get('enabled', False),
            "configured": bool(email.get('smtp_server') and email.get('username')),
            "smtp_server": email.get('smtp_server', 'Not set'),
            "smtp_port": email.get('smtp_port', 587),
            "username": email.get('username', 'Not set'),
            "recipient": email.get('recipient', 'Not set'),
            "use_tls": email.get('use_tls', True)
        }
        
        # Telegram
        telegram = alerts_config.get('telegram', {})
        summary['alert_channels']['telegram'] = {
            "enabled": telegram.get('enabled', False),
            "configured": bool(telegram.get('bot_token') and telegram.get('chat_id')),
            "bot_token_set": "Yes" if telegram.get('bot_token') else "No",
            "chat_id_set": "Yes" if telegram.get('chat_id') else "No"
        }
        
        # Desktop/System
        summary['alert_channels']['desktop'] = {
            "toast_notifications": alerts_config.get('desktop_notification', True),
            "sound_alerts": alerts_config.get('sound_alert', False),
            "log_to_file": alerts_config.get('log_to_file', True)
        }
        
        # Overall status
        active_channels = []
        if summary['alert_channels']['discord']['enabled']:
            active_channels.append('Discord')
        if summary['alert_channels']['email']['enabled']:
            active_channels.append('Email')
        if summary['alert_channels']['telegram']['enabled']:
            active_channels.append('Telegram')
        if summary['alert_channels']['desktop']['toast_notifications']:
            active_channels.append('Desktop Notifications')
        
        summary['summary'] = {
            "total_active_channels": len(active_channels),
            "active_channels": active_channels,
            "any_alerts_enabled": len(active_channels) > 0
        }
        
        return summary
    
    def save_summary(self, config: Dict[str, Any]) -> bool:
        """
        Generate and save alert configuration summary
        
        Args:
            config: Full Senthium config dict
            
        Returns:
            True if saved successfully
        """
        try:
            summary = self.generate_summary(config)
            
            with open(self.summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            
            print(f"📋 DEBUG: Alert config summary saved to {self.summary_file}")
            return True
            
        except Exception as e:
            print(f"❌ DEBUG: Failed to save alert summary: {e}")
            return False
    
    def load_summary(self) -> Dict[str, Any]:
        """Load existing summary file"""
        if not self.summary_file.exists():
            return {"error": "Summary file not found"}
        
        try:
            with open(self.summary_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            return {"error": str(e)}
    
    def print_summary(self, config: Dict[str, Any]) -> str:
        """Generate a pretty text summary"""
        summary = self.generate_summary(config)
        
        lines = []
        lines.append("="*50)
        lines.append("📢 ALERT CONFIGURATION SUMMARY")
        lines.append("="*50)
        lines.append(f"Generated: {summary['generated_at']}")
        lines.append(f"Version: {summary['version']}")
        lines.append("")
        
        lines.append("🔔 Active Alert Channels:")
        if summary['summary']['active_channels']:
            for channel in summary['summary']['active_channels']:
                lines.append(f"  ✅ {channel}")
        else:
            lines.append("  ⚠️ No alert channels enabled!")
        
        lines.append("")
        lines.append("📊 Detailed Channel Status:")
        lines.append("")
        
        # Discord
        discord = summary['alert_channels']['discord']
        status = "✅ ENABLED" if discord['enabled'] else "❌ DISABLED"
        lines.append(f"💜 Discord: {status}")
        lines.append(f"   Webhook configured: {discord['webhook_set']}")
        lines.append("")
        
        # Email
        email = summary['alert_channels']['email']
        status = "✅ ENABLED" if email['enabled'] else "❌ DISABLED"
        lines.append(f"✉️ Email: {status}")
        lines.append(f"   Server: {email['smtp_server']}:{email['smtp_port']}")
        lines.append(f"   From: {email['username']}")
        lines.append(f"   To: {email['recipient']}")
        lines.append("")
        
        # Telegram
        telegram = summary['alert_channels']['telegram']
        status = "✅ ENABLED" if telegram['enabled'] else "❌ DISABLED"
        lines.append(f"💬 Telegram: {status}")
        lines.append(f"   Bot token configured: {telegram['bot_token_set']}")
        lines.append(f"   Chat ID configured: {telegram['chat_id_set']}")
        lines.append("")
        
        # Desktop
        desktop = summary['alert_channels']['desktop']
        lines.append(f"🖥️ Desktop Notifications: {'✅' if desktop['toast_notifications'] else '❌'}")
        lines.append(f"🔊 Sound Alerts: {'✅' if desktop['sound_alerts'] else '❌'}")
        lines.append(f"📝 Log to File: {'✅' if desktop['log_to_file'] else '❌'}")
        
        lines.append("="*50)
        
        return "\n".join(lines)
