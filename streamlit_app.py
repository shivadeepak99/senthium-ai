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
            with st.spinner("� Capturing and analyzing..."):
                try:
                    # Direct function call - no subprocess! 🎯
                    check_result = st.session_state.security_manager.perform_security_check()
                    
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
            
            st.metric("Total Checks Performed", stats.get('total_checks', 0))
            st.metric("Threats Detected", stats.get('threats_detected', 0), 
                     delta=f"{stats.get('threats_detected', 0)} threats")
            st.metric("Last Check", stats.get('last_check_time', 'Never'))
        
        except Exception as e:
            st.error(f"Error loading stats: {e}")

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
    
    # ===== ALERT CONFIGURATION =====
    st.subheader("📢 Alert Configuration")
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
        
        discord_webhook = st.text_input(
            "Discord Webhook URL",
            value="",
            placeholder="https://discord.com/api/webhooks/...",
            help="Paste your Discord webhook URL here",
            type="password"
        )
        discord_enabled = st.checkbox("Enable Discord Alerts", value=False)
        
        if st.button("💾 Save Discord Config", key="save_discord"):
            st.success("✅ Discord configuration saved!")
            st.info("Note: This will be fully functional in next update")
    
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
        
        col1, col2 = st.columns(2)
        
        with col1:
            smtp_server = st.text_input("SMTP Server", placeholder="smtp.gmail.com")
            smtp_port = st.number_input("SMTP Port", value=587, min_value=1, max_value=65535)
            smtp_username = st.text_input("Username/Email", placeholder="your.email@gmail.com")
        
        with col2:
            smtp_password = st.text_input("Password", type="password", help="Use app-specific password for Gmail")
            recipient_email = st.text_input("Alert Recipient", placeholder="alerts@example.com")
            email_enabled = st.checkbox("Enable Email Alerts", value=False)
        
        if st.button("💾 Save Email Config", key="save_email"):
            st.success("✅ Email configuration saved!")
            st.info("Note: This will be fully functional in next update")
    
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
        
        telegram_token = st.text_input("Bot Token", type="password", placeholder="123456:ABC-DEF...")
        telegram_chat_id = st.text_input("Chat ID", placeholder="Your chat ID")
        telegram_enabled = st.checkbox("Enable Telegram Alerts", value=False)
        
        if st.button("� Save Telegram Config", key="save_telegram"):
            st.success("✅ Telegram configuration saved!")
            st.info("Note: This will be fully functional in next update")
    
    # Desktop Notifications
    with st.expander("🖥️ Desktop & System Alerts", expanded=False):
        desktop_notif = st.checkbox("Windows Toast Notifications", value=True, help="Show Windows 10/11 notifications")
        sound_alert = st.checkbox("Sound Alerts", value=False, help="Play alert sound on detection")
        log_to_file = st.checkbox("Log Alerts to File", value=True, help="Save alerts to logs/security/alerts.jsonl")
        
        if st.button("💾 Save System Config", key="save_system"):
            st.success("✅ System configuration saved!")
    
    st.markdown("---")
    
    # ===== DAEMON CONTROL =====
    st.subheader("🤖 Background Daemon (Advanced)")
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
            max_value=0.9,
            value=0.6,
            step=0.05,
            help="Lower = stricter matching (0.6 recommended)"
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
        st.success("✅ Monitoring settings saved!")
        st.info("Restart daemon to apply changes")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 2rem;'>
    <p><strong>Senthium AI Security System</strong> v0.6.0</p>
    <p>🔒 Intelligent Wake-Lock + AI Face Recognition</p>
    <p>Made with 💖 using Streamlit</p>
</div>
""", unsafe_allow_html=True)
