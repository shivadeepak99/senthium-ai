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

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.vision.security_manager import SecurityManager
from src.rules.schema import ConfigSchema
from src.daemon.control import start_daemon, stop_daemon
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
            
            # Daemon status indicator
            pid_file = PIDFile()
            is_daemon_running = pid_file.is_running()
            daemon_status = "🟢 Running" if is_daemon_running else "🔴 Stopped"
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
        st.subheader("📷 Capture or Upload Face Image")
        
        name = st.text_input("Enter person's name", placeholder="e.g., John Doe")
        
        # Create tabs for different input methods 🎨
        tab1, tab2 = st.tabs(["📸 Capture from Webcam", "📁 Upload Image"])
        
        with tab1:
            st.markdown("### Take a photo using your webcam")
            
            col_a, col_b, col_c = st.columns([1, 2, 1])
            
            with col_b:
                if st.button("📸 Take Photo", key="capture_btn", use_container_width=True):
                    if not name:
                        st.error("⚠️ Please enter a name first!")
                    else:
                        with st.spinner("📷 Capturing from webcam..."):
                            try:
                                # Initialize camera if needed
                                if not st.session_state.security_manager.camera._is_initialized:
                                    st.session_state.security_manager.camera.initialize()
                                
                                # Capture frame
                                frame = st.session_state.security_manager.camera.capture_frame()
                                
                                if frame is not None:
                                    # Store in session state for preview
                                    st.session_state['captured_frame'] = frame
                                    st.session_state['captured_name'] = name
                                    st.success("✅ Photo captured! Review below.")
                                    st.rerun()
                                else:
                                    st.error("❌ Failed to capture image from webcam. Make sure your camera is connected!")
                            
                            except Exception as e:
                                st.error(f"💥 Camera error: {e}")
                                import traceback
                                st.code(traceback.format_exc(), language="python")
            
            # Show captured preview and enroll button
            if 'captured_frame' in st.session_state:
                st.divider()
                st.markdown("### 📸 Captured Photo")
                
                # Convert BGR to RGB for display
                import cv2
                rgb_frame = cv2.cvtColor(st.session_state['captured_frame'], cv2.COLOR_BGR2RGB)
                st.image(rgb_frame, caption=f"Preview: {st.session_state.get('captured_name', 'Unknown')}", use_container_width=True)
                
                col_x, col_y = st.columns(2)
                
                with col_x:
                    if st.button("✅ Enroll This Face", key="enroll_captured", use_container_width=True):
                        with st.spinner("🎯 Enrolling face..."):
                            try:
                                # Save temp file
                                temp_path = Path("temp_webcam_capture.jpg")
                                cv2.imwrite(str(temp_path), st.session_state['captured_frame'])
                                
                                # Enroll
                                success = st.session_state.security_manager.enroll_owner_from_file(
                                    image_path=str(temp_path),
                                    user_name=st.session_state['captured_name']
                                )
                                
                                # IMPORTANT: Release camera after enrollment!
                                print("[DEBUG] Releasing camera after webcam enrollment...")
                                st.session_state.security_manager.camera.release()
                                
                                # Cleanup
                                temp_path.unlink(missing_ok=True)
                                
                                if success:
                                    st.success(f"✅ Successfully enrolled {st.session_state['captured_name']}!")
                                    st.balloons()
                                    # Clear session state
                                    del st.session_state['captured_frame']
                                    del st.session_state['captured_name']
                                    st.rerun()
                                else:
                                    st.error("❌ Enrollment failed - no face detected or error occurred")
                            
                            except Exception as e:
                                st.error(f"💥 Enrollment error: {e}")
                                import traceback
                                st.code(traceback.format_exc(), language="python")
                
                with col_y:
                    if st.button("🔄 Retake Photo", key="retake_btn", use_container_width=True):
                        # Release camera before retake
                        print("[DEBUG] Releasing camera for retake...")
                        st.session_state.security_manager.camera.release()
                        del st.session_state['captured_frame']
                        del st.session_state['captured_name']
                        st.rerun()
        
        with tab2:
            st.markdown("### Upload an image file")
            uploaded_file = st.file_uploader("Choose an image", type=['jpg', 'jpeg', 'png'])
            
            if uploaded_file is not None:
                # Display preview
                image = Image.open(uploaded_file)
                st.image(image, caption="Preview", use_container_width=True)
                
                if st.button("🎯 Enroll Face", key="enroll_btn", use_container_width=True):
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
            if st.button("💾 Save Discord Config", key="save_discord", use_container_width=True):
                print(f"🔍 DEBUG: Saving Discord - Enabled={discord_enabled}, URL={'SET' if discord_webhook else 'EMPTY'}")
                
                if st.session_state.config_manager.update_discord(discord_webhook, discord_enabled):
                    print(f"✅ DEBUG: Discord config saved successfully!")
                    st.success("✅ Discord configuration saved!")
                    st.info("💡 Restart daemon to apply changes")
                    
                    # Update notifier config
                    st.session_state.security_manager.notifier.config['discord_webhook_url'] = discord_webhook
                    st.session_state.security_manager.notifier.config['discord_enabled'] = discord_enabled
                    print(f"🔄 DEBUG: Updated SecurityManager notifier config")
                    
                    st.rerun()
                else:
                    print(f"❌ DEBUG: Failed to save Discord config")
                    st.error("❌ Failed to save configuration")
        
        with col_test:
            if st.button("🧪 Test Discord Alert", key="test_discord", use_container_width=True, disabled=not discord_webhook):
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
                    response = requests.post(discord_webhook, json=test_payload, timeout=10)
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
            if st.button("💾 Save Email Config", key="save_email", use_container_width=True):
                print(f"🔍 DEBUG: Saving Email - Enabled={email_enabled}, Server={smtp_server}, Port={smtp_port}")
                print(f"🔍 DEBUG: Email - Username={smtp_username}, Recipient={recipient_email}")
                
                if st.session_state.config_manager.update_email(
                    smtp_server, smtp_port, smtp_username, smtp_password, recipient_email, email_enabled
                ):
                    print(f"✅ DEBUG: Email config saved successfully!")
                    st.success("✅ Email configuration saved!")
                    st.info("💡 Restart daemon to apply changes")
                    
                    # Update notifier config
                    st.session_state.security_manager.notifier.config['email_smtp_host'] = smtp_server
                    st.session_state.security_manager.notifier.config['email_smtp_port'] = smtp_port
                    st.session_state.security_manager.notifier.config['email_from'] = smtp_username
                    st.session_state.security_manager.notifier.config['email_to'] = recipient_email
                    st.session_state.security_manager.notifier.config['email_password'] = smtp_password
                    st.session_state.security_manager.notifier.config['email_enabled'] = email_enabled
                    print(f"🔄 DEBUG: Updated SecurityManager notifier email config")
                    
                    st.rerun()
                else:
                    print(f"❌ DEBUG: Failed to save Email config")
                    st.error("❌ Failed to save configuration")
        
        with col_test:
            test_disabled = not (smtp_server and smtp_username and smtp_password and recipient_email)
            if st.button("🧪 Test Email Alert", key="test_email", use_container_width=True, disabled=test_disabled):
                print(f"🧪 DEBUG: Testing Email SMTP connection...")
                try:
                    import smtplib
                    from email.mime.text import MIMEText
                    from email.mime.multipart import MIMEMultipart
                    
                    msg = MIMEMultipart()
                    msg['From'] = smtp_username
                    msg['To'] = recipient_email
                    msg['Subject'] = "🧪 Test Alert - Senthium AI"
                    
                    body = """
                    This is a test alert from your Senthium AI Security System!
                    
                    If you received this email, your SMTP configuration is working correctly.
                    
                    ---
                    Senthium AI Security System
                    """
                    msg.attach(MIMEText(body, 'plain'))
                    
                    print(f"🔗 DEBUG: Connecting to {smtp_server}:{smtp_port}...")
                    server = smtplib.SMTP(smtp_server, smtp_port)
                    server.starttls()
                    print(f"🔐 DEBUG: Logging in as {smtp_username}...")
                    server.login(smtp_username, smtp_password)
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
            
            if st.session_state.config_manager.update_telegram(telegram_token, telegram_chat_id, telegram_enabled):
                print(f"✅ DEBUG: Telegram config saved successfully!")
                st.success("✅ Telegram configuration saved!")
                st.info("💡 Restart daemon to apply changes")
                
                # Update notifier config
                st.session_state.security_manager.notifier.config['telegram_bot_token'] = telegram_token
                st.session_state.security_manager.notifier.config['telegram_chat_id'] = telegram_chat_id
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
        if st.session_state.config_manager.update_monitoring(
            check_interval, recognition_tolerance, camera_index, alert_cooldown
        ):
            st.success("✅ Monitoring settings saved!")
            st.info("💡 Restart daemon to apply changes")
            st.rerun()
        else:
            st.error("❌ Failed to save configuration")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 2rem;'>
    <p><strong>Senthium AI Security System</strong> v0.6.0</p>
    <p>🔒 Intelligent Wake-Lock + AI Face Recognition</p>
    <p>Made with 💖 using Streamlit</p>
</div>
""", unsafe_allow_html=True)
