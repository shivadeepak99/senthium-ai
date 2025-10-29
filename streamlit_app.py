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

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.vision.security_manager import SecurityManager
from src.rules.schema import ConfigSchema
from src.daemon.control import start_daemon, stop_daemon

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
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        border-left: 4px solid;
    }
    .alert-threat {
        background: #fee;
        border-color: #f00;
    }
    .alert-authorized {
        background: #efe;
        border-color: #0f0;
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
        st.session_state.config_loaded = True
    except Exception as e:
        st.session_state.config_loaded = False
        st.session_state.error = str(e)

# Sidebar
with st.sidebar:
    st.image("https://via.placeholder.com/200x100/667eea/ffffff?text=SENTHIUM", width="stretch")
    st.title("🔒 Senthium AI")
    st.markdown("### Navigation")
    
    page = st.radio(
        "Choose a page:",
        ["📊 Dashboard", "👤 Face Enrollment", "🔍 Security Check", "⚙️ Settings"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    st.markdown("### Quick Stats")
    
    if st.session_state.config_loaded:
        try:
            stats = st.session_state.security_manager.get_stats()
            st.metric("System Status", "🟢 Active" if stats.get('enabled', False) else "🔴 Disabled")
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
    st.title("📊 Security Dashboard")
    st.markdown("Real-time overview of your AI security system")
    
    # Stats cards in columns
    col1, col2, col3, col4 = st.columns(4)
    
    try:
        stats = st.session_state.security_manager.get_stats()
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <h3>System Status</h3>
                <h2>{'🟢 Active' if stats.get('enabled', False) else '🔴 Disabled'}</h2>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <h3>Total Checks</h3>
                <h2>{stats.get('total_checks', 0)}</h2>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <h3>Threats</h3>
                <h2>{stats.get('threats_detected', 0)}</h2>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="metric-card">
                <h3>Authorized</h3>
                <h2>{stats.get('authorized_users_count', 0)}</h2>
            </div>
            """, unsafe_allow_html=True)
    
    except Exception as e:
        st.error(f"Error loading stats: {e}")
    
    st.markdown("---")
    
    # Recent Alerts
    st.subheader("🚨 Recent Alerts")
    
    alerts_file = Path("logs/security/alerts.jsonl")
    if alerts_file.exists():
        try:
            with open(alerts_file, 'r') as f:
                alerts = [json.loads(line) for line in f.readlines()[-10:]]  # Last 10 alerts
            
            if alerts:
                for alert in reversed(alerts):  # Show newest first
                    is_threat = alert.get('unknown_faces_count', 0) > 0
                    alert_class = "alert-threat" if is_threat else "alert-authorized"
                    icon = "⚠️" if is_threat else "✅"
                    
                    st.markdown(f"""
                    <div class="alert-card {alert_class}">
                        <strong>{icon} {alert.get('timestamp', 'Unknown time')}</strong><br>
                        Faces: {alert.get('detected_faces_count', 0)} | 
                        Unknown: {alert.get('unknown_faces_count', 0)} | 
                        Confidence: {alert.get('max_confidence', 0):.2f}
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No alerts yet. Perform a security check to see alerts here.")
        except Exception as e:
            st.error(f"Error loading alerts: {e}")
    else:
        st.info("No alerts file found. Perform a security check first.")
    
    # Latest Snapshot
    st.markdown("---")
    st.subheader("📸 Latest Snapshot")
    
    snapshots_dir = Path("logs/security/snapshots")
    if snapshots_dir.exists():
        snapshots = sorted(snapshots_dir.glob("*.jpg"), key=lambda x: x.stat().st_mtime, reverse=True)
        if snapshots:
            latest = snapshots[0]
            st.image(str(latest), caption=f"Captured: {latest.name}", width="stretch")
        else:
            st.info("No snapshots available yet.")
    else:
        st.info("No snapshots directory found.")

# ==================== FACE ENROLLMENT PAGE ====================
elif page == "👤 Face Enrollment":
    st.title("👤 Face Enrollment")
    st.markdown("Add authorized users to the security system")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Upload Face Image")
        
        name = st.text_input("Enter person's name", placeholder="e.g., John Doe")
        uploaded_file = st.file_uploader("Choose an image", type=['jpg', 'jpeg', 'png'])
        
        if uploaded_file is not None:
            # Display preview
            image = Image.open(uploaded_file)
            st.image(image, caption="Preview", width="stretch")
            
            if st.button("🎯 Enroll Face", key="enroll_btn"):
                if not name:
                    st.error("Please enter a name first!")
                else:
                    with st.spinner("Enrolling face..."):
                        try:
                            st.write("🔍 **DEBUG:** Starting enrollment process...")
                            
                            # Save uploaded file temporarily
                            temp_path = Path("temp_upload.jpg")
                            with open(temp_path, "wb") as f:
                                f.write(uploaded_file.getbuffer())
                            st.write(f"✅ **DEBUG:** Saved temp file: {temp_path}")
                            
                            # Direct function call - no subprocess! 💪
                            st.write(f"🔧 **DEBUG:** Enrolling {name} directly via security_manager...")
                            
                            success = st.session_state.security_manager.enroll_owner_from_file(
                                image_path=str(temp_path),
                                user_name=name
                            )
                            
                            # Clean up
                            temp_path.unlink(missing_ok=True)
                            st.write("🧹 **DEBUG:** Cleaned up temp file")
                            
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
        
        faces_dir = Path("config/faces")
        if faces_dir.exists():
            enrolled = list(faces_dir.glob("*.jpg"))
            if enrolled:
                st.info(f"**{len(enrolled)}** users enrolled")
                for face_file in enrolled:
                    name = face_file.stem
                    with st.expander(f"👤 {name}"):
                        try:
                            st.image(str(face_file), width="stretch")
                        except:
                            st.text(name)
            else:
                st.warning("No enrolled users yet")
        else:
            st.warning("Faces directory not found")

# ==================== SECURITY CHECK PAGE ====================
elif page == "🔍 Security Check":
    st.title("🔍 Security Check")
    st.markdown("Perform real-time face recognition security check")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Perform Check")
        
        if st.button("🚀 Run Security Check Now", key="check_btn"):
            with st.spinner("Checking security..."):
                try:
                    st.write("🔍 **DEBUG:** Starting security check...")
                    
                    # Direct function call - no subprocess! 🎯
                    check_result = st.session_state.security_manager.perform_security_check()
                    
                    if check_result:
                        st.success("✅ Security check completed!")
                        
                        # Display results
                        st.json(check_result)
                        
                        # Show warning if threats detected
                        unknown_count = check_result.get('unknown_faces_count', 0)
                        detected_count = check_result.get('detected_faces_count', 0)
                        
                        if unknown_count > 0:
                            st.error(f"⚠️ WARNING: {unknown_count} unauthorized face(s) detected!")
                        elif detected_count > 0:
                            st.success(f"✅ All detected faces are authorized!")
                        else:
                            st.info("ℹ️ No faces detected in this check")
                    else:
                        st.warning("Security is disabled or check returned no data")
                
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
            
            st.metric("Total Checks Performed", stats.get('total_checks', 0))
            st.metric("Threats Detected", stats.get('threats_detected', 0), 
                     delta=f"{stats.get('threats_detected', 0)} threats")
            st.metric("Last Check", stats.get('last_check_time', 'Never'))
        
        except Exception as e:
            st.error(f"Error loading stats: {e}")

# ==================== SETTINGS PAGE ====================
elif page == "⚙️ Settings":
    st.title("⚙️ Settings")
    st.markdown("Configure your security system")
    
    # Security Toggle
    st.subheader("🔐 Security System")
    
    try:
        stats = st.session_state.security_manager.get_stats()
        is_enabled = stats.get('enabled', False)
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.write(f"**Current Status:** {'🟢 Enabled' if is_enabled else '🔴 Disabled'}")
        
        with col2:
            if is_enabled:
                if st.button("🔴 Disable", key="disable_btn"):
                    st.write("🔍 **DEBUG:** Disabling security...")
                    st.session_state.security_manager.disable()
                    st.success("Security disabled")
                    st.rerun()
            else:
                if st.button("🟢 Enable", key="enable_btn"):
                    st.write("🔍 **DEBUG:** Enabling security...")
                    st.session_state.security_manager.enable()
                    st.success("Security enabled")
                    st.rerun()
    
    except Exception as e:
        st.error(f"Error: {e}")
    
    st.markdown("---")
    
    # Alert Channels
    st.subheader("📢 Alert Channels")
    
    config_path = Path("config/config.yaml")
    if config_path.exists():
        try:
            validator = ConfigSchema()
            config = validator.load_and_validate(config_path)
            alerts = config['senthium']['security']['alerts']
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.checkbox("🖥️ Desktop Notifications", value=alerts.get('desktop_notification', False), disabled=True)
                st.checkbox("🔔 Sound Alerts", value=alerts.get('sound_alert', False), disabled=True)
            
            with col2:
                st.checkbox("✉️ Email Alerts", value=alerts.get('email', {}).get('enabled', False), disabled=True)
                st.checkbox("💬 Telegram Alerts", value=alerts.get('telegram', {}).get('enabled', False), disabled=True)
            
            with col3:
                st.checkbox("💜 Discord Alerts", value=alerts.get('discord', {}).get('enabled', False), disabled=True)
                st.checkbox("📝 Log to File", value=alerts.get('log_to_file', False), disabled=True)
            
            st.info("💡 Edit `config/config.yaml` to change alert settings")
        
        except Exception as e:
            st.error(f"Error loading config: {e}")
    
    st.markdown("---")
    
    # Daemon Control
    st.subheader("🤖 Daemon Control")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("▶️ Start Daemon"):
            with st.spinner("Starting daemon..."):
                st.write("🔍 **DEBUG:** Starting daemon...")
                try:
                    exit_code = start_daemon()
                    if exit_code == 0:
                        st.success("✅ Daemon started!")
                    else:
                        st.error("❌ Failed to start daemon")
                except Exception as e:
                    st.error(f"❌ Exception: {e}")
    
    with col2:
        if st.button("⏹️ Stop Daemon"):
            with st.spinner("Stopping daemon..."):
                st.write("🔍 **DEBUG:** Stopping daemon...")
                try:
                    exit_code = stop_daemon()
                    if exit_code == 0:
                        st.success("✅ Daemon stopped!")
                    else:
                        st.error("❌ Failed to stop daemon")
                except Exception as e:
                    st.error(f"❌ Exception: {e}")
    
    with col3:
        if st.button("🔄 Restart Daemon"):
            with st.spinner("Restarting daemon..."):
                st.write("🔍 **DEBUG:** Restarting daemon...")
                try:
                    stop_daemon()
                    time.sleep(1)  # Wait a sec between stop/start
                    exit_code = start_daemon()
                    if exit_code == 0:
                        st.success("✅ Daemon restarted!")
                    else:
                        st.error("❌ Failed to restart")
                except Exception as e:
                    st.error(f"❌ Exception: {e}")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 2rem;'>
    <p><strong>Senthium AI Security System</strong> v0.6.0</p>
    <p>🔒 Intelligent Wake-Lock + AI Face Recognition</p>
    <p>Made with 💖 using Streamlit</p>
</div>
""", unsafe_allow_html=True)
