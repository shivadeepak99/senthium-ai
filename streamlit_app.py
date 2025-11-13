"""
🔒 Senthium AI Security - Streamlit Dashboard
Simple, beautiful GUI for AI-powered face recognition security

Run with: streamlit run streamlit_app.py
"""

import streamlit as st
import sys
from pathlib import Path
from PIL import Image
import json
from datetime import datetime
import os
import time
import requests  # For testing webhooks
import psutil  # For system monitoring
import cv2  # For video processing
import numpy as np  # For numerical operations

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.vision.security_manager import SecurityManager
from src.rules.schema import ConfigSchema
from src.daemon.control import start_daemon, stop_daemon, daemon_status, restart_daemon
from src.utils.config_manager import ConfigManager
from src.utils.pid import PIDFile

# Page config
st.set_page_config(
    page_title="Senthium AI Security",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for beautiful styling
st.markdown("""
<style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem;
        border-radius: 0.5rem;
        font-weight: 600;
        transition: transform 0.2s;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 20px rgba(0,0,0,0.2);
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 1rem;
        color: white;
        text-align: center;
    }
    .alert-card {
        padding: 1.25rem;
        border-radius: 0.75rem;
        margin: 0.75rem 0;
        border-left: 5px solid;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        color: #1a1a1a;
        font-size: 0.95rem;
    }
    .alert-threat {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);
        border-color: #c92a2a;
        color: white;
    }
    .alert-authorized {
        background: linear-gradient(135deg, #51cf66 0%, #37b24d 100%);
        border-color: #2f9e44;
        color: white;
    }
    .alert-card strong {
        font-size: 1.1rem;
        display: block;
        margin-bottom: 0.5rem;
    }
    .alert-card small {
        opacity: 0.9;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'security_manager' not in st.session_state:
    config_path = Path("config/config.yaml")
    try:
        validator = ConfigSchema()
        config = validator.load_and_validate(config_path)
        st.session_state.security_manager = SecurityManager(config)
        st.session_state.config_manager = ConfigManager(str(config_path))
        st.session_state.config_loaded = True
    except Exception as e:
        st.session_state.config_loaded = False
        st.session_state.error = str(e)


with st.sidebar:
    st.image("https://via.placeholder.com/200x100/667eea/ffffff?text=SENTHIUM")
    st.title("🔒 Senthium AI")
    st.markdown("### Navigation")
    
    page = st.radio(
        "Choose a page:",
        ["📊 Dashboard", "📈 System Monitor", "🎓 AI Training", "👤 Face Enrollment", "🔍 Security Check", "📈 Forensics Timeline", "🔍 Intruder Patterns", "👻 Haunting Mode", "⚙️ Settings"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    st.markdown("### Quick Stats")
    
    if st.session_state.config_loaded:
        try:
            stats = st.session_state.security_manager.get_stats()
            
            # Safety check for None stats FIRST
            if not stats or not isinstance(stats, dict):
                stats = {
                    'total_checks': 0,
                    'threats_detected': 0,
                    'authorized_users_count': 0
                }
            
            # Check if security is actually enabled in config
            config = st.session_state.config_manager._config
            
            # Safety check for config being None
            if not config or not isinstance(config, dict):
                security_enabled = False
                security_config = {}
            else:
                security_config = config.get('senthium', {}).get('security', {})
                security_enabled = security_config.get('enabled', False)
            
            # Debug: Show what we're actually reading
            # st.write(f"DEBUG: security_enabled = {security_enabled}, config keys = {list(security_config.keys())}")
            
            st.metric("System Status", "🟢 ACTIVE" if security_enabled else "🔴 Disabled")
            
            # Daemon status indicator
            pid_file = PIDFile()
            is_daemon_running = pid_file.is_running()
            daemon_pid = pid_file.get_pid() if is_daemon_running else None
            daemon_status = "🟢 Running" if is_daemon_running else "🔴 Stopped"
            
            # Show PID if running
            if is_daemon_running and daemon_pid:
                st.metric("Daemon Status", f"{daemon_status} (PID: {daemon_pid})")
            else:
                st.metric("Daemon Status", daemon_status)
            
            st.metric("Total Checks", stats.get('total_checks', 0))
            st.metric("Threats Detected", stats.get('threats_detected', 0))
            st.metric("Authorized Users", stats.get('authorized_users_count', 0))
        except Exception as e:
            st.error(f"Error loading stats: {e}")
    
    st.markdown("---")
    st.markdown("**Version:** v0.6.0")
    st.markdown("**Status:** Running ✅")

# Main content area
if not st.session_state.config_loaded:
    st.error("❌ Failed to load configuration")
    st.error(st.session_state.error)
    st.stop()

# ==================== DASHBOARD PAGE ====================
if page == "📊 Dashboard":
    st.title("📊 Enhanced Security Dashboard")
    st.markdown("Real-time overview of your AI security system with state monitoring")
    
    # Top row: State badge + Pause button
    col_badge, col_pause = st.columns([3, 1])
    
    with col_badge:
        # Get current state - prioritize daemon state over session state
        try:
            pid_file = PIDFile()
            is_daemon_running = pid_file.is_running()
            
            # Check config for security enabled
            config = st.session_state.config_manager._config
            
            # Safety check for config being None
            if not config or not isinstance(config, dict):
                current_state = "IDLE"
                status_message = "Configuration not loaded"
            else:
                security_enabled = config.get('senthium', {}).get('security', {}).get('enabled', False)
                
                # Determine actual current state
                if not is_daemon_running:
                    current_state = "IDLE"  # Daemon not running
                    status_message = "Daemon stopped - start for 24/7 monitoring"
                elif not security_enabled:
                    current_state = "PAUSED"  # Security disabled
                    status_message = "Security disabled in config"
                else:
                    # Get state from security manager (only if enabled)
                    stats = st.session_state.security_manager.get_stats()
                    if stats and isinstance(stats, dict):
                        current_state = stats.get('current_state', 'MONITORING')
                        status_message = "Actively monitoring for threats"
                    else:
                        current_state = "MONITORING"
                        status_message = "Initializing security system..."
            
            # State badge with emoji and color
            state_emojis = {
                "AUTHORIZED": "🟢",
                "MONITORING": "🔵", 
                "NO_FACE": "👻",
                "GRACE": "⏳",
                "UNAUTHORIZED": "🔴",
                "LOCKED": "🔒",
                "PAUSED": "⏸️",
                "ACTIVE": "🟢",
                "IDLE": "⚪"
            }
            
            state_colors = {
                "AUTHORIZED": "#28a745",  # Green
                "MONITORING": "#17a2b8",  # Blue
                "NO_FACE": "#6c757d",     # Gray
                "GRACE": "#ffc107",       # Yellow
                "UNAUTHORIZED": "#dc3545", # Red
                "LOCKED": "#343a40",      # Dark
                "PAUSED": "#6c757d",      # Gray
                "ACTIVE": "#28a745",      # Green
                "IDLE": "#adb5bd"         # Light gray
            }
            
            emoji = state_emojis.get(current_state, "⚪")
            color = state_colors.get(current_state, "#6c757d")
            
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, {color} 0%, {color}CC 100%);
                padding: 1.5rem 2rem;
                border-radius: 1rem;
                color: white;
                text-align: center;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            ">
                <h1 style="margin: 0; font-size: 3rem;">{emoji}</h1>
                <h2 style="margin: 0.5rem 0 0 0;">CURRENT STATE: {current_state}</h2>
                <p style="margin: 0.5rem 0 0 0; opacity: 0.9; font-size: 0.9rem;">{status_message}</p>
                <p style="margin: 0.3rem 0 0 0; opacity: 0.7; font-size: 0.8rem;">Last update: {datetime.now().strftime("%H:%M:%S")}</p>
            </div>
            """, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Error loading state: {e}")
    
    with col_pause:
        st.markdown("<br>", unsafe_allow_html=True)  # Spacing
        
        # Pause/Resume button
        is_paused = st.session_state.get('system_paused', False)
        pause_duration = st.session_state.get('pause_duration', 10)
        
        if not is_paused:
            if st.button("⏸️ Pause Monitoring", key="pause_btn", help="Temporarily disable monitoring"):
                # Show pause duration selector
                st.session_state['show_pause_options'] = True
        else:
            pause_until = st.session_state.get('pause_until', datetime.now())
            remaining = (pause_until - datetime.now()).total_seconds()
            if remaining > 0:
                st.warning(f"⏸️ PAUSED\n\n{int(remaining)}s remaining")
                if st.button("▶️ Resume Now", key="resume_btn"):
                    st.session_state['system_paused'] = False
                    st.success("✅ Monitoring resumed!")
                    st.rerun()
            else:
                # Auto-resume
                st.session_state['system_paused'] = False
                st.rerun()
        
        # Pause duration selector
        if st.session_state.get('show_pause_options', False):
            st.selectbox(
                "Pause duration:",
                options=[10, 30, 60, 300, 600],
                format_func=lambda x: f"{x//60}m {x%60}s" if x >= 60 else f"{x}s",
                key="pause_duration_select"
            )
            
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("✅ Confirm", key="confirm_pause"):
                    from datetime import timedelta
                    duration = st.session_state.get('pause_duration_select', 10)
                    st.session_state['system_paused'] = True
                    st.session_state['pause_until'] = datetime.now() + timedelta(seconds=duration)
                    st.session_state['show_pause_options'] = False
                    st.success(f"⏸️ Paused for {duration}s!")
                    st.rerun()
            with col_b:
                if st.button("❌ Cancel", key="cancel_pause"):
                    st.session_state['show_pause_options'] = False
                    st.rerun()
    
    st.markdown("---")
    
    # ===== DAEMON CONTROLS & SYSTEM STATS =====
    st.subheader("🎛️ System Control & Monitoring")
    
    # Row 1: Daemon Controls
    col_daemon1, col_daemon2 = st.columns([2, 1])
    
    with col_daemon1:
        pid_file = PIDFile()
        is_running = pid_file.is_running()
        daemon_pid = pid_file.get_pid() if is_running else None
        
        if is_running:
            st.success(f"🟢 **Background Daemon Running** (PID: {daemon_pid})")
            st.caption("Continuously monitoring system 24/7")
        else:
            st.error("🔴 **Background Daemon Stopped**")
            st.caption("Start daemon for automatic monitoring")
    
    with col_daemon2:
        # Daemon control buttons
        btn_col1, btn_col2, btn_col3 = st.columns(3)
        
        with btn_col1:
            if st.button("▶️ Start", key="start_daemon_btn", use_container_width=True, 
                        disabled=is_running, help="Start background monitoring"):
                with st.spinner("Starting daemon..."):
                    try:
                        result = start_daemon(
                            config_path="config/config.yaml",
                            log_level="INFO",
                            foreground=False
                        )
                        if result == 0:
                            st.success("✅ Daemon started!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("❌ Failed to start daemon")
                    except Exception as e:
                        st.error(f"Error: {e}")
        
        with btn_col2:
            if st.button("⏹️ Stop", key="stop_daemon_btn", use_container_width=True,
                        disabled=not is_running, help="Stop background monitoring"):
                with st.spinner("Stopping daemon..."):
                    try:
                        result = stop_daemon()
                        if result == 0:
                            st.success("✅ Daemon stopped!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("❌ Failed to stop daemon")
                    except Exception as e:
                        st.error(f"Error: {e}")
        
        with btn_col3:
            if st.button("🔄 Restart", key="restart_daemon_btn", use_container_width=True,
                        disabled=not is_running, help="Restart daemon (apply config changes)"):
                with st.spinner("Restarting daemon..."):
                    try:
                        result = restart_daemon(
                            config_path="config/config.yaml",
                            log_level="INFO"
                        )
                        if result == 0:
                            st.success("✅ Daemon restarted!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("❌ Failed to restart daemon")
                    except Exception as e:
                        st.error(f"Error: {e}")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Row 2: System Performance Metrics
    st.markdown("### 📊 Live System Performance")
    
    sys_col1, sys_col2, sys_col3, sys_col4 = st.columns(4)
    
    try:
        # Get real-time system metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk_io = psutil.disk_io_counters()
        net_io = psutil.net_io_counters()
        
        # Calculate delta (simplified - you can enhance this with history)
        with sys_col1:
            st.metric(
                label="💻 CPU Usage",
                value=f"{cpu_percent:.1f}%",
                delta=f"+{cpu_percent - 50:.1f}%" if cpu_percent > 50 else f"{cpu_percent - 50:.1f}%",
                help="Current CPU utilization"
            )
        
        with sys_col2:
            st.metric(
                label="🧠 Memory",
                value=f"{memory.percent:.1f}%",
                delta=f"{memory.available / (1024**3):.1f}GB free",
                help=f"Using {memory.used / (1024**3):.1f}GB of {memory.total / (1024**3):.1f}GB"
            )
        
        with sys_col3:
            disk_read_mb = disk_io.read_bytes / (1024**2)
            disk_write_mb = disk_io.write_bytes / (1024**2)
            st.metric(
                label="💾 Disk I/O",
                value=f"{(disk_read_mb + disk_write_mb) / 1024:.2f}GB",
                delta=f"↓{disk_read_mb / 1024:.2f}GB ↑{disk_write_mb / 1024:.2f}GB",
                help="Total disk read/write since boot"
            )
        
        with sys_col4:
            net_sent_mb = net_io.bytes_sent / (1024**2)
            net_recv_mb = net_io.bytes_recv / (1024**2)
            st.metric(
                label="🌐 Network I/O",
                value=f"{(net_sent_mb + net_recv_mb) / 1024:.2f}GB",
                delta=f"↓{net_recv_mb / 1024:.2f}GB ↑{net_sent_mb / 1024:.2f}GB",
                help="Total network traffic since boot"
            )
    except Exception as e:
        st.error(f"Error loading system metrics: {e}")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Row 3: Active Rules Display
    st.markdown("### 📋 Active Sleep Prevention Rules")
    
    try:
        config_manager = st.session_state.config_manager
        config = config_manager._config
        rules = config.get('senthium', {}).get('rules', [])
        
        if rules:
            rules_col1, rules_col2 = st.columns(2)
            
            enabled_rules = [r for r in rules if r.get('enabled', False)]
            disabled_rules = [r for r in rules if not r.get('enabled', False)]
            
            with rules_col1:
                st.markdown("**✅ Enabled Rules:**")
                if enabled_rules:
                    for rule in enabled_rules:
                        rule_type = rule.get('type', 'unknown')
                        rule_name = rule.get('name', 'Unnamed')
                        
                        type_icons = {
                            'process': '🖥️',
                            'cpu': '💻',
                            'disk': '💾',
                            'network': '🌐',
                            'schedule': '⏰',
                            'combined': '🔗'
                        }
                        
                        icon = type_icons.get(rule_type, '📌')
                        st.info(f"{icon} **{rule_name}** ({rule_type})")
                else:
                    st.warning("No enabled rules")
            
            with rules_col2:
                st.markdown("**⏸️ Disabled Rules:**")
                if disabled_rules:
                    for rule in disabled_rules:
                        rule_type = rule.get('type', 'unknown')
                        rule_name = rule.get('name', 'Unnamed')
                        st.text(f"⚪ {rule_name} ({rule_type})")
                else:
                    st.success("All rules enabled!")
        else:
            st.warning("⚠️ No rules configured. System will not prevent sleep automatically.")
    except Exception as e:
        st.error(f"Error loading rules: {e}")
    
    st.markdown("---")
    
    # Live Stats Row (4 metrics)
    col1, col2, col3, col4 = st.columns(4)
    
    try:
        stats = st.session_state.security_manager.get_stats()
        recognizer_stats = st.session_state.security_manager.recognizer.get_stats()
        
        # Safety check for None
        if not stats or not isinstance(stats, dict):
            stats = {'total_checks': 0, 'threats_detected': 0}
        if not recognizer_stats or not isinstance(recognizer_stats, dict):
            recognizer_stats = {'total_faces': 0}
        
        with col1:
            uptime_seconds = int(time.time() - st.session_state.get('start_time', time.time()))
            uptime_str = f"{uptime_seconds // 3600}h {(uptime_seconds % 3600) // 60}m"
            
            st.markdown(f"""
            <div class="metric-card">
                <h3>⏱️ Uptime</h3>
                <h2>{uptime_str}</h2>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            total_checks = stats.get('total_checks', 0)
            st.markdown(f"""
            <div class="metric-card">
                <h3>🔍 Total Checks</h3>
                <h2>{total_checks}</h2>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            threats = stats.get('threats_detected', 0)
            st.markdown(f"""
            <div class="metric-card">
                <h3>🚨 Alerts</h3>
                <h2>{threats}</h2>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            total_faces = recognizer_stats.get('total_faces', 0)
            st.markdown(f"""
            <div class="metric-card">
                <h3>👥 Enrolled Faces</h3>
                <h2>{total_faces}</h2>
            </div>
            """, unsafe_allow_html=True)
    
    except Exception as e:
        st.error(f"Error loading stats: {e}")
    
    # Add start_time to session state if not present
    if 'start_time' not in st.session_state:
        st.session_state['start_time'] = time.time()
    
    st.markdown("---")
    
    # Recent Alerts (same as before, but with better formatting)
    st.subheader("🚨 Recent Alerts")
    
    alerts_file = Path("logs/security/alerts.jsonl")
    if alerts_file.exists():
        try:
            with open(alerts_file, 'r') as f:
                alerts = [json.loads(line) for line in f.readlines()[-10:]]  # Last 10 alerts
            
            if alerts:
                for alert in reversed(alerts):  # Show newest first
                    alert_type = alert.get('alert_type', 'unknown')
                    is_threat = alert_type == 'unauthorized_access'
                    alert_class = "alert-threat" if is_threat else "alert-authorized"
                    icon = "⚠️" if is_threat else "✅"
                    
                    # Format timestamp nicely
                    timestamp = alert.get('timestamp', 'Unknown time')
                    if 'T' in timestamp:
                        timestamp = timestamp.split('T')[1].split('.')[0]  # Get time only
                    
                    message = alert.get('message', 'No message')
                    faces_count = alert.get('detected_faces_count', 0)
                    
                    st.markdown(f"""
                    <div class="alert-card {alert_class}">
                        <strong>{icon} {timestamp}</strong><br>
                        {message}<br>
                        <small>Detected faces: {faces_count}</small>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No alerts yet. Perform a security check to see alerts here.")
        except Exception as e:
            st.error(f"Error loading alerts: {e}")
    else:
        st.info("No alerts file found. Perform a security check first.")
    
    # Latest Snapshots Gallery (show 3 most recent)
    st.markdown("---")
    st.subheader("📸 Latest Snapshots")
    
    snapshots_dir = Path("logs/security/snapshots")
    if snapshots_dir.exists():
        snapshots = sorted(snapshots_dir.glob("*.jpg"), key=lambda x: x.stat().st_mtime, reverse=True)
        if snapshots:
            # Show top 3 in columns
            snapshot_cols = st.columns(min(3, len(snapshots)))
            for idx, (col, snapshot) in enumerate(zip(snapshot_cols, snapshots[:3])):
                with col:
                    st.image(str(snapshot), caption=f"Snapshot {idx + 1}")
                    st.caption(snapshot.name)
        else:
            st.info("No snapshots available yet.")
    else:
        st.info("No snapshots directory found.")

# ==================== SYSTEM MONITOR PAGE ====================
elif page == "📈 System Monitor":
    st.title("📈 Real-Time System Monitor")
    st.markdown("Live performance metrics and process monitoring")
    
    # Auto-refresh
    st_autorefresh = st.empty()
    with st_autorefresh:
        st.caption("🔄 Auto-refreshing every 2 seconds...")
    
    # System Performance Gauges
    st.subheader("💻 System Performance")
    
    try:
        # Get real-time metrics
        cpu_percent = psutil.cpu_percent(interval=0.5, percpu=False)
        cpu_per_core = psutil.cpu_percent(interval=0.5, percpu=True)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        disk_io = psutil.disk_io_counters()
        net_io = psutil.net_io_counters()
        
        # Row 1: Main Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "💻 CPU Usage",
                f"{cpu_percent:.1f}%",
                delta=f"{'High' if cpu_percent > 70 else 'Normal'}" if cpu_percent > 50 else "Low",
                help=f"Average across {len(cpu_per_core)} cores"
            )
        
        with col2:
            st.metric(
                "🧠 Memory",
                f"{memory.percent:.1f}%",
                delta=f"{memory.available / (1024**3):.1f}GB free",
                help=f"Using {memory.used / (1024**3):.1f}GB / {memory.total / (1024**3):.1f}GB"
            )
        
        with col3:
            st.metric(
                "💾 Disk Usage",
                f"{disk.percent:.1f}%",
                delta=f"{disk.free / (1024**3):.0f}GB free",
                help=f"Using {disk.used / (1024**3):.0f}GB / {disk.total / (1024**3):.0f}GB"
            )
        
        with col4:
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot_time
            uptime_hours = int(uptime.total_seconds() / 3600)
            st.metric(
                "⏱️ System Uptime",
                f"{uptime_hours}h",
                delta=f"{uptime.days} days",
                help=f"Booted at {boot_time.strftime('%Y-%m-%d %H:%M:%S')}"
            )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Row 2: CPU Per-Core Usage
        st.subheader("🔥 CPU Per-Core Usage")
        
        if len(cpu_per_core) <= 16:
            cores_per_row = 4
        else:
            cores_per_row = 8
        
        cores_cols = st.columns(cores_per_row)
        for idx, core_usage in enumerate(cpu_per_core):
            with cores_cols[idx % cores_per_row]:
                color = "🟢" if core_usage < 50 else "🟡" if core_usage < 80 else "🔴"
                st.metric(f"{color} Core {idx}", f"{core_usage:.0f}%")
        
        st.markdown("---")
        
        # Row 3: Disk & Network I/O
        st.subheader("📊 I/O Statistics")
        
        io_col1, io_col2 = st.columns(2)
        
        with io_col1:
            st.markdown("### 💾 Disk I/O (Since Boot)")
            disk_read_gb = disk_io.read_bytes / (1024**3)
            disk_write_gb = disk_io.write_bytes / (1024**3)
            
            st.metric("📥 Read", f"{disk_read_gb:.2f} GB")
            st.metric("📤 Write", f"{disk_write_gb:.2f} GB")
            st.metric("📊 Total", f"{disk_read_gb + disk_write_gb:.2f} GB")
        
        with io_col2:
            st.markdown("### 🌐 Network I/O (Since Boot)")
            net_recv_gb = net_io.bytes_recv / (1024**3)
            net_sent_gb = net_io.bytes_sent / (1024**3)
            
            st.metric("📥 Received", f"{net_recv_gb:.2f} GB")
            st.metric("📤 Sent", f"{net_sent_gb:.2f} GB")
            st.metric("📊 Total", f"{net_recv_gb + net_sent_gb:.2f} GB")
        
        st.markdown("---")
        
        # Row 4: Process List
        st.subheader("🖥️ Top Processes by CPU")
        
        # Get all processes
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
            try:
                pinfo = proc.info
                if pinfo['cpu_percent'] is not None and pinfo['cpu_percent'] > 0:
                    processes.append(pinfo)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # Sort by CPU usage
        processes = sorted(processes, key=lambda x: x['cpu_percent'], reverse=True)[:20]
        
        # Display as table
        if processes:
            # Create table data
            import pandas as pd
            df = pd.DataFrame(processes)
            df = df[['name', 'pid', 'cpu_percent', 'memory_percent', 'status']]
            df.columns = ['Process Name', 'PID', 'CPU %', 'Memory %', 'Status']
            df['CPU %'] = df['CPU %'].round(1)
            df['Memory %'] = df['Memory %'].round(1)
            
            # Add search
            search = st.text_input("🔍 Search processes:", placeholder="e.g., python, chrome, code")
            
            if search:
                df = df[df['Process Name'].str.contains(search, case=False, na=False)]
            
            st.dataframe(
                df,
                use_container_width=True,
                height=400
            )
            
            st.caption(f"Showing top {len(df)} processes (filtered by CPU usage > 0%)")
        else:
            st.info("No active processes found")
        
        # Auto-refresh trigger
        time.sleep(2)
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Error loading system metrics: {e}")
        st.exception(e)

# ==================== AI TRAINING PAGE ====================
elif page == "🎓 AI Training":
    st.title("🎓 AI Training - Dynamic Face Learning")
    st.markdown("**Train the AI model with 1-minute video capture for optimal recognition accuracy**")
    
    st.info("""
    ### 🧠 How AI Training Works:
    
    **This is the "training phase" where the AI learns your face:**
    
    1. **📹 Video Capture**: Record a 1-minute video while moving your head
    2. **🔍 Face Detection**: AI detects your face in every frame (600-1000 frames)
    3. **🎯 Multi-Angle Learning**: Captures different angles, lighting, expressions
    4. **🧮 Embedding Generation**: FaceNet CNN generates 128-dimensional vectors
    5. **📊 Fine-Tuning**: AI averages best encodings for robust recognition
    6. **💾 Model Update**: Your personalized face model is saved
    
    **Why 1 minute?** More data = better accuracy! The AI learns to recognize you across:
    - Different head angles (left, right, up, down)
    - Various lighting conditions
    - Multiple facial expressions
    - Temporal face variations
    """)
    
    st.markdown("---")
    
    # Training configuration
    st.subheader("🎯 Training Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        user_name = st.text_input(
            "👤 Your Name",
            placeholder="e.g., John Doe",
            help="Enter the name for this training session"
        )
        
        training_duration = st.selectbox(
            "⏱️ Training Duration",
            options=[30, 60, 90, 120],
            index=1,
            format_func=lambda x: f"{x} seconds ({x//60}m {x%60}s)" if x >= 60 else f"{x} seconds",
            help="Longer duration = more training data"
        )
    
    with col2:
        fps_target = st.slider(
            "📷 Capture Rate (FPS)",
            min_value=5,
            max_value=15,
            value=10,
            help="Frames per second to capture (10 FPS = 600 frames in 60s)"
        )
        
        st.metric(
            "Expected Frames",
            f"~{training_duration * fps_target} frames",
            help="Total training samples to collect"
        )
    
    st.markdown("---")
    
    # Training instructions
    st.subheader("📋 Training Instructions")
    
    st.success("""
    **During the 1-minute training:**
    
    ✅ **DO:**
    - Look directly at the camera initially
    - Slowly turn your head left and right
    - Tilt your head up and down
    - Make natural facial expressions
    - Stay within camera frame
    - Ensure good lighting
    
    ❌ **DON'T:**
    - Move too fast (AI needs clear frames)
    - Block your face with hands
    - Wear sunglasses/masks
    - Leave the camera view
    """)
    
    # Training button
    st.markdown("<br>", unsafe_allow_html=True)
    
    if not user_name:
        st.warning("⚠️ Please enter your name to start training")
    else:
        col_start, col_stop = st.columns([1, 3])
        
        with col_start:
            start_training = st.button(
                "🚀 Start AI Training",
                type="primary",
                use_container_width=True,
                help=f"Begin {training_duration}s training session",
                disabled=not user_name
            )
        
        if start_training:
            # Initialize training session
            st.session_state['training_active'] = True
            st.session_state['training_user'] = user_name
            st.session_state['training_duration'] = training_duration
            st.session_state['training_fps'] = fps_target
            st.rerun()
    
    # Training execution
    if st.session_state.get('training_active', False):
        st.markdown("---")
        st.subheader("🎬 Live Training Session")
        
        # Training progress area
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Video preview
        video_placeholder = st.empty()
        
        # Metrics
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        
        with col_m1:
            frames_captured_metric = st.empty()
        with col_m2:
            faces_detected_metric = st.empty()
        with col_m3:
            quality_metric = st.empty()
        with col_m4:
            time_remaining_metric = st.empty()
        
        # Stop button
        stop_btn = st.button("⏹️ Stop Training", type="secondary")
        
        if stop_btn:
            st.session_state['training_active'] = False
            st.warning("Training cancelled by user")
            st.rerun()
        
        try:
            # Import trainer
            from src.ai.trainer import FaceTrainer
            
            trainer = FaceTrainer(
                user_name=st.session_state['training_user'],
                output_dir="data/training"
            )
            
            # Progress callback
            def update_progress(progress_pct, frame, face_locations):
                """Update UI during training"""
                # Update progress bar
                progress_bar.progress(int(progress_pct))
                
                # Update status
                status_text.markdown(f"### 📹 Training in progress... {progress_pct:.1f}%")
                
                # Draw face boxes on frame
                if len(face_locations) > 0:
                    for (top, right, bottom, left) in face_locations:
                        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 3)
                        cv2.putText(frame, "TRAINING", (left, top - 10),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                
                # Show frame
                video_placeholder.image(frame, channels="BGR", use_container_width=True)
                
                # Update metrics
                frames_captured_metric.metric("📸 Frames Captured", len(trainer.frames))
                faces_detected_metric.metric("👤 Faces Detected", len(trainer.face_encodings))
                
                if trainer.quality_scores:
                    avg_quality = np.mean(trainer.quality_scores)
                    quality_metric.metric("⭐ Avg Quality", f"{avg_quality:.3f}")
                
                remaining = st.session_state['training_duration'] - (progress_pct / 100 * st.session_state['training_duration'])
                time_remaining_metric.metric("⏱️ Time Left", f"{int(remaining)}s")
            
            # Run training
            with st.spinner("Initializing camera..."):
                stats = trainer.capture_training_video(
                    duration_seconds=st.session_state['training_duration'],
                    fps_target=st.session_state['training_fps'],
                    on_progress=update_progress
                )
            
            # Training complete!
            if stats['success']:
                status_text.success("✅ Training Complete!")
                progress_bar.progress(100)
                
                st.balloons()
                
                # Generate final encoding
                with st.spinner("🧠 Fine-tuning AI model..."):
                    final_encoding = trainer.generate_averaged_encoding(top_n=50)
                    encoding_file = trainer.save_training_data(final_encoding, save_frames=True)
                    report = trainer.get_training_report(stats, final_encoding)
                
                # Show training report
                st.markdown("---")
                st.subheader("📊 Training Report")
                
                col_r1, col_r2, col_r3 = st.columns(3)
                
                with col_r1:
                    st.metric("Total Frames Processed", stats['total_frames'])
                    st.metric("Valid Face Frames", stats['valid_frames'])
                
                with col_r2:
                    st.metric("Capture Success Rate", f"{stats['capture_rate']:.1f}%")
                    st.metric("Average Quality", f"{stats['avg_quality']:.3f}")
                
                with col_r3:
                    st.metric("Actual Duration", f"{stats['duration']:.1f}s")
                    st.metric("Effective FPS", f"{stats['fps']:.1f}")
                
                # Quality assessment
                st.markdown("### 🎯 Training Quality Assessment")
                
                quality_msg = report['quality_assessment']
                
                if "EXCELLENT" in quality_msg:
                    st.success(quality_msg)
                elif "GOOD" in quality_msg:
                    st.success(quality_msg)
                elif "FAIR" in quality_msg:
                    st.warning(quality_msg)
                else:
                    st.error(quality_msg)
                
                # Save to face database
                st.markdown("### 💾 Save to Face Database")
                
                if st.button("✅ Save Trained Model", type="primary"):
                    try:
                        # Load existing face database
                        face_db_path = Path("data/faces/encodings.json")
                        face_db_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        if face_db_path.exists():
                            with open(face_db_path, 'r') as f:
                                face_db = json.load(f)
                        else:
                            face_db = {}
                        
                        # Add new trained face
                        face_db[user_name] = {
                            'name': user_name,
                            'encoding': final_encoding.tolist(),
                            'enrolled_at': datetime.now().isoformat(),
                            'training_method': 'AI_VIDEO_TRAINING',
                            'training_duration': training_duration,
                            'num_frames': stats['valid_frames'],
                            'quality_score': stats['avg_quality']
                        }
                        
                        # Save database
                        with open(face_db_path, 'w') as f:
                            json.dump(face_db, f, indent=2)
                        
                        st.success(f"✅ {user_name}'s trained model saved to database!")
                        st.info(f"📁 Encoding file: {encoding_file}")
                        
                        # Reset training state
                        st.session_state['training_active'] = False
                        time.sleep(2)
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Failed to save: {e}")
                
            else:
                st.error(f"❌ Training Failed: {stats.get('error', 'Unknown error')}")
                st.session_state['training_active'] = False
        
        except Exception as e:
            st.error(f"💥 Training Error: {e}")
            import traceback
            st.code(traceback.format_exc())
            st.session_state['training_active'] = False

# ==================== FACE ENROLLMENT PAGE ====================
elif page == "👤 Face Enrollment":
    st.title("👤 Face Enrollment")
    st.markdown("Add authorized users to the security system")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📷 Multi-Snapshot Enrollment (5-10 photos for better accuracy)")
        
        name = st.text_input("Enter person's name", placeholder="e.g., John Doe")
        
        # Add number of snapshots selector
        num_snapshots = st.slider(
            "Number of snapshots to capture",
            min_value=1,
            max_value=10,
            value=5,
            help="More snapshots = better recognition accuracy! Recommended: 5-7"
        )
        
        # Initialize snapshot collection in session state
        if 'snapshot_collection' not in st.session_state:
            st.session_state['snapshot_collection'] = []
            st.session_state['snapshot_count'] = 0
        
        # Create tabs for different input methods 🎨
        tab1, tab2 = st.tabs(["📸 Capture from Webcam (Multi-Snapshot)", "📁 Upload Image (Single)"])
        
        with tab1:
            st.markdown("### Take multiple photos from different angles/lighting")
            
            # Show progress
            if st.session_state.snapshot_count > 0:
                progress_pct = st.session_state.snapshot_count / num_snapshots
                st.progress(progress_pct, text=f"📸 Captured {st.session_state.snapshot_count}/{num_snapshots} snapshots")
            
            # Instructions
            st.info(f"""
            **Multi-Snapshot Enrollment Instructions:**
            1. Click "📸 Take Photo" below
            2. **Rotate your head slightly** between captures (left, right, up, down)
            3. **Vary lighting** if possible (move closer/farther from window)
            4. Capture {num_snapshots} photos total
            5. Review and enroll!
            
            **Why multi-snapshot?** Better accuracy across different angles and lighting! 🎯
            """)
            
            col_a, col_b, col_c = st.columns([1, 2, 1])
            
            with col_b:
                # Only show capture button if we haven't reached target
                if st.session_state.snapshot_count < num_snapshots:
                    button_text = f"📸 Take Photo ({st.session_state.snapshot_count + 1}/{num_snapshots})"
                    if st.button(button_text, key="capture_btn"):
                        if not name:
                            st.error("⚠️ Please enter a name first!")
                        else:
                            with st.spinner(f"📷 Capturing snapshot {st.session_state.snapshot_count + 1}/{num_snapshots}..."):
                                try:
                                    # Initialize camera if needed
                                    if not st.session_state.security_manager.camera._is_initialized:
                                        st.session_state.security_manager.camera.initialize()
                                    
                                    # Capture frame
                                    frame = st.session_state.security_manager.camera.capture_frame()
                                    
                                    if frame is not None:
                                        # Add to collection
                                        st.session_state.snapshot_collection.append(frame.copy())
                                        st.session_state.snapshot_count += 1
                                        st.session_state['captured_name'] = name
                                        
                                        if st.session_state.snapshot_count >= num_snapshots:
                                            st.success(f"✅ All {num_snapshots} snapshots captured! Review below.")
                                        else:
                                            st.success(f"✅ Snapshot {st.session_state.snapshot_count}/{num_snapshots} captured! Rotate your head and take another.")
                                        
                                        st.rerun()
                                    else:
                                        st.error("❌ Failed to capture image from webcam. Make sure your camera is connected!")
                                
                                except Exception as e:
                                    st.error(f"💥 Camera error: {e}")
                                    import traceback
                                    st.code(traceback.format_exc(), language="python")
                else:
                    st.success(f"🎉 All {num_snapshots} snapshots captured!")
            
            # Show collected snapshots
            if st.session_state.snapshot_collection:
                st.divider()
                st.markdown(f"### 📸 Captured Snapshots ({len(st.session_state.snapshot_collection)}/{num_snapshots})")
                
                # Show snapshots in a grid
                import cv2
                cols_per_row = 3
                for i in range(0, len(st.session_state.snapshot_collection), cols_per_row):
                    cols = st.columns(cols_per_row)
                    for j, col in enumerate(cols):
                        idx = i + j
                        if idx < len(st.session_state.snapshot_collection):
                            with col:
                                rgb_frame = cv2.cvtColor(st.session_state.snapshot_collection[idx], cv2.COLOR_BGR2RGB)
                                st.image(rgb_frame, caption=f"Snapshot {idx + 1}")
                
                # Action buttons
                col_x, col_y, col_z = st.columns(3)
                
                with col_x:
                    if st.button("✅ Enroll All Snapshots", key="enroll_multi"):
                        with st.spinner(f"🎯 Enrolling {len(st.session_state.snapshot_collection)} snapshots for {st.session_state.get('captured_name', name)}..."):
                            try:
                                enrolled_count = 0
                                
                                # Enroll each snapshot
                                for idx, frame in enumerate(st.session_state.snapshot_collection):
                                    # Save temp file
                                    temp_path = Path(f"temp_snapshot_{idx}.jpg")
                                    cv2.imwrite(str(temp_path), frame)
                                    
                                    # Enroll (replace=False to accumulate multiple encodings)
                                    replace = (idx == 0)  # Replace on first, append for rest
                                    success = st.session_state.security_manager.enroll_owner_from_file(
                                        image_path=str(temp_path),
                                        user_name=st.session_state.get('captured_name', name),
                                        replace_existing=replace
                                    )
                                    
                                    # Cleanup
                                    temp_path.unlink(missing_ok=True)
                                    
                                    if success:
                                        enrolled_count += 1
                                
                                # Release camera after enrollment
                                print("[DEBUG] Releasing camera after multi-snapshot enrollment...")
                                st.session_state.security_manager.camera.release()
                                
                                if enrolled_count > 0:
                                    st.success(f"✅ Successfully enrolled {enrolled_count}/{len(st.session_state.snapshot_collection)} snapshots for {st.session_state.get('captured_name', name)}!")
                                    st.balloons()
                                    # Clear collection
                                    st.session_state.snapshot_collection = []
                                    st.session_state.snapshot_count = 0
                                    if 'captured_name' in st.session_state:
                                        del st.session_state['captured_name']
                                    st.rerun()
                                else:
                                    st.error("❌ Enrollment failed - no faces detected in any snapshot")
                            
                            except Exception as e:
                                st.error(f"💥 Enrollment error: {e}")
                                import traceback
                                st.code(traceback.format_exc(), language="python")
                
                with col_y:
                    if st.button("🔄 Start Over", key="restart_capture"):
                        # Release camera
                        print("[DEBUG] Releasing camera for restart...")
                        st.session_state.security_manager.camera.release()
                        # Clear collection
                        st.session_state.snapshot_collection = []
                        st.session_state.snapshot_count = 0
                        st.rerun()
                
                with col_z:
                    if st.session_state.snapshot_count < num_snapshots:
                        if st.button("➕ Add More Snapshots", key="add_more"):
                            st.info("Click '📸 Take Photo' button above to continue capturing!")
            
            # Legacy single capture section removed - now everything is multi-snapshot!
                        del st.session_state['captured_name']
                        st.rerun()
        
        with tab2:
            st.markdown("### Upload an image file")
            uploaded_file = st.file_uploader("Choose an image", type=['jpg', 'jpeg', 'png'])
            
            if uploaded_file is not None:
                # Display preview
                image = Image.open(uploaded_file)
                st.image(image, caption="Preview")
                
                if st.button("🎯 Enroll Face", key="enroll_btn"):
                    if not name:
                        st.error("⚠️ Please enter a name first!")
                    else:
                        with st.spinner("Enrolling face..."):
                            try:
                                # Save uploaded file temporarily
                                temp_path = Path("temp_upload.jpg")
                                with open(temp_path, "wb") as f:
                                    f.write(uploaded_file.getbuffer())
                                
                                # Enroll
                                success = st.session_state.security_manager.enroll_owner_from_file(
                                    image_path=str(temp_path),
                                    user_name=name
                                )
                                
                                # IMPORTANT: Release camera after enrollment (if it was used)!
                                print("[DEBUG] Releasing camera after file upload enrollment...")
                                st.session_state.security_manager.camera.release()
                                
                                # Clean up
                                temp_path.unlink(missing_ok=True)
                                
                                if success:
                                    st.success(f"✅ Successfully enrolled {name}!")
                                    st.balloons()
                                    st.rerun()
                                else:
                                    st.error(f"❌ Enrollment failed - check logs for details")
                            
                            except Exception as e:
                                st.error(f"💥 **Exception:** {e}")
                                import traceback
                                st.code(traceback.format_exc(), language="python")
    
    with col2:
        st.subheader("📋 Enrolled Users")
        
        # Get enrolled users from recognizer
        try:
            enrolled_users = st.session_state.security_manager.recognizer.get_authorized_users()
            
            if enrolled_users:
                st.success(f"✅ **{len(enrolled_users)}** user(s) enrolled")
                
                for user_name in enrolled_users:
                    with st.expander(f"👤 {user_name}"):
                        st.write(f"**Name:** {user_name}")
                        
                        # Get face count for this user
                        face_count = len(st.session_state.security_manager.recognizer.authorized_encodings.get(user_name, []))
                        st.write(f"**Face encodings:** {face_count}")
                        
                        # Remove button
                        if st.button(f"�️ Remove {user_name}", key=f"remove_{user_name}"):
                            if st.session_state.security_manager.recognizer.remove_user(user_name):
                                st.success(f"Removed {user_name}")
                                st.rerun()
                            else:
                                st.error("Failed to remove user")
            else:
                st.warning("⚠️ No users enrolled yet!\n\nEnroll yourself first to start using the system.")
        except Exception as e:
            st.error(f"Error loading enrolled users: {e}")

# ==================== SECURITY CHECK PAGE ====================
elif page == "🔍 Security Check":
    st.title("🔍 Manual Security Check")
    st.markdown("""
    **What does this do?**  
    Captures a photo from your webcam and checks for unauthorized faces.
    
    - ✅ **Authorized**: Face is enrolled in the system
    - ⚠️ **Unauthorized**: Unknown face detected - alert will be sent!
    - ℹ️ **No faces**: Nobody detected in frame
    
    💡 **Tip:** This is a one-time check. For continuous monitoring, use the Daemon in Settings.
    """)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Perform Check")
        
        if st.button("🚀 Run Security Check Now", key="check_btn", help="Capture webcam photo and check for unauthorized faces"):
            with st.spinner("📷 Capturing and analyzing..."):
                try:
                    # Direct function call - no subprocess! 🎯
                    check_result = st.session_state.security_manager.perform_security_check()
                    
                    # IMPORTANT: Release camera after check!
                    print("[DEBUG] Releasing camera after manual security check...")
                    st.session_state.security_manager.camera.release()
                    
                    if check_result:
                        st.success("✅ Security check completed!")
                        
                        # Show results in friendly format
                        unknown_count = check_result.get('unknown_faces_count', 0)
                        detected_count = check_result.get('detected_faces_count', 0)
                        authorized_count = detected_count - unknown_count
                        
                        # Result cards
                        metric_col1, metric_col2, metric_col3 = st.columns(3)
                        
                        with metric_col1:
                            st.metric("Total Faces", detected_count, help="Total faces detected in frame")
                        
                        with metric_col2:
                            st.metric("✅ Authorized", authorized_count, help="Faces recognized as enrolled users")
                        
                        with metric_col3:
                            st.metric("⚠️ Unauthorized", unknown_count, 
                                     delta=f"{'THREAT!' if unknown_count > 0 else 'Safe'}", 
                                     delta_color="inverse",
                                     help="Unknown faces (not enrolled)")
                        
                        st.markdown("---")
                        
                        # Status message
                        if unknown_count > 0:
                            st.error(f"🚨 **SECURITY ALERT!** {unknown_count} unauthorized face(s) detected!")
                            st.warning("Alerts have been sent via configured channels (Discord, etc.)")
                        elif detected_count > 0:
                            st.success(f"✅ **ALL CLEAR!** All {detected_count} detected face(s) are authorized.")
                        else:
                            st.info("ℹ️ **NO FACES DETECTED** - Nobody visible in camera frame")
                        
                        # Detailed results (collapsible)
                        with st.expander("📊 Detailed Results (JSON)"):
                            st.json(check_result)
                    else:
                        st.warning("⚠️ Security check returned no data. Make sure security is enabled!")
                
                except Exception as e:
                    st.error(f"💥 **Exception:** {e}")
                    import traceback
                    st.code(traceback.format_exc(), language="python")
        
        st.markdown("---")
        st.info("💡 **Tip:** Make sure your webcam is connected and not in use by other applications.")
    
    with col2:
        st.subheader("📊 Check Statistics")
        
        try:
            stats = st.session_state.security_manager.get_stats()
            
            # Safety check for None
            if not stats or not isinstance(stats, dict):
                stats = {'total_checks': 0, 'threats_detected': 0, 'last_check_time': 'Never'}
            
            st.metric("Total Checks Performed", stats.get('total_checks', 0))
            st.metric("Threats Detected", stats.get('threats_detected', 0), 
                     delta=f"{stats.get('threats_detected', 0)} threats")
            st.metric("Last Check", stats.get('last_check_time', 'Never'))
        
        except Exception as e:
            st.error(f"Error loading stats: {e}")
    
    # ==================== SNAPSHOT ENCRYPTION GALLERY ====================
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("---")
    st.header("🔐 Snapshot Encryption Gallery")
    st.markdown("*Manage and secure your captured surveillance snapshots*")
    
    # Get snapshots directory
    snapshots_dir = Path("data/snapshots")
    
    if not snapshots_dir.exists():
        st.info("📁 No snapshots directory found. Run security checks to capture snapshots first.")
    else:
        # Get all snapshot files
        all_snapshots = list(snapshots_dir.glob("*.jpg")) + list(snapshots_dir.glob("*.png"))
        encrypted_snapshots = list(snapshots_dir.glob("*.enc"))
        
        # Stats overview
        st.subheader("📊 Snapshot Overview")
        
        stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
        
        with stat_col1:
            st.metric("📷 Total Snapshots", len(all_snapshots) + len(encrypted_snapshots))
        
        with stat_col2:
            st.metric("🔓 Plaintext", len(all_snapshots), 
                     delta="Unencrypted" if len(all_snapshots) > 0 else "Safe",
                     delta_color="inverse")
        
        with stat_col3:
            st.metric("🔐 Encrypted", len(encrypted_snapshots),
                     delta="Protected" if len(encrypted_snapshots) > 0 else "None",
                     delta_color="normal")
        
        with stat_col4:
            encryption_pct = (len(encrypted_snapshots) / (len(all_snapshots) + len(encrypted_snapshots)) * 100) if (len(all_snapshots) + len(encrypted_snapshots)) > 0 else 0
            st.metric("🔒 Encryption %", f"{encryption_pct:.0f}%")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Bulk Operations
        st.subheader("⚡ Bulk Operations")
        
        bulk_col1, bulk_col2, bulk_col3 = st.columns(3)
        
        with bulk_col1:
            if st.button("🔐 Encrypt All Plaintext", 
                        disabled=len(all_snapshots) == 0,
                        help="Encrypt all unencrypted snapshots",
                        use_container_width=True):
                with st.spinner(f"Encrypting {len(all_snapshots)} snapshots..."):
                    try:
                        from src.utils.snapshot_encryption import SnapshotEncryption
                        encryptor = SnapshotEncryption()
                        encrypted_count = 0
                        
                        for snapshot in all_snapshots:
                            try:
                                result = encryptor.encrypt_file(str(snapshot))
                                if result:
                                    # Delete original after successful encryption
                                    snapshot.unlink()
                                    encrypted_count += 1
                            except Exception as e:
                                st.error(f"Failed to encrypt {snapshot.name}: {e}")
                        
                        st.success(f"✅ Encrypted {encrypted_count} snapshots!")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Bulk encryption error: {e}")
        
        with bulk_col2:
            if st.button("🔓 Decrypt All Encrypted",
                        disabled=len(encrypted_snapshots) == 0,
                        help="Decrypt all encrypted snapshots",
                        use_container_width=True):
                with st.spinner(f"Decrypting {len(encrypted_snapshots)} snapshots..."):
                    try:
                        from src.utils.snapshot_encryption import SnapshotEncryption
                        encryptor = SnapshotEncryption()
                        decrypted_count = 0
                        
                        for snapshot in encrypted_snapshots:
                            try:
                                result = encryptor.decrypt_file(str(snapshot))
                                if result:
                                    # Delete encrypted file after successful decryption
                                    snapshot.unlink()
                                    decrypted_count += 1
                            except Exception as e:
                                st.error(f"Failed to decrypt {snapshot.name}: {e}")
                        
                        st.success(f"✅ Decrypted {decrypted_count} snapshots!")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Bulk decryption error: {e}")
        
        with bulk_col3:
            if st.button("🗑️ Delete All Originals",
                        disabled=len(all_snapshots) == 0,
                        help="Delete plaintext snapshots (keep encrypted only)",
                        use_container_width=True,
                        type="secondary"):
                if st.checkbox("⚠️ Confirm deletion", key="confirm_delete_originals"):
                    with st.spinner(f"Deleting {len(all_snapshots)} plaintext files..."):
                        try:
                            deleted_count = 0
                            for snapshot in all_snapshots:
                                try:
                                    snapshot.unlink()
                                    deleted_count += 1
                                except Exception as e:
                                    st.error(f"Failed to delete {snapshot.name}: {e}")
                            
                            st.success(f"✅ Deleted {deleted_count} plaintext snapshots!")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Bulk deletion error: {e}")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Gallery View
        st.subheader("🖼️ Snapshot Gallery")
        
        # Filter options
        filter_col1, filter_col2 = st.columns([1, 3])
        
        with filter_col1:
            view_filter = st.selectbox(
                "Show:",
                ["All Snapshots", "Plaintext Only", "Encrypted Only"],
                help="Filter snapshots by encryption status"
            )
        
        with filter_col2:
            sort_by = st.selectbox(
                "Sort By:",
                ["Newest First", "Oldest First", "Name (A-Z)", "Name (Z-A)"],
                help="Sort order for gallery"
            )
        
        # Apply filters
        if view_filter == "Plaintext Only":
            display_snapshots = all_snapshots
        elif view_filter == "Encrypted Only":
            display_snapshots = encrypted_snapshots
        else:
            display_snapshots = all_snapshots + encrypted_snapshots
        
        # Apply sorting
        if sort_by == "Newest First":
            display_snapshots = sorted(display_snapshots, key=lambda x: x.stat().st_mtime, reverse=True)
        elif sort_by == "Oldest First":
            display_snapshots = sorted(display_snapshots, key=lambda x: x.stat().st_mtime)
        elif sort_by == "Name (A-Z)":
            display_snapshots = sorted(display_snapshots, key=lambda x: x.name)
        else:  # Name (Z-A)
            display_snapshots = sorted(display_snapshots, key=lambda x: x.name, reverse=True)
        
        if not display_snapshots:
            st.info(f"No snapshots found matching filter: {view_filter}")
        else:
            st.caption(f"Showing {len(display_snapshots)} snapshots")
            
            # Display in grid (4 columns)
            cols_per_row = 4
            
            for i in range(0, len(display_snapshots), cols_per_row):
                cols = st.columns(cols_per_row)
                
                for j, col in enumerate(cols):
                    if i + j < len(display_snapshots):
                        snapshot = display_snapshots[i + j]
                        
                        with col:
                            is_encrypted = snapshot.suffix == ".enc"
                            
                            # Show thumbnail or placeholder
                            if is_encrypted:
                                st.markdown("### 🔐")
                                st.caption(f"**{snapshot.name[:20]}...**" if len(snapshot.name) > 20 else f"**{snapshot.name}**")
                                st.caption("🔒 Encrypted")
                            else:
                                try:
                                    img = Image.open(snapshot)
                                    st.image(img, use_container_width=True)
                                    st.caption(f"**{snapshot.name[:20]}...**" if len(snapshot.name) > 20 else f"**{snapshot.name}**")
                                except Exception as e:
                                    st.error(f"Error: {e}")
                            
                            # File info
                            file_size_kb = snapshot.stat().st_size / 1024
                            mod_time = datetime.fromtimestamp(snapshot.stat().st_mtime)
                            st.caption(f"📦 {file_size_kb:.1f} KB")
                            st.caption(f"🕐 {mod_time.strftime('%Y-%m-%d %H:%M')}")
                            
                            # Actions
                            action_col1, action_col2 = st.columns(2)
                            
                            with action_col1:
                                if is_encrypted:
                                    if st.button("🔓", key=f"decrypt_{snapshot.name}", help="Decrypt this file"):
                                        try:
                                            from src.utils.snapshot_encryption import SnapshotEncryption
                                            encryptor = SnapshotEncryption()
                                            result = encryptor.decrypt_file(str(snapshot))
                                            if result:
                                                snapshot.unlink()  # Delete encrypted file
                                                st.success("✅ Decrypted!")
                                                time.sleep(0.5)
                                                st.rerun()
                                        except Exception as e:
                                            st.error(f"❌ {e}")
                                else:
                                    if st.button("🔐", key=f"encrypt_{snapshot.name}", help="Encrypt this file"):
                                        try:
                                            from src.utils.snapshot_encryption import SnapshotEncryption
                                            encryptor = SnapshotEncryption()
                                            result = encryptor.encrypt_file(str(snapshot))
                                            if result:
                                                snapshot.unlink()  # Delete original file
                                                st.success("✅ Encrypted!")
                                                time.sleep(0.5)
                                                st.rerun()
                                        except Exception as e:
                                            st.error(f"❌ {e}")
                            
                            with action_col2:
                                if st.button("🗑️", key=f"delete_{snapshot.name}", help="Delete this file"):
                                    try:
                                        snapshot.unlink()
                                        st.success("✅ Deleted!")
                                        time.sleep(0.5)
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"❌ {e}")

# ==================== FORENSICS TIMELINE PAGE ====================
elif page == "📈 Forensics Timeline":
    st.title("📈 Forensics & Activity Timeline")
    st.markdown("Detailed audit trail of all security events with photos and analytics")
    
    # Load alerts from JSONL file
    alerts_file = Path("logs/security/alerts.jsonl")
    
    if not alerts_file.exists():
        st.warning("⚠️ No alerts file found. Security checks haven't been performed yet.")
        st.info("💡 Go to **🔍 Security Check** page to run your first check!")
        st.stop()
    
    # Read all alerts
    try:
        with open(alerts_file, 'r') as f:
            all_alerts = [json.loads(line) for line in f.readlines()]
        
        if not all_alerts:
            st.info("No security events recorded yet. Run a security check to see events here.")
            st.stop()
        
        st.success(f"📊 Loaded {len(all_alerts)} security events")
        
        # === FILTERS ===
        st.subheader("🔍 Filters")
        
        filter_col1, filter_col2, filter_col3 = st.columns(3)
        
        with filter_col1:
            # Event type filter
            event_types = list(set(alert.get('alert_type', 'unknown') for alert in all_alerts))
            event_types.insert(0, "All Types")
            selected_type = st.selectbox("Event Type:", event_types)
        
        with filter_col2:
            # Date range filter
            show_last = st.selectbox(
                "Show Last:",
                ["All Events", "Last 10", "Last 25", "Last 50", "Last 100"],
                index=2  # Default to Last 25
            )
        
        with filter_col3:
            # Sort order
            sort_order = st.selectbox(
                "Sort By:",
                ["Newest First", "Oldest First"],
                index=0
            )
        
        # Apply filters
        filtered_alerts = all_alerts.copy()
        
        # Filter by type
        if selected_type != "All Types":
            filtered_alerts = [a for a in filtered_alerts if a.get('alert_type') == selected_type]
        
        # Apply show last limit
        if show_last != "All Events":
            limit = int(show_last.split()[-1])
            filtered_alerts = filtered_alerts[-limit:]
        
        # Apply sort
        if sort_order == "Newest First":
            filtered_alerts = list(reversed(filtered_alerts))
        
        st.info(f"📋 Showing {len(filtered_alerts)} events")
        
        # === STATISTICS ===
        st.markdown("---")
        st.subheader("📊 Event Statistics")
        
        stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
        
        total_events = len(all_alerts)
        unauthorized_count = len([a for a in all_alerts if a.get('alert_type') == 'unauthorized_access'])
        authorized_count = len([a for a in all_alerts if a.get('alert_type') == 'authorized'])
        no_face_count = len([a for a in all_alerts if a.get('alert_type') == 'no_face'])
        
        with stat_col1:
            st.metric("Total Events", total_events)
        with stat_col2:
            st.metric("🚨 Unauthorized", unauthorized_count)
        with stat_col3:
            st.metric("✅ Authorized", authorized_count)
        with stat_col4:
            st.metric("👻 No Face", no_face_count)
        
        # === EXPORT ===
        st.markdown("---")
        export_col1, export_col2 = st.columns([3, 1])
        
        with export_col2:
            if st.button("📥 Export to CSV"):
                import csv
                import io
                
                # Create CSV
                output = io.StringIO()
                fieldnames = ['timestamp', 'alert_type', 'message', 'detected_faces_count', 'snapshot_path']
                writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
                
                writer.writeheader()
                for alert in all_alerts:
                    writer.writerow(alert)
                
                # Download button
                st.download_button(
                    label="⬇️ Download CSV",
                    data=output.getvalue(),
                    file_name=f"senthium_alerts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        
        # === TIMELINE ===
        st.markdown("---")
        st.subheader("📅 Event Timeline")
        
        # Display events
        for idx, alert in enumerate(filtered_alerts):
            alert_type = alert.get('alert_type', 'unknown')
            timestamp = alert.get('timestamp', 'Unknown')
            message = alert.get('message', 'No message')
            faces_count = alert.get('detected_faces_count', 0)
            snapshot_path = alert.get('snapshot_path', '')
            
            # Format timestamp
            try:
                if 'T' in timestamp:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    formatted_time = timestamp
            except:
                formatted_time = timestamp
            
            # Determine styling
            is_threat = alert_type == 'unauthorized_access'
            
            if is_threat:
                icon = "🚨"
                color = "#dc3545"
                bg_color = "#f8d7da"
            elif alert_type == 'authorized':
                icon = "✅"
                color = "#28a745"
                bg_color = "#d4edda"
            elif alert_type == 'no_face':
                icon = "👻"
                color = "#6c757d"
                bg_color = "#e2e3e5"
            else:
                icon = "ℹ️"
                color = "#17a2b8"
                bg_color = "#d1ecf1"
            
            # Create expandable event card
            with st.expander(f"{icon} **{formatted_time}** - {alert_type.upper()}", expanded=(idx < 3)):
                event_col1, event_col2 = st.columns([2, 1])
                
                with event_col1:
                    st.markdown(f"""
                    <div style="
                        background: {bg_color};
                        border-left: 5px solid {color};
                        padding: 1rem;
                        border-radius: 0.5rem;
                        margin-bottom: 1rem;
                    ">
                        <strong style="color: {color}; font-size: 1.1rem;">{icon} {alert_type.replace('_', ' ').title()}</strong><br>
                        <p style="margin: 0.5rem 0; color: #333;">{message}</p>
                        <small style="color: #666;">
                            <strong>Timestamp:</strong> {formatted_time}<br>
                            <strong>Faces Detected:</strong> {faces_count}<br>
                            <strong>Snapshot:</strong> {Path(snapshot_path).name if snapshot_path else 'N/A'}
                        </small>
                    </div>
                    """, unsafe_allow_html=True)
                
                with event_col2:
                    # Show snapshot if available
                    if snapshot_path and Path(snapshot_path).exists():
                        st.image(str(snapshot_path), caption="Event Snapshot")
                        
                        # Check for annotated version
                        snapshot_file = Path(snapshot_path)
                        annotated_path = snapshot_file.parent / f"{snapshot_file.stem}_annotated{snapshot_file.suffix}"
                        
                        if annotated_path.exists():
                            st.image(str(annotated_path), caption="Annotated Snapshot")
                    else:
                        st.info("No snapshot available")
                
                # Additional details in columns
                detail_col1, detail_col2 = st.columns(2)
                
                with detail_col1:
                    st.markdown("**Event Details:**")
                    for key, value in alert.items():
                        if key not in ['message', 'timestamp', 'alert_type', 'snapshot_path', 'detected_faces_count']:
                            st.text(f"{key}: {value}")
                
                with detail_col2:
                    if snapshot_path and Path(snapshot_path).exists():
                        # Download button for snapshot
                        with open(snapshot_path, 'rb') as img_file:
                            st.download_button(
                                label="📥 Download Snapshot",
                                data=img_file,
                                file_name=Path(snapshot_path).name,
                                mime="image/jpeg",
                                use_container_width=True
                            )
        
        # === CHART (Event Type Distribution) ===
        st.markdown("---")
        st.subheader("📊 Event Type Distribution")
        
        # Count events by type
        type_counts = {}
        for alert in all_alerts:
            atype = alert.get('alert_type', 'unknown')
            type_counts[atype] = type_counts.get(atype, 0) + 1
        
        # Create bar chart data
        import pandas as pd
        chart_data = pd.DataFrame({
            'Event Type': list(type_counts.keys()),
            'Count': list(type_counts.values())
        })
        
        st.bar_chart(chart_data.set_index('Event Type'))
        
    except Exception as e:
        st.error(f"❌ Error loading forensics data: {e}")
        import traceback
        st.code(traceback.format_exc(), language="python")

# ==================== INTRUDER PATTERNS PAGE ====================
elif page == "🔍 Intruder Patterns":
    st.title("🔍 Intruder Patterns - Repeat Offenders")
    st.markdown("Track and identify repeat unauthorized access attempts 🚨")
    
    # Load config
    try:
        config = st.session_state.config_manager._config
        if not config:
            config = st.session_state.config_manager.load()
    except Exception as e:
        st.error(f"❌ Failed to load config: {e}")
        st.stop()
    
    # Check if pattern detection is enabled
    pattern_config = config.get('senthium', {}).get('security', {}).get('intruder_patterns', {})
    
    if not pattern_config.get('enabled', False):
        st.warning("⚠️ Intruder pattern detection is currently disabled!")
        st.markdown("Enable it in Settings to start tracking repeat offenders.")
        
        if st.button("🔓 Enable Pattern Detection"):
            try:
                config['senthium']['security']['intruder_patterns']['enabled'] = True
                st.session_state.config_manager.save(config)
                st.success("✅ Pattern detection enabled! Restart the daemon to apply changes.")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Failed to enable: {e}")
    
    else:
        # Load patterns from file
        patterns_file = Path("logs/security/intruder_patterns.json")
        
        if not patterns_file.exists():
            st.info("📭 No intruder patterns detected yet!")
            st.markdown("Patterns will appear here once the same unauthorized face is detected multiple times.")
        
        else:
            try:
                with open(patterns_file, 'r') as f:
                    patterns_data = json.load(f)
                
                if not patterns_data:
                    st.info("📭 No intruder patterns detected yet!")
                else:
                    # === STATS ===
                    st.subheader("📊 Pattern Statistics")
                    
                    total_patterns = len(patterns_data)
                    total_detections = sum(p['count'] for p in patterns_data.values())
                    
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Total Patterns", total_patterns, help="Unique repeat offenders")
                    col2.metric("Total Detections", total_detections, help="All unauthorized attempts")
                    col3.metric("Alert Threshold", pattern_config.get('alert_threshold', 3), help="Detections before alert")
                    
                    st.divider()
                    
                    # === FILTERS ===
                    st.subheader("🔍 Filters")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        threat_filter = st.selectbox(
                            "Threat Level",
                            ["All", "CRITICAL", "HIGH", "MEDIUM", "LOW"],
                            help="Filter by threat level"
                        )
                    
                    with col2:
                        sort_by = st.selectbox(
                            "Sort By",
                            ["Most Recent", "Most Frequent", "Oldest"],
                            help="Sort patterns"
                        )
                    
                    # Convert to list
                    patterns_list = []
                    for pattern_id, pattern_data in patterns_data.items():
                        pattern_data['pattern_id'] = pattern_id
                        patterns_list.append(pattern_data)
                    
                    # Filter by threat level
                    if threat_filter != "All":
                        patterns_list = [p for p in patterns_list if p.get('threat_level') == threat_filter]
                    
                    # Sort
                    if sort_by == "Most Recent":
                        patterns_list.sort(key=lambda p: p.get('last_seen', ''), reverse=True)
                    elif sort_by == "Most Frequent":
                        patterns_list.sort(key=lambda p: p.get('count', 0), reverse=True)
                    else:  # Oldest
                        patterns_list.sort(key=lambda p: p.get('first_seen', ''))
                    
                    st.divider()
                    
                    # === PATTERN LIST ===
                    st.subheader("🚨 Detected Patterns")
                    st.markdown(f"Showing {len(patterns_list)} pattern(s)")
                    
                    if not patterns_list:
                        st.info("No patterns match your filters.")
                    
                    else:
                        for pattern in patterns_list:
                            threat_level = pattern.get('threat_level', 'LOW')
                            
                            # Threat level colors
                            color_map = {
                                'CRITICAL': '#dc3545',
                                'HIGH': '#fd7e14',
                                'MEDIUM': '#ffc107',
                                'LOW': '#6c757d'
                            }
                            border_color = color_map.get(threat_level, '#6c757d')
                            
                            # Pattern card
                            with st.container():
                                st.markdown(f"""
                                <div style="border-left: 4px solid {border_color}; padding-left: 1rem; margin-bottom: 1rem;">
                                    <h4>{pattern.get('pattern_id', 'Unknown')}</h4>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                col1, col2, col3, col4 = st.columns(4)
                                col1.metric("🔢 Count", pattern.get('count', 0))
                                col2.metric("⚠️ Threat", threat_level)
                                col3.metric("📅 First Seen", pattern.get('first_seen', 'N/A')[:10])
                                col4.metric("🕒 Last Seen", pattern.get('last_seen', 'N/A')[:10])
                                
                                # Expandable details
                                with st.expander("📋 View Details"):
                                    st.json(pattern, expanded=False)
                                    
                                    # Photo gallery
                                    snapshot_paths = pattern.get('snapshot_paths', [])
                                    
                                    if snapshot_paths:
                                        st.markdown("**📸 Associated Snapshots:**")
                                        
                                        # Display up to 5 snapshots
                                        cols = st.columns(min(len(snapshot_paths), 5))
                                        for idx, snapshot_path in enumerate(snapshot_paths[:5]):
                                            snapshot_file = Path(snapshot_path)
                                            
                                            if snapshot_file.exists():
                                                try:
                                                    img = Image.open(snapshot_file)
                                                    cols[idx % 5].image(img)
                                                except Exception as e:
                                                    cols[idx % 5].error(f"Error loading image: {e}")
                                            else:
                                                cols[idx % 5].warning("Snapshot not found")
                                        
                                        if len(snapshot_paths) > 5:
                                            st.info(f"+ {len(snapshot_paths) - 5} more snapshots")
                                
                                st.divider()
            
            except Exception as e:
                st.error(f"❌ Error loading patterns: {e}")
                import traceback
                st.code(traceback.format_exc(), language="python")

# ==================== HAUNTING MODE PAGE ====================
elif page == "👻 Haunting Mode":
    st.title("👻 Haunting Mode - Spooky Intruder Deterrence")
    st.markdown("*Escalate from warnings to full paranormal psychological warfare* 💀")
    
    # Load config
    config = st.session_state.config_manager._config
    haunting_config = config.get('senthium', {}).get('haunting_mode', {})
    
    # Main Enable/Disable Toggle
    st.subheader("🔮 Haunting Mode Control")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown("""
        **What is Haunting Mode?**
        
        When an intruder is detected, Senthium can escalate from silent monitoring to active deterrence:
        
        - 🔇 **Level 0**: Silent monitoring only (default)
        - 🔔 **Level 1**: System notifications + email alerts
        - 🗣️ **Level 2**: Text-to-Speech whispers ("I can see you...")
        - 👁️ **Level 3**: Screen glitches + cryptic messages
        - 💀 **Level 4**: Full haunting (lock screen, sirens, all effects)
        
        *Use responsibly. May cause psychological distress to intruders.* 😈
        """)
    
    with col2:
        # Status indicator
        haunting_enabled = haunting_config.get('enabled', False)
        if haunting_enabled:
            st.success("### 🟢 ACTIVE")
            st.caption("Haunting armed")
        else:
            st.warning("### 🔴 DISABLED")
            st.caption("No spooky stuff")
    
    st.markdown("---")
    
    # Enable/Disable Toggle
    enable_haunting = st.toggle(
        "🔮 Enable Haunting Mode",
        value=haunting_enabled,
        help="Turn on paranormal deterrence features"
    )
    
    if enable_haunting != haunting_enabled:
        if 'senthium' not in config:
            config['senthium'] = {}
        if 'haunting_mode' not in config['senthium']:
            config['senthium']['haunting_mode'] = {}
        
        config['senthium']['haunting_mode']['enabled'] = enable_haunting
        st.session_state.config_manager._config = config
        st.session_state.config_manager.save_config()
        st.success(f"✅ Haunting Mode {'enabled' if enable_haunting else 'disabled'}!")
        st.rerun()
    
    # Configuration (only show if enabled)
    if enable_haunting:
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Escalation Settings
        st.subheader("⚡ Escalation Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            escalation_delay = st.slider(
                "🕐 Escalation Delay (seconds)",
                min_value=5,
                max_value=120,
                value=haunting_config.get('escalation_delay_seconds', 30),
                step=5,
                help="How long to wait before escalating to next level"
            )
            
            max_level = st.select_slider(
                "🔥 Maximum Escalation Level",
                options=[0, 1, 2, 3, 4],
                value=haunting_config.get('max_escalation_level', 2),
                help="Highest level of haunting to reach"
            )
        
        with col2:
            repeat_whispers = st.checkbox(
                "🔁 Repeat TTS Whispers",
                value=haunting_config.get('repeat_whispers', True),
                help="Keep whispering at intruder periodically"
            )
            
            whisper_interval = st.slider(
                "⏱️ Whisper Interval (seconds)",
                min_value=10,
                max_value=300,
                value=haunting_config.get('whisper_interval_seconds', 60),
                step=10,
                help="Time between repeated whispers",
                disabled=not repeat_whispers
            )
        
        st.markdown("---")
        
        # TTS Configuration
        st.subheader("🗣️ Text-to-Speech Settings")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Try to get available voices
            try:
                import pyttsx3
                engine = pyttsx3.init()
                voices = engine.getProperty('voices')
                voice_names = [f"{i}: {v.name}" for i, v in enumerate(voices)]
                
                selected_voice_idx = st.selectbox(
                    "🎙️ TTS Voice",
                    options=range(len(voices)),
                    format_func=lambda i: voice_names[i],
                    index=haunting_config.get('tts_voice_index', 0),
                    help="Choose a creepy voice"
                )
                
                # Test voice button
                if st.button("🔊 Test Voice", help="Hear the selected voice"):
                    with st.spinner("Speaking..."):
                        try:
                            engine.setProperty('voice', voices[selected_voice_idx].id)
                            engine.setProperty('rate', haunting_config.get('tts_rate', 150))
                            engine.say("I am watching you... I can see everything you do...")
                            engine.runAndWait()
                            st.success("✅ Voice test complete!")
                        except Exception as e:
                            st.error(f"❌ TTS Error: {e}")
                
            except Exception as e:
                st.warning(f"⚠️ TTS not available: {e}")
                st.info("Install pyttsx3: `pip install pyttsx3`")
                selected_voice_idx = 0
        
        with col2:
            tts_rate = st.slider(
                "⚡ Speech Rate",
                min_value=50,
                max_value=300,
                value=haunting_config.get('tts_rate', 150),
                step=10,
                help="Words per minute (lower = creepier)"
            )
            
            tts_volume = st.slider(
                "🔊 Volume",
                min_value=0.0,
                max_value=1.0,
                value=haunting_config.get('tts_volume', 0.8),
                step=0.1,
                help="TTS volume level"
            )
        
        st.markdown("---")
        
        # Whisper Messages
        st.subheader("💬 Whisper Messages")
        st.markdown("*Messages that will be randomly selected and spoken to intruders*")
        
        default_whispers = [
            "I can see you...",
            "You shouldn't be here...",
            "I'm watching your every move...",
            "This system is protected...",
            "Your face has been recorded...",
            "Security has been notified...",
            "Why are you touching my things?",
            "I know who you are...",
            "Leave now while you still can...",
            "The authorities are on their way..."
        ]
        
        current_whispers = haunting_config.get('whisper_messages', default_whispers)
        whisper_text = st.text_area(
            "Whisper Lines (one per line)",
            value="\n".join(current_whispers),
            height=200,
            help="Each line is a separate message that can be spoken"
        )
        
        st.markdown("---")
        
        # Screen Effects
        st.subheader("👁️ Screen Effects (Level 3+)")
        
        effect_cols = st.columns(3)
        
        with effect_cols[0]:
            glitch_screen = st.checkbox(
                "⚡ Screen Glitches",
                value=haunting_config.get('glitch_screen', True),
                help="Distort screen with glitch effects"
            )
            
            show_eyes = st.checkbox(
                "👁️ Watching Eyes",
                value=haunting_config.get('show_eyes', True),
                help="Display creepy eye images"
            )
        
        with effect_cols[1]:
            cryptic_messages = st.checkbox(
                "💀 Cryptic Messages",
                value=haunting_config.get('cryptic_messages', True),
                help="Show mysterious text overlays"
            )
            
            invert_colors = st.checkbox(
                "🌈 Invert Colors",
                value=haunting_config.get('invert_colors', False),
                help="Invert screen colors periodically"
            )
        
        with effect_cols[2]:
            shake_windows = st.checkbox(
                "📳 Shake Windows",
                value=haunting_config.get('shake_windows', False),
                help="Make windows vibrate (Windows only)"
            )
            
            play_sounds = st.checkbox(
                "🔊 Spooky Sounds",
                value=haunting_config.get('play_sounds', False),
                help="Play eerie sound effects"
            )
        
        st.markdown("---")
        
        # Level 4 Nuclear Options
        st.subheader("💀 Level 4 - Maximum Deterrence")
        st.warning("⚠️ **WARNING**: These are extreme measures. Use only if you want to traumatize intruders.")
        
        nuke_cols = st.columns(2)
        
        with nuke_cols[0]:
            auto_lock = st.checkbox(
                "🔒 Auto-Lock Workstation",
                value=haunting_config.get('auto_lock', False),
                help="Lock Windows immediately"
            )
            
            trigger_siren = st.checkbox(
                "🚨 Trigger Alarm Siren",
                value=haunting_config.get('trigger_siren', False),
                help="Play loud alarm sound"
            )
        
        with nuke_cols[1]:
            full_screen_takeover = st.checkbox(
                "🖥️ Full-Screen Takeover",
                value=haunting_config.get('full_screen_takeover', False),
                help="Take over entire screen with warning"
            )
            
            emergency_shutdown = st.checkbox(
                "⚡ Emergency Shutdown",
                value=haunting_config.get('emergency_shutdown', False),
                help="Shutdown computer (EXTREME)"
            )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Save All Settings Button
        if st.button("💾 Save Haunting Configuration", type="primary", use_container_width=True):
            with st.spinner("Saving haunting settings..."):
                # Update config
                if 'senthium' not in config:
                    config['senthium'] = {}
                if 'haunting_mode' not in config['senthium']:
                    config['senthium']['haunting_mode'] = {}
                
                config['senthium']['haunting_mode'].update({
                    'enabled': enable_haunting,
                    'escalation_delay_seconds': escalation_delay,
                    'max_escalation_level': max_level,
                    'repeat_whispers': repeat_whispers,
                    'whisper_interval_seconds': whisper_interval,
                    'tts_voice_index': selected_voice_idx,
                    'tts_rate': tts_rate,
                    'tts_volume': tts_volume,
                    'whisper_messages': [line.strip() for line in whisper_text.split('\n') if line.strip()],
                    'glitch_screen': glitch_screen,
                    'show_eyes': show_eyes,
                    'cryptic_messages': cryptic_messages,
                    'invert_colors': invert_colors,
                    'shake_windows': shake_windows,
                    'play_sounds': play_sounds,
                    'auto_lock': auto_lock,
                    'trigger_siren': trigger_siren,
                    'full_screen_takeover': full_screen_takeover,
                    'emergency_shutdown': emergency_shutdown
                })
                
                st.session_state.config_manager._config = config
                st.session_state.config_manager.save_config()
                
                st.success("✅ Haunting configuration saved successfully! 👻")
                time.sleep(1)
                st.rerun()
    
    else:
        st.info("💡 Enable Haunting Mode to configure spooky deterrence features")

# ==================== SETTINGS PAGE ====================
elif page == "⚙️ Settings":
    st.title("⚙️ Settings & Configuration")
    st.markdown("Configure your security system, alerts, and monitoring")
    
    # ===== SECURITY SYSTEM CONTROL =====
    st.subheader("🔐 Security System Control")
    st.markdown("""
    **What does this do?**
    - 🟢 **Enable**: Security checks will detect unauthorized faces and send alerts
    - � **Disable**: No security checks or alerts (system paused)
    """)
    
    try:
        stats = st.session_state.security_manager.get_stats()
        
        # Safety check for None
        if not stats or not isinstance(stats, dict):
            stats = {'enabled': False}
        
        is_enabled = stats.get('enabled', False)
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            if is_enabled:
                st.success("🟢 **Security System: ACTIVE**")
                st.info("ℹ️ System is monitoring for unauthorized faces")
            else:
                st.warning("🔴 **Security System: DISABLED**")
                st.info("ℹ️ No monitoring or alerts")
        
        with col2:
            if is_enabled:
                if st.button("🔴 Disable Security", key="disable_btn", help="Stop all security monitoring and alerts"):
                    st.session_state.security_manager.disable()
                    # Stop camera if running
                    if st.session_state.security_manager.camera._is_initialized:
                        st.session_state.security_manager.camera.release()
                    st.success("✅ Security disabled, camera stopped")
                    st.rerun()
            else:
                if st.button("🟢 Enable Security", key="enable_btn", help="Start security monitoring and alerts"):
                    st.session_state.security_manager.enable()
                    st.success("✅ Security enabled")
                    st.rerun()
    
    except Exception as e:
        st.error(f"Error: {e}")
    
    st.markdown("---")
    
    # ===== INTRUDER ACTION SETTINGS =====
    st.subheader("🔐 Intruder Action Settings")
    st.markdown("""
    **What happens when an unauthorized face is detected?**
    
    Configure automatic actions to protect your PC from intruders!
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        auto_lock = st.checkbox(
            "🔒 Auto-Lock Screen",
            value=st.session_state.config_manager.get('senthium.security.auto_lock_on_intruder', True),
            help="Immediately lock the screen when an unauthorized face is detected"
        )
        
        play_alarm = st.checkbox(
            "🔔 Play Alarm Sound",
            value=st.session_state.config_manager.get('senthium.security.play_alarm_on_intruder', True),
            help="Play a loud alarm sound to alert you"
        )
    
    with col2:
        auto_sleep = st.checkbox(
            "😴 Auto-Sleep Computer",
            value=st.session_state.config_manager.get('senthium.security.auto_sleep_on_intruder', False),
            help="⚠️ NUCLEAR OPTION: Put computer to sleep immediately (requires wake-up)"
        )
        
        if auto_sleep:
            st.warning("⚠️ **Warning:** This will put your computer to sleep immediately! You'll need to physically wake it up.")
    
    if st.button("💾 Save Action Settings", key="save_actions"):
        # Load current config
        config = st.session_state.config_manager._config
        if config is None:
            config = st.session_state.config_manager.load()
        
        # Update action settings
        config['senthium']['security']['auto_lock_on_intruder'] = auto_lock
        config['senthium']['security']['play_alarm_on_intruder'] = play_alarm
        config['senthium']['security']['auto_sleep_on_intruder'] = auto_sleep
        
        if st.session_state.config_manager.save(config):
            st.success("✅ Action settings saved!")
            st.info("💡 Restart daemon to apply changes")
            
            # Update security manager settings if already initialized
            if st.session_state.security_manager:
                st.session_state.security_manager.auto_lock_on_intruder = auto_lock
                st.session_state.security_manager.play_alarm_on_intruder = play_alarm
                st.session_state.security_manager.auto_sleep_on_intruder = auto_sleep
            
            st.rerun()
        else:
            st.error("❌ Failed to save configuration")
    
    st.markdown("---")
    
    # ===== ALERT CONFIGURATION =====
    st.subheader("📢 Alert Configuration")
    
    # Show current alert status summary
    from src.utils.alert_config_summary import AlertConfigSummary
    summary_gen = AlertConfigSummary()
    summary = summary_gen.generate_summary(st.session_state.config_manager._config or st.session_state.config_manager.load())
    
    # Display active channels in a nice card
    col_sum1, col_sum2, col_sum3 = st.columns(3)
    
    with col_sum1:
        active_count = summary['summary']['total_active_channels']
        st.metric("Active Alert Channels", active_count, delta="Configured" if active_count > 0 else "None")
    
    with col_sum2:
        discord_status = "🟢 Active" if summary['alert_channels']['discord']['enabled'] else "⚪ Inactive"
        st.metric("Discord", discord_status)
    
    with col_sum3:
        email_status = "🟢 Active" if summary['alert_channels']['email']['enabled'] else "⚪ Inactive"
        st.metric("Email", email_status)
    
    st.markdown("""
    **Configure where you want to receive security alerts:**
    
    Choose which channels to use when unauthorized access is detected.
    """)
    
    # Discord Webhook
    with st.expander("💜 Discord Webhook", expanded=False):
        st.markdown("""
        **What is this?**  
        Get instant alerts in your Discord server when unauthorized faces are detected.
        
        **How to set up:**
        1. Go to your Discord server settings
        2. Navigate to Integrations → Webhooks
        3. Create a new webhook
        4. Copy the webhook URL and paste below
        """)
        
        # Load current values
        current_discord = st.session_state.config_manager.get('senthium.security.alerts.discord', {})
        
        discord_webhook = st.text_input(
            "Discord Webhook URL",
            value=current_discord.get('webhook_url', ''),
            placeholder="https://discord.com/api/webhooks/...",
            help="Paste your Discord webhook URL here",
            type="password"
        )
        discord_enabled = st.checkbox(
            "Enable Discord Alerts",
            value=current_discord.get('enabled', False)
        )
        
        col_save, col_test = st.columns(2)
        
        with col_save:
            if st.button("💾 Save Discord Config", key="save_discord"):
                print(f"🔍 DEBUG: Saving Discord - Enabled={discord_enabled}, URL={'SET' if discord_webhook else 'EMPTY'}")
                
                if st.session_state.config_manager.update_discord(discord_webhook or "", discord_enabled):
                    print(f"✅ DEBUG: Discord config saved successfully!")
                    st.success("✅ Discord configuration saved!")
                    st.info("💡 Restart daemon to apply changes")
                    
                    # Update notifier config
                    st.session_state.security_manager.notifier.config['discord_webhook_url'] = discord_webhook or ""
                    st.session_state.security_manager.notifier.config['discord_enabled'] = discord_enabled
                    print(f"🔄 DEBUG: Updated SecurityManager notifier config")
                    
                    st.rerun()
                else:
                    print(f"❌ DEBUG: Failed to save Discord config")
                    st.error("❌ Failed to save configuration")
        
        with col_test:
            if st.button("🧪 Test Discord Alert", key="test_discord", disabled=not discord_webhook):
                print(f"🧪 DEBUG: Testing Discord webhook...")
                try:
                    test_payload = {
                        "embeds": [{
                            "title": "🧪 Test Alert - Senthium AI",
                            "description": "This is a test alert from your security system!",
                            "color": 3066993,  # Green
                            "timestamp": datetime.now().isoformat(),
                            "footer": {"text": "Senthium AI Security System"}
                        }]
                    }
                    response = requests.post(discord_webhook or "", json=test_payload, timeout=10)
                    if response.status_code in [200, 204]:
                        print(f"✅ DEBUG: Discord test alert sent successfully!")
                        st.success("✅ Test alert sent to Discord!")
                    else:
                        print(f"❌ DEBUG: Discord test failed - Status {response.status_code}")
                        st.error(f"❌ Failed: HTTP {response.status_code}")
                except Exception as e:
                    print(f"❌ DEBUG: Discord test exception: {e}")
                    st.error(f"❌ Error: {e}")
    
    # Email Alerts
    with st.expander("✉️ Email (SMTP)", expanded=False):
        st.markdown("""
        **What is this?**  
        Receive email alerts when security threats are detected.
        
        **Supported providers:**
        - Gmail (smtp.gmail.com)
        - Outlook (smtp-mail.outlook.com)
        - Yahoo (smtp.mail.yahoo.com)
        - Custom SMTP server
        """)
        
        # Load current values
        current_email = st.session_state.config_manager.get('senthium.security.alerts.email', {})
        
        col1, col2 = st.columns(2)
        
        with col1:
            smtp_server = st.text_input("SMTP Server", value=current_email.get('smtp_server', ''), placeholder="smtp.gmail.com")
            smtp_port = st.number_input("SMTP Port", value=current_email.get('smtp_port', 587), min_value=1, max_value=65535)
            smtp_username = st.text_input("Username/Email", value=current_email.get('username', ''), placeholder="your.email@gmail.com")
        
        with col2:
            smtp_password = st.text_input("Password", value=current_email.get('password', ''), type="password", help="Use app-specific password for Gmail")
            recipient_email = st.text_input("Alert Recipient", value=current_email.get('recipient', ''), placeholder="alerts@example.com")
            email_enabled = st.checkbox("Enable Email Alerts", value=current_email.get('enabled', False))
        
        col_save, col_test = st.columns(2)
        
        with col_save:
            if st.button("💾 Save Email Config", key="save_email"):
                print(f"🔍 DEBUG: Saving Email - Enabled={email_enabled}, Server={smtp_server}, Port={smtp_port}")
                print(f"🔍 DEBUG: Email - Username={smtp_username}, Recipient={recipient_email}")
                
                if st.session_state.config_manager.update_email(
                    smtp_server or "", smtp_port, smtp_username or "", smtp_password or "", recipient_email or "", email_enabled
                ):
                    print(f"✅ DEBUG: Email config saved successfully!")
                    st.success("✅ Email configuration saved!")
                    st.info("💡 Restart daemon to apply changes")
                    
                    # Update notifier config
                    st.session_state.security_manager.notifier.config['email_smtp_host'] = smtp_server or ""
                    st.session_state.security_manager.notifier.config['email_smtp_port'] = smtp_port
                    st.session_state.security_manager.notifier.config['email_from'] = smtp_username or ""
                    st.session_state.security_manager.notifier.config['email_to'] = recipient_email or ""
                    st.session_state.security_manager.notifier.config['email_password'] = smtp_password
                    st.session_state.security_manager.notifier.config['email_enabled'] = email_enabled
                    print(f"🔄 DEBUG: Updated SecurityManager notifier email config")
                    
                    st.rerun()
                else:
                    print(f"❌ DEBUG: Failed to save Email config")
                    st.error("❌ Failed to save configuration")
        
        with col_test:
            test_disabled = not (smtp_server and smtp_username and smtp_password and recipient_email)
            if st.button("🧪 Test Email Alert", key="test_email", disabled=test_disabled):
                print(f"🧪 DEBUG: Testing Email SMTP connection...")
                try:
                    import smtplib
                    from email.mime.text import MIMEText
                    from email.mime.multipart import MIMEMultipart
                    
                    msg = MIMEMultipart()
                    msg['From'] = smtp_username or ""
                    msg['To'] = recipient_email or ""
                    msg['Subject'] = "🧪 Test Alert - Senthium AI"
                    
                    body = """
                    This is a test alert from your Senthium AI Security System!
                    
                    If you received this email, your SMTP configuration is working correctly.
                    
                    ---
                    Senthium AI Security System
                    """
                    msg.attach(MIMEText(body, 'plain'))
                    
                    print(f"🔗 DEBUG: Connecting to {smtp_server}:{smtp_port}...")
                    server = smtplib.SMTP(smtp_server or "", smtp_port)
                    server.starttls()
                    print(f"🔐 DEBUG: Logging in as {smtp_username}...")
                    server.login(smtp_username or "", smtp_password or "")
                    print(f"📧 DEBUG: Sending test email to {recipient_email}...")
                    server.send_message(msg)
                    server.quit()
                    
                    print(f"✅ DEBUG: Email test sent successfully!")
                    st.success(f"✅ Test email sent to {recipient_email}!")
                except Exception as e:
                    print(f"❌ DEBUG: Email test exception: {e}")
                    st.error(f"❌ Error: {e}")
    
    # Telegram Bot
    with st.expander("💬 Telegram Bot", expanded=False):
        st.markdown("""
        **What is this?**  
        Get instant Telegram messages when threats are detected.
        
        **How to set up:**
        1. Message @BotFather on Telegram
        2. Create a new bot with /newbot
        3. Copy the bot token
        4. Start a chat with your bot
        5. Get your chat ID from https://api.telegram.org/bot<TOKEN>/getUpdates
        """)
        
        # Load current values
        current_telegram = st.session_state.config_manager.get('senthium.security.alerts.telegram', {})
        
        telegram_token = st.text_input("Bot Token", value=current_telegram.get('bot_token', ''), type="password", placeholder="123456:ABC-DEF...")
        telegram_chat_id = st.text_input("Chat ID", value=current_telegram.get('chat_id', ''), placeholder="Your chat ID")
        telegram_enabled = st.checkbox("Enable Telegram Alerts", value=current_telegram.get('enabled', False))
        
        if st.button("💾 Save Telegram Config", key="save_telegram"):
            print(f"🔍 DEBUG: Saving Telegram - Enabled={telegram_enabled}, Token={'SET' if telegram_token else 'EMPTY'}, ChatID={telegram_chat_id}")
            
            if st.session_state.config_manager.update_telegram(telegram_token or "", telegram_chat_id or "", telegram_enabled):
                print(f"✅ DEBUG: Telegram config saved successfully!")
                st.success("✅ Telegram configuration saved!")
                st.info("💡 Restart daemon to apply changes")
                
                # Update notifier config
                st.session_state.security_manager.notifier.config['telegram_bot_token'] = telegram_token or ""
                st.session_state.security_manager.notifier.config['telegram_chat_id'] = telegram_chat_id or ""
                st.session_state.security_manager.notifier.config['telegram_enabled'] = telegram_enabled
                print(f"🔄 DEBUG: Updated SecurityManager notifier telegram config")
                
                st.rerun()
            else:
                print(f"❌ DEBUG: Failed to save Telegram config")
                st.error("❌ Failed to save configuration")
    
    # Desktop Notifications
    with st.expander("🖥️ Desktop & System Alerts", expanded=False):
        # Load current values
        current_alerts = st.session_state.config_manager.get('senthium.security.alerts', {})
        
        desktop_notif = st.checkbox("Windows Toast Notifications", value=current_alerts.get('desktop_notification', True), help="Show Windows 10/11 notifications")
        sound_alert = st.checkbox("Sound Alerts", value=current_alerts.get('sound_alert', False), help="Play alert sound on detection")
        log_to_file = st.checkbox("Log Alerts to File", value=current_alerts.get('log_to_file', True), help="Save alerts to logs/security/alerts.jsonl")
        
        if st.button("💾 Save System Config", key="save_system"):
            print(f"🔍 DEBUG: Saving System Alerts - Desktop={desktop_notif}, Sound={sound_alert}, LogFile={log_to_file}")
            
            if st.session_state.config_manager.update_desktop_alerts(desktop_notif, sound_alert, log_to_file):
                print(f"✅ DEBUG: System alerts config saved successfully!")
                st.success("✅ System configuration saved!")
                st.info("💡 Restart daemon to apply changes")
                
                # Update notifier config
                st.session_state.security_manager.notifier.config['desktop_notification'] = desktop_notif
                st.session_state.security_manager.notifier.config['sound_alert'] = sound_alert
                st.session_state.security_manager.notifier.config['log_to_file'] = log_to_file
                print(f"🔄 DEBUG: Updated SecurityManager notifier system config")
                
                st.rerun()
            else:
                print(f"❌ DEBUG: Failed to save system alerts config")
                st.error("❌ Failed to save configuration")
    
    # View full configuration summary
    st.divider()
    
    with st.expander("📋 View Alert Configuration Summary", expanded=False):
        summary_text = summary_gen.print_summary(st.session_state.config_manager._config or st.session_state.config_manager.load())
        st.code(summary_text, language="text")
        
        st.info(f"💾 Configuration details are also saved to: `config/alert_settings_summary.json`")
        
        # Download summary as JSON
        summary_json = json.dumps(summary, indent=2)
        st.download_button(
            label="⬇️ Download Configuration as JSON",
            data=summary_json,
            file_name=f"senthium_alert_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            key="download_summary"
        )
    
    st.markdown("---")
    
    # ===== DAEMON CONTROL =====
    st.subheader("🤖 Background Daemon (Advanced)")
    
    # Check daemon status
    pid_file = PIDFile()
    is_daemon_running = pid_file.is_running()
    daemon_pid = pid_file.get_pid() if is_daemon_running else None
    
    # Status indicator
    if is_daemon_running:
        st.success(f"✅ **Daemon Status: RUNNING** (PID: {daemon_pid})")
        st.info("💡 The daemon is actively monitoring in the background. Check the Dashboard for recent alerts.")
    else:
        st.warning("⚠️ **Daemon Status: NOT RUNNING**")
        st.info("ℹ️ Start the daemon below for 24/7 automatic monitoring")
    
    st.markdown("""
    **What is the daemon?**  
    The daemon is a background process that runs 24/7 monitoring your system.
    
    - **Start**: Launch background monitoring (runs even after closing this dashboard)
    - **Stop**: Stop background monitoring
    - **Restart**: Reload configuration and restart
    
    ⚠️ **Note:** You can use the dashboard without the daemon by using manual security checks instead.
    """)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("▶️ Start Daemon", key="start_daemon", help="Start background monitoring process"):
            with st.spinner("Starting daemon..."):
                try:
                    exit_code = start_daemon()
                    if exit_code == 0:
                        st.success("✅ Daemon started!")
                        st.info("Background monitoring is now active")
                    else:
                        st.error("❌ Failed to start daemon")
                except Exception as e:
                    st.error(f"❌ Exception: {e}")
    
    with col2:
        if st.button("⏹️ Stop Daemon", key="stop_daemon", help="Stop background monitoring process"):
            with st.spinner("Stopping daemon..."):
                try:
                    exit_code = stop_daemon()
                    if exit_code == 0:
                        st.success("✅ Daemon stopped!")
                    else:
                        st.error("❌ Failed to stop daemon")
                except Exception as e:
                    st.error(f"❌ Exception: {e}")
    
    with col3:
        if st.button("🔄 Restart Daemon", key="restart_daemon", help="Reload config and restart daemon"):
            with st.spinner("Restarting daemon..."):
                try:
                    stop_daemon()
                    time.sleep(1)
                    exit_code = start_daemon()
                    if exit_code == 0:
                        st.success("✅ Daemon restarted!")
                    else:
                        st.error("❌ Failed to restart")
                except Exception as e:
                    st.error(f"❌ Exception: {e}")
    
    st.markdown("---")
    
    # ===== MONITORING SETTINGS =====
    st.subheader("⚙️ Monitoring Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        check_interval = st.slider(
            "Check Interval (seconds)",
            min_value=5,
            max_value=60,
            value=10,
            help="How often to check for unauthorized faces (daemon mode)"
        )
        
        recognition_tolerance = st.slider(
            "Recognition Tolerance",
            min_value=0.3,
            max_value=15.0,  # Increased to allow testing with high variance
            value=10.0,  # Start high for testing
            step=0.5,
            help="Distance threshold for face matching (lower = stricter, higher = more lenient)"
        )
    
    with col2:
        camera_index = st.number_input(
            "Camera Device",
            min_value=0,
            max_value=10,
            value=0,
            help="Webcam device index (0 = default camera)"
        )
        
        alert_cooldown = st.slider(
            "Alert Cooldown (seconds)",
            min_value=60,
            max_value=600,
            value=300,
            help="Minimum time between repeated alerts"
        )
    
    if st.button("💾 Save Monitoring Settings", key="save_monitoring"):
        if st.session_state.config_manager.update_monitoring(
            check_interval, recognition_tolerance, camera_index, alert_cooldown
        ):
            st.success("✅ Monitoring settings saved!")
            st.info("💡 Restart daemon to apply changes")
            st.rerun()
        else:
            st.error("❌ Failed to save configuration")
    
    st.markdown("---")
    
    # ===== CALIBRATION WIZARD =====
    st.subheader("🎯 Calibration Wizard")
    st.markdown("""
    **Automatic Tolerance Calibration**
    
    This wizard helps you find the optimal recognition tolerance by testing with:
    - ✅ Your face (authorized)
    - ❌ Unknown faces (strangers)
    - 📊 Statistical analysis
    
    **How it works:**
    1. Capture 5-10 photos of YOUR face (authorized)
    2. Show 3-5 photos of OTHER people (strangers)
    3. System analyzes distances and recommends optimal threshold
    """)
    
    # Initialize calibration state
    if 'calibration_owner_samples' not in st.session_state:
        st.session_state['calibration_owner_samples'] = []
    if 'calibration_stranger_samples' not in st.session_state:
        st.session_state['calibration_stranger_samples'] = []
    
    # Step 1: Collect Owner Samples
    with st.expander("📸 Step 1: Capture YOUR Face (Owner)", expanded=len(st.session_state.calibration_owner_samples) < 5):
        st.markdown(f"""
        **Progress:** {len(st.session_state.calibration_owner_samples)}/5 owner samples captured
        
        Take 5-10 photos of yourself from different angles and lighting.
        """)
        
        col_a, col_b = st.columns([2, 1])
        
        with col_a:
            if st.button("📸 Capture Owner Sample", key="cal_owner_capture"):
                try:
                    if not st.session_state.security_manager.camera._is_initialized:
                        st.session_state.security_manager.camera.initialize()
                    
                    frame = st.session_state.security_manager.camera.capture_frame()
                    
                    if frame is not None:
                        # Detect and encode
                        detections = st.session_state.security_manager.detector.detect_and_encode(frame)
                        
                        if detections:
                            _, encoding = detections[0]
                            st.session_state.calibration_owner_samples.append({
                                'encoding': encoding,
                                'frame': frame
                            })
                            st.success(f"✅ Owner sample {len(st.session_state.calibration_owner_samples)} captured!")
                            st.rerun()
                        else:
                            st.error("❌ No face detected! Make sure you're visible to the camera.")
                    else:
                        st.error("❌ Failed to capture from camera")
                
                except Exception as e:
                    st.error(f"Error: {e}")
        
        with col_b:
            if st.session_state.calibration_owner_samples:
                st.metric("Samples", len(st.session_state.calibration_owner_samples))
        
        # Show captured samples
        if st.session_state.calibration_owner_samples:
            st.markdown("**Captured Samples:**")
            cols = st.columns(min(5, len(st.session_state.calibration_owner_samples)))
            import cv2
            for idx, (col, sample) in enumerate(zip(cols, st.session_state.calibration_owner_samples)):
                with col:
                    rgb = cv2.cvtColor(sample['frame'], cv2.COLOR_BGR2RGB)
                    st.image(rgb, caption=f"Owner {idx+1}")
    
    # Step 2: Collect Stranger Samples
    with st.expander("🚫 Step 2: Show STRANGER Faces (Not You)", expanded=len(st.session_state.calibration_owner_samples) >= 5 and len(st.session_state.calibration_stranger_samples) < 3):
        st.markdown(f"""
        **Progress:** {len(st.session_state.calibration_stranger_samples)}/3 stranger samples captured
        
        Show photos of OTHER people (NOT you). You can:
        - Point camera at a photo on your phone
        - Show a printed photo
        - Have a friend stand in front of camera
        """)
        
        col_c, col_d = st.columns([2, 1])
        
        with col_c:
            if st.button("📸 Capture Stranger Sample", key="cal_stranger_capture"):
                try:
                    if not st.session_state.security_manager.camera._is_initialized:
                        st.session_state.security_manager.camera.initialize()
                    
                    frame = st.session_state.security_manager.camera.capture_frame()
                    
                    if frame is not None:
                        # Detect and encode
                        detections = st.session_state.security_manager.detector.detect_and_encode(frame)
                        
                        if detections:
                            _, encoding = detections[0]
                            st.session_state.calibration_stranger_samples.append({
                                'encoding': encoding,
                                'frame': frame
                            })
                            st.success(f"✅ Stranger sample {len(st.session_state.calibration_stranger_samples)} captured!")
                            st.rerun()
                        else:
                            st.error("❌ No face detected!")
                    else:
                        st.error("❌ Failed to capture from camera")
                
                except Exception as e:
                    st.error(f"Error: {e}")
        
        with col_d:
            if st.session_state.calibration_stranger_samples:
                st.metric("Samples", len(st.session_state.calibration_stranger_samples))
        
        # Show captured samples
        if st.session_state.calibration_stranger_samples:
            st.markdown("**Captured Samples:**")
            cols = st.columns(min(5, len(st.session_state.calibration_stranger_samples)))
            import cv2
            for idx, (col, sample) in enumerate(zip(cols, st.session_state.calibration_stranger_samples)):
                with col:
                    rgb = cv2.cvtColor(sample['frame'], cv2.COLOR_BGR2RGB)
                    st.image(rgb, caption=f"Stranger {idx+1}")
    
    # Step 3: Analyze and Recommend
    if len(st.session_state.calibration_owner_samples) >= 3 and len(st.session_state.calibration_stranger_samples) >= 2:
        st.markdown("---")
        st.subheader("📊 Analysis & Recommendation")
        
        if st.button("🎯 Analyze & Get Recommendation", key="cal_analyze"):
            with st.spinner("🔍 Analyzing face distances..."):
                import numpy as np
                
                # Calculate distances within owner samples (should be low)
                owner_distances = []
                owner_encodings = [s['encoding'] for s in st.session_state.calibration_owner_samples]
                
                for i in range(len(owner_encodings)):
                    for j in range(i+1, len(owner_encodings)):
                        dist = np.linalg.norm(owner_encodings[i] - owner_encodings[j])
                        owner_distances.append(dist)
                
                # Calculate distances between owner and strangers (should be high)
                stranger_distances = []
                stranger_encodings = [s['encoding'] for s in st.session_state.calibration_stranger_samples]
                
                for owner_enc in owner_encodings:
                    for stranger_enc in stranger_encodings:
                        dist = np.linalg.norm(owner_enc - stranger_enc)
                        stranger_distances.append(dist)
                
                # Statistics
                owner_mean = np.mean(owner_distances) if owner_distances else 0
                owner_max = np.max(owner_distances) if owner_distances else 0
                stranger_mean = np.mean(stranger_distances) if stranger_distances else 0
                stranger_min = np.min(stranger_distances) if stranger_distances else 0
                
                # Recommended threshold: midpoint between max owner and min stranger
                recommended_threshold = (owner_max + stranger_min) / 2
                
                # Add safety margin (20% closer to owner max)
                safety_threshold = owner_max + (recommended_threshold - owner_max) * 0.8
                
                st.success("✅ Analysis Complete!")
                
                # Show results
                result_col1, result_col2, result_col3 = st.columns(3)
                
                with result_col1:
                    st.metric("Owner Distance Range", f"{owner_mean:.2f} avg", f"Max: {owner_max:.2f}")
                    st.info("Lower = More Similar")
                
                with result_col2:
                    st.metric("Stranger Distance Range", f"{stranger_mean:.2f} avg", f"Min: {stranger_min:.2f}")
                    st.info("Higher = More Different")
                
                with result_col3:
                    st.metric("🎯 Recommended Threshold", f"{safety_threshold:.2f}")
                    st.success("Safe & Accurate!")
                
                st.markdown("---")
                st.markdown(f"""
                **📊 Detailed Analysis:**
                
                - **Owner Samples:** {len(owner_distances)} comparisons, distances range {owner_mean:.2f} (avg) to {owner_max:.2f} (max)
                - **Stranger Samples:** {len(stranger_distances)} comparisons, distances range {stranger_min:.2f} (min) to {stranger_mean:.2f} (avg)
                - **Separation Gap:** {stranger_min - owner_max:.2f} (larger = better)
                
                **Recommended Threshold:** `{safety_threshold:.2f}`
                
                This threshold ensures:
                - ✅ Your face variations are recognized (below threshold)
                - ❌ Stranger faces are rejected (above threshold)
                - 🛡️ 20% safety margin to avoid false positives
                """)
                
                # Apply button
                if st.button("✅ Apply This Threshold", key="cal_apply"):
                    if st.session_state.config_manager.update_monitoring(
                        check_interval=st.session_state.config_manager.get('senthium.security.monitoring.check_interval_seconds', 10),
                        recognition_tolerance=safety_threshold,
                        camera_index=st.session_state.config_manager.get('senthium.security.monitoring.camera_index', 0),
                        alert_cooldown=st.session_state.config_manager.get('senthium.security.monitoring.alert_cooldown_seconds', 300)
                    ):
                        st.success(f"✅ Recognition tolerance updated to {safety_threshold:.2f}!")
                        st.balloons()
                        st.info("💡 Restart daemon to apply changes")
                        
                        # Clear calibration data
                        st.session_state.calibration_owner_samples = []
                        st.session_state.calibration_stranger_samples = []
                        
                        st.rerun()
                    else:
                        st.error("❌ Failed to save threshold")
    
    # Reset button
    if st.session_state.calibration_owner_samples or st.session_state.calibration_stranger_samples:
        if st.button("🔄 Reset Calibration", key="cal_reset"):
            st.session_state.calibration_owner_samples = []
            st.session_state.calibration_stranger_samples = []
            st.success("✅ Calibration data cleared!")
            st.rerun()
    
    st.markdown("---")
    
    # ===== SNAPSHOT ENCRYPTION =====
    st.subheader("🔒 Snapshot Encryption & Privacy")
    st.markdown("""
    **Encrypt security snapshots for privacy protection**
    
    - Snapshots contain facial images - keep them secure! 🛡️
    - Encryption uses AES-128 (Fernet) - military grade! 🔐
    - Encrypted files can only be decrypted with your key
    - Key is stored securely with restricted permissions
    """)
    
    # Load current encryption config
    encryption_config = st.session_state.config_manager.get('senthium.security.encryption', {})
    encryption_enabled = encryption_config.get('enabled', False)
    auto_encrypt = encryption_config.get('auto_encrypt_new', False)
    
    col_enc1, col_enc2 = st.columns(2)
    
    with col_enc1:
        new_encryption_enabled = st.checkbox(
            "🔒 Enable Snapshot Encryption",
            value=encryption_enabled,
            help="Encrypt all security snapshots for privacy"
        )
        
        new_auto_encrypt = st.checkbox(
            "⚡ Auto-Encrypt New Snapshots",
            value=auto_encrypt,
            help="Automatically encrypt snapshots as they're captured",
            disabled=not new_encryption_enabled
        )
    
    with col_enc2:
        # Encryption stats
        snapshot_dir = Path("logs/security/snapshots")
        if snapshot_dir.exists():
            all_files = list(snapshot_dir.glob("*.*"))
            encrypted_files = list(snapshot_dir.glob("*.encrypted"))
            plaintext_files = [f for f in all_files if not f.name.endswith('.encrypted')]
            
            st.metric("Total Snapshots", len(all_files))
            st.metric("🔒 Encrypted", len(encrypted_files))
            st.metric("📁 Plaintext", len(plaintext_files))
        else:
            st.info("No snapshots directory found")
    
    # Encryption actions
    st.markdown("**Bulk Actions:**")
    action_col1, action_col2, action_col3 = st.columns(3)
    
    with action_col1:
        if st.button("🔒 Encrypt All Snapshots"):
            with st.spinner("Encrypting all snapshots..."):
                try:
                    from src.utils.snapshot_encryption import SnapshotEncryption
                    
                    encryptor = SnapshotEncryption(key_file="config/.snapshot_key")
                    count = encryptor.encrypt_directory("logs/security/snapshots", pattern="*.jpg")
                    
                    if count > 0:
                        st.success(f"✅ Encrypted {count} snapshot(s)!")
                        st.balloons()
                        st.rerun()
                    else:
                        st.info("No unencrypted snapshots found")
                
                except Exception as e:
                    st.error(f"❌ Encryption failed: {e}")
    
    with action_col2:
        if st.button("🔓 Decrypt All Snapshots"):
            with st.spinner("Decrypting all snapshots..."):
                try:
                    from src.utils.snapshot_encryption import SnapshotEncryption
                    
                    encryptor = SnapshotEncryption(key_file="config/.snapshot_key")
                    count = encryptor.decrypt_directory("logs/security/snapshots", pattern="*.encrypted")
                    
                    if count > 0:
                        st.success(f"✅ Decrypted {count} snapshot(s)!")
                        st.rerun()
                    else:
                        st.info("No encrypted snapshots found")
                
                except Exception as e:
                    st.error(f"❌ Decryption failed: {e}")
    
    with action_col3:
        if st.button("🗑️ Delete Plaintext Backups", type="secondary"):
            with st.warning("⚠️ This will permanently delete unencrypted .jpg files!"):
                if st.button("⚠️ Confirm Delete", key="confirm_delete_plaintext"):
                    try:
                        snapshot_dir = Path("logs/security/snapshots")
                        deleted = 0
                        
                        for jpg_file in snapshot_dir.glob("*.jpg"):
                            # Check if encrypted version exists
                            encrypted_version = snapshot_dir / f"{jpg_file.name}.encrypted"
                            if encrypted_version.exists():
                                jpg_file.unlink()
                                deleted += 1
                        
                        st.success(f"🗑️ Deleted {deleted} plaintext backup(s)")
                        st.rerun()
                    
                    except Exception as e:
                        st.error(f"❌ Deletion failed: {e}")
    
    # Save encryption settings
    if st.button("💾 Save Encryption Settings", key="save_encryption"):
        # Update config (we'll need to add this method)
        try:
            # Direct config update for now
            config = st.session_state.config_manager.load()
            if 'senthium' not in config:
                config['senthium'] = {}
            if 'security' not in config['senthium']:
                config['senthium']['security'] = {}
            if 'encryption' not in config['senthium']['security']:
                config['senthium']['security']['encryption'] = {}
            
            config['senthium']['security']['encryption']['enabled'] = new_encryption_enabled
            config['senthium']['security']['encryption']['auto_encrypt_new'] = new_auto_encrypt
            
            if st.session_state.config_manager.save(config):
                st.success("✅ Encryption settings saved!")
                st.info("💡 Changes will apply to new snapshots")
                st.rerun()
            else:
                st.error("❌ Failed to save encryption settings")
        
        except Exception as e:
            st.error(f"❌ Error: {e}")
            import traceback
            st.code(traceback.format_exc(), language="python")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 2rem;'>
    <p><strong>Senthium AI Security System</strong> v0.6.0</p>
    <p>🔒 Intelligent Wake-Lock + AI Face Recognition</p>
    <p>Made with 💖 using Streamlit</p>
</div>
""", unsafe_allow_html=True)
