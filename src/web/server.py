"""
Flask Backend for Senthium Web Dashboard
Real-time monitoring with WebSocket updates
"""

import logging
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import eventlet

from ipc.channel import IPCClient
from utils.activity_log import ActivityLogger
from rules.schema import ConfigSchema

# Patch for eventlet
eventlet.monkey_patch()

# Initialize Flask app
app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')
app.config['SECRET_KEY'] = 'senthium-web-dashboard-secret-key'
CORS(app)

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

logger = logging.getLogger(__name__)


class DashboardManager:
    """Manages dashboard state and updates"""
    
    def __init__(self):
        self.ipc_client = IPCClient()
        self.activity_logger = ActivityLogger()
        self.config_path = Path.cwd() / 'config' / 'config.yaml'
        self.last_status = None
        
    def get_daemon_status(self) -> Dict:
        """Get current daemon status via IPC"""
        try:
            response = self.ipc_client.send_command('STATUS')
            if response and response.get('success'):
                return {
                    'online': True,
                    'state': response.get('state', 'unknown'),
                    'uptime': response.get('uptime', 0),
                    'active_since': response.get('active_since'),
                    'matched_rules': response.get('matched_rules', []),
                    'wrapper_locked': response.get('wrapper_locked', False)
                }
            else:
                return {'online': False, 'state': 'offline'}
        except Exception as e:
            logger.error(f"Failed to get daemon status: {e}")
            return {'online': False, 'state': 'error', 'error': str(e)}
    
    def get_daemon_info(self) -> Dict:
        """Get daemon system info"""
        try:
            response = self.ipc_client.send_command('INFO')
            if response and response.get('success'):
                return response.get('info', {})
            return {}
        except Exception as e:
            logger.error(f"Failed to get daemon info: {e}")
            return {}
    
    def get_activity_stats(self, days: int = 7) -> Dict:
        """Get activity statistics"""
        try:
            # Get weekly summary
            summary = self.activity_logger.get_weekly_summary()
            
            # Format for dashboard
            stats = {
                'total_sessions': 0,
                'total_duration': 0,
                'by_day': [],
                'by_rule': [],
                'by_trigger': []
            }
            
            for day_summary in summary:
                stats['total_sessions'] += day_summary['session_count']
                stats['total_duration'] += day_summary['total_duration']
                
                stats['by_day'].append({
                    'date': day_summary['date'],
                    'sessions': day_summary['session_count'],
                    'duration': day_summary['total_duration']
                })
            
            # Get top rules from most recent day
            if summary:
                latest = summary[-1]
                stats['by_rule'] = [
                    {'name': name, 'duration': dur, 'count': count}
                    for name, dur, count in latest['by_rule'][:5]
                ]
                stats['by_trigger'] = [
                    {'type': ttype, 'duration': dur, 'count': count}
                    for ttype, dur, count in latest['by_trigger']
                ]
            
            return stats
        except Exception as e:
            logger.error(f"Failed to get activity stats: {e}")
            return {}
    
    def get_config_rules(self) -> List[Dict]:
        """Load rules from config file"""
        try:
            validator = ConfigSchema()
            config = validator.load_and_validate(self.config_path)
            rules = config['senthium']['rules']
            
            return [
                {
                    'name': rule['name'],
                    'type': rule['type'],
                    'enabled': rule.get('enabled', True),
                    'description': rule.get('description', '')
                }
                for rule in rules
            ]
        except Exception as e:
            logger.error(f"Failed to load config rules: {e}")
            return []
    
    def control_daemon(self, action: str) -> Dict:
        """Control daemon (start/stop)"""
        # For now, return placeholder
        # Actual implementation would use subprocess to call CLI
        return {
            'success': False,
            'message': 'Daemon control not yet implemented from web UI'
        }


# Global dashboard manager
dashboard = DashboardManager()


# ==========================================
# Web Routes
# ==========================================

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')


@app.route('/api/status')
def api_status():
    """Get current daemon status"""
    status = dashboard.get_daemon_status()
    info = dashboard.get_daemon_info()
    
    return jsonify({
        'status': status,
        'info': info,
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/activity')
def api_activity():
    """Get activity statistics"""
    days = request.args.get('days', 7, type=int)
    stats = dashboard.get_activity_stats(days)
    
    return jsonify(stats)


@app.route('/api/rules')
def api_rules():
    """Get configured rules"""
    rules = dashboard.get_config_rules()
    return jsonify(rules)


@app.route('/api/control/<action>', methods=['POST'])
def api_control(action: str):
    """Control daemon (start/stop/restart)"""
    result = dashboard.control_daemon(action)
    return jsonify(result)


# ==========================================
# WebSocket Events
# ==========================================

@socketio.on('connect')
def handle_connect():
    """Client connected"""
    logger.info("Dashboard client connected")
    emit('connected', {'message': 'Connected to Senthium'})
    
    # Send initial status
    status = dashboard.get_daemon_status()
    emit('status_update', status)


@socketio.on('disconnect')
def handle_disconnect():
    """Client disconnected"""
    logger.info("Dashboard client disconnected")


@socketio.on('request_status')
def handle_status_request():
    """Client requests status update"""
    status = dashboard.get_daemon_status()
    emit('status_update', status)


def broadcast_status():
    """Broadcast status updates to all connected clients"""
    status = dashboard.get_daemon_status()
    socketio.emit('status_update', status)


# ==========================================
# Background Tasks
# ==========================================

def background_status_updater():
    """Background task to broadcast status updates"""
    while True:
        eventlet.sleep(2)  # Update every 2 seconds
        try:
            status = dashboard.get_daemon_status()
            
            # Only broadcast if status changed
            if status != dashboard.last_status:
                dashboard.last_status = status
                socketio.emit('status_update', status)
        except Exception as e:
            logger.error(f"Error in status updater: {e}")


# ==========================================
# App Factory
# ==========================================

def create_app():
    """Create and configure Flask app"""
    return app


def run_dashboard(host: str = '127.0.0.1', port: int = 5000, debug: bool = False):
    """Run the dashboard server"""
    logger.info(f"Starting Senthium Web Dashboard on {host}:{port}")
    
    # Start background updater
    eventlet.spawn(background_status_updater)
    
    # Run socketio server
    socketio.run(app, host=host, port=port, debug=debug)


if __name__ == '__main__':
    from utils.logger import setup_logger
    setup_logger('senthium.web', level='DEBUG')
    
    print("🌐 Senthium Web Dashboard")
    print("=" * 60)
    print("Starting server on http://127.0.0.1:5000")
    print("Press Ctrl+C to stop")
    print()
    
    run_dashboard(debug=True)
