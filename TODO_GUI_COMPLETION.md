# 🎯 Senthium AI - GUI Completion & Feature Implementation TODO

**Date:** November 12, 2025  
**Current Status:** Core features working, GUI needs completion  
**Priority:** High - Make GUI match planned features

---

## 📋 **CURRENT STATE ANALYSIS**

### ✅ **Working Features:**
- ✅ Daemon running in background (PID: 18212)
- ✅ Face enrollment (1 user enrolled: "ss")
- ✅ Intruder detection (28 events captured!)
- ✅ Intruder patterns tracking (1 pattern, 2 detections)
- ✅ Forensics timeline with snapshots
- ✅ Settings page with all configs
- ✅ Email alerts configured (Active)
- ✅ Auto-lock and alarm on intruder
- ✅ 596 snapshots stored (unencrypted)

### ❌ **Missing/Incomplete Features:**
- ❌ Dashboard missing system stats (CPU, Memory, Disk, Network)
- ❌ Dashboard missing daemon status card
- ❌ Dashboard missing rules display
- ❌ No "System Monitor" page (real-time graphs)
- ❌ No "Haunting Mode" page
- ❌ No dedicated "Snapshot Encryption" page (only in Settings)
- ❌ Security system shows "DISABLED" but daemon is monitoring
- ❌ No daemon control from Dashboard (only in Settings)

---

## 🚀 **TODO LIST - PRIORITIZED**

### **PRIORITY 1: Critical Dashboard Fixes** 🔥

#### TODO 1.1: Add Daemon Status Card to Dashboard
**File:** `streamlit_app.py` - Dashboard page section  
**What to add:**
```python
# Daemon Status Card
with st.container():
    daemon_status = get_daemon_status()  # Returns running/stopped + PID
    if daemon_status['running']:
        st.success(f"🟢 Daemon Running (PID: {daemon_status['pid']})")
        if st.button("⏹️ Stop Daemon"):
            stop_daemon()
    else:
        st.error("🔴 Daemon Stopped")
        if st.button("▶️ Start Daemon"):
            start_daemon()
```
**Reason:** Users need to see daemon status at a glance on main dashboard

---

#### TODO 1.2: Add System Stats to Dashboard
**File:** `streamlit_app.py` - Dashboard page  
**What to add:**
```python
# System Statistics
col1, col2, col3, col4 = st.columns(4)
metrics = get_system_metrics()

with col1:
    st.metric("💻 CPU Usage", f"{metrics['cpu']}%", delta="+2%")
with col2:
    st.metric("🧠 Memory", f"{metrics['memory']}%", delta="-5%")
with col3:
    st.metric("💾 Disk I/O", f"{metrics['disk_io']} MB/s")
with col4:
    st.metric("🌐 Network", f"{metrics['network']} MB/s")
```
**Dependencies:** Need to integrate with `src/daemon/monitor.py` to get real-time stats  
**Reason:** Core feature - system monitoring is main purpose of daemon

---

#### TODO 1.3: Display Active Rules on Dashboard
**File:** `streamlit_app.py` - Dashboard page  
**What to add:**
```python
# Active Rules Display
st.subheader("📋 Active Rules")
config = load_config()
rules = config['senthium']['rules']

for rule in rules:
    if rule['enabled']:
        st.info(f"✅ {rule['name']} - {rule['type']}")
    else:
        st.warning(f"⏸️ {rule['name']} (disabled)")
```
**Dependencies:** Config loading already works  
**Reason:** Users need to see what rules are preventing sleep

---

### **PRIORITY 2: Add Missing Pages** 🎨

#### TODO 2.1: Create "System Monitor" Page
**File:** `streamlit_app.py` - New page in navigation  
**What to implement:**
- Real-time CPU/Memory/Disk/Network graphs (using Plotly/Altair)
- Process list table (top 20 processes by CPU)
- Auto-refresh every 2 seconds
- Search/filter processes

**Reference:** See `MANUAL_TESTING_GUIDE.md` Test 7  
**Code location:** After "Dashboard" page, before "Security Check"  
**Estimated effort:** 2-3 hours

---

#### TODO 2.2: Create "Haunting Mode" Page
**File:** `streamlit_app.py` - New page in navigation  
**What to implement:**
- Enable/Disable haunting mode toggle
- Escalation level slider (Polite → Firm → Aggressive)
- Custom TTS message input
- Voice selection (if available)
- Volume control
- Preview/test TTS button

**Reference:** See `HAUNTING_MODE.md` for full spec  
**Dependencies:** `src/security/haunting_mode.py` already exists  
**Code example:**
```python
haunting_enabled = st.toggle("👻 Enable Haunting Mode", value=config['haunting_mode']['enabled'])

escalation = st.slider("Escalation Level", 1, 3, value=2, 
                       help="1=Polite, 2=Firm, 3=Aggressive")

custom_msg = st.text_area("Custom Message (optional)", 
                          placeholder="I see you there...")

if st.button("🔊 Test Haunting Message"):
    test_haunting_mode(escalation, custom_msg)
```
**Estimated effort:** 1-2 hours

---

#### TODO 2.3: Create Dedicated "Snapshot Encryption" Page
**File:** `streamlit_app.py` - New page  
**Current state:** Encryption section exists in Settings, needs full page  
**What to implement:**
- Gallery view of unencrypted snapshots (thumbnails)
- Gallery view of encrypted snapshots
- Select multiple snapshots to encrypt/decrypt
- Bulk actions (Encrypt All, Decrypt All)
- Encryption statistics
- Key management (show key, regenerate key)

**Reference:** See `MANUAL_TESTING_GUIDE.md` Test 13  
**Dependencies:** `src/security/snapshot_encryption.py` already exists  
**Note:** Settings page already has encryption section at bottom - can expand this  
**Estimated effort:** 2 hours

---

### **PRIORITY 3: Fix Existing Issues** 🔧

#### TODO 3.1: Fix "Security System: DISABLED" Status
**Issue:** Dashboard shows "System Status: Disabled" but daemon is monitoring and catching intruders!  
**Root cause:** Need to check if security monitoring is actually enabled in code  
**Files to check:**
- `streamlit_app.py` - Dashboard status logic
- `config/config.yaml` - `security.enabled` value
- `src/daemon/core.py` - Security check logic

**Fix:**
```python
# In dashboard
security_config = config['senthium']['security']
if security_config['enabled']:
    st.success("🟢 Security System: ACTIVE")
else:
    st.error("🔴 Security System: DISABLED")
```

**Reason:** Confusing UX - shows disabled but is actually working  
**Estimated effort:** 30 minutes

---

#### TODO 3.2: Add Daemon Controls to Dashboard
**Issue:** Stop/Start/Restart daemon buttons only in Settings, should be on Dashboard too  
**What to add:**
```python
# Daemon Control Buttons
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("⏹️ Stop Daemon", use_container_width=True):
        daemon_control.stop_daemon()
with col2:
    if st.button("▶️ Start Daemon", use_container_width=True):
        daemon_control.start_daemon()
with col3:
    if st.button("🔄 Restart Daemon", use_container_width=True):
        daemon_control.restart_daemon()
```
**Estimated effort:** 15 minutes

---

### **PRIORITY 4: Feature Completion** ✨

#### TODO 4.1: Verify Haunting Mode Backend Works
**File:** `src/security/haunting_mode.py`  
**What to test:**
- TTS engine initialized correctly
- Messages play on intruder detection
- Escalation logic works (Level 1 → 2 → 3)
- Volume increases with escalation
- Custom messages work

**Test command:**
```bash
python -c "from src.security.haunting_mode import HauntingMode; h = HauntingMode(); h.haunt(level=2)"
```

---

#### TODO 4.2: Implement Snapshot Encryption Backend
**File:** `src/security/snapshot_encryption.py`  
**Current state:** File exists with 596 snapshots unencrypted  
**What to verify:**
- Encryption key generated (or in config)
- `encrypt_snapshot()` method works
- `decrypt_snapshot()` method works
- Bulk operations work
- `.enc` files created correctly

**Test command:**
```bash
python -c "from src.security.snapshot_encryption import SnapshotEncryption; se = SnapshotEncryption(); print(se.get_stats())"
```

---

#### TODO 4.3: Add Discord Alerts
**Current state:** Email alerts working (Active), Discord shows "Inactive"  
**What to implement:**
- Discord webhook configuration in Settings (already has UI!)
- Test Discord alert button functionality
- Send Discord message on intruder detection
- Attach snapshot to Discord embed

**File:** `src/alerts/notifier.py` - Discord section  
**Dependencies:** `discord-webhook` library (might need pip install)

---

#### TODO 4.4: Implement Telegram Alerts
**Current state:** Settings shows "Telegram Bot" option  
**What to implement:**
- Telegram bot token configuration
- Chat ID configuration
- Send message via Telegram on intruder
- Attach snapshot to Telegram message

**File:** `src/alerts/notifier.py` - Telegram section  
**Dependencies:** `python-telegram-bot` library

---

### **PRIORITY 5: Polish & Testing** 💎

#### TODO 5.1: Add Loading Spinners
**Where:** All pages that fetch data (Dashboard, Forensics, Patterns)  
**What to add:**
```python
with st.spinner("Loading data..."):
    data = load_data()
```

---

#### TODO 5.2: Add Error Handling
**Where:** All pages  
**What to add:**
```python
try:
    # existing code
except Exception as e:
    st.error(f"❌ Error: {e}")
    st.exception(e)  # For debugging
```

---

#### TODO 5.3: Add Success/Info Messages
**Where:** All actions (save config, enroll face, etc.)  
**What to add:**
```python
st.success("✅ Configuration saved successfully!")
st.info("ℹ️ Changes will take effect after daemon restart")
st.warning("⚠️ High recognition tolerance may cause false positives")
```

---

#### TODO 5.4: Test All Features End-to-End
**Manual testing checklist:**
- [ ] Enroll new face
- [ ] Trigger intruder detection
- [ ] Verify alert sent (email)
- [ ] Check forensics timeline
- [ ] Verify pattern tracking
- [ ] Test haunting mode
- [ ] Test snapshot encryption
- [ ] Test daemon stop/start/restart
- [ ] Verify system monitor graphs update
- [ ] Test all config changes

---

## 📊 **FEATURE COMPARISON TABLE**

| Feature | Brainstormed | Implemented | GUI Available | Status |
|---------|-------------|-------------|---------------|--------|
| Face Enrollment | ✅ | ✅ | ✅ | Working |
| Face Recognition | ✅ | ✅ | ✅ | Working |
| Intruder Detection | ✅ | ✅ | ✅ | Working (28 events!) |
| Intruder Patterns | ✅ | ✅ | ✅ | Working (1 pattern) |
| Forensics Timeline | ✅ | ✅ | ✅ | Working (28 events) |
| Auto-Lock Screen | ✅ | ✅ | ✅ | Working |
| Alarm Sound | ✅ | ✅ | ✅ | Working |
| Email Alerts | ✅ | ✅ | ✅ | Working (Active) |
| Discord Alerts | ✅ | ✅ | ❌ | Backend done, needs config |
| Telegram Alerts | ✅ | ✅ | ❌ | Backend done, needs config |
| Snapshot Encryption | ✅ | ✅ | ⚠️ | Partial (in Settings only) |
| Haunting Mode | ✅ | ✅ | ❌ | No GUI page |
| System Monitor | ✅ | ✅ | ❌ | No GUI page |
| Dashboard Stats | ✅ | ✅ | ❌ | Missing from Dashboard |
| Rules Display | ✅ | ✅ | ❌ | Missing from Dashboard |
| Daemon Control | ✅ | ✅ | ⚠️ | Only in Settings |
| Calibration Wizard | ✅ | ✅ | ✅ | Working |
| Critical Apps Protection | ✅ | ✅ | ✅ | Working (python.exe protected) |

**Legend:**
- ✅ Complete
- ⚠️ Partial
- ❌ Missing
- 🚧 In Progress

---

## 🎯 **NEXT STEPS (Prioritized Execution Order)**

### **Today (2-3 hours):**
1. ✅ Fix Dashboard - Add daemon status card
2. ✅ Fix Dashboard - Add system stats (CPU, Memory, Disk, Network)
3. ✅ Fix Dashboard - Show active rules
4. ✅ Fix "System Status: Disabled" → "ACTIVE"

### **Tomorrow (3-4 hours):**
5. ✅ Create "System Monitor" page with graphs
6. ✅ Create "Haunting Mode" page
7. ✅ Add daemon controls to Dashboard

### **Day After (2-3 hours):**
8. ✅ Expand "Snapshot Encryption" to full page
9. ✅ Configure Discord alerts
10. ✅ Test all features end-to-end

---

## 📚 **REFERENCE DOCUMENTS**

Check these files for full specs:
- `MANUAL_TESTING_GUIDE.md` - Complete testing procedures
- `HAUNTING_MODE.md` - Haunting mode full specification
- `INFO.MD` - Original brainstorming and features
- `config/config.yaml` - All settings and configurations

---

## 🐛 **KNOWN BUGS TO FIX**

1. **Dashboard shows "System Status: Disabled"** - Needs to reflect actual security state
2. **No daemon controls on Dashboard** - Only in Settings
3. **No CPU/Memory graphs** - Core monitoring feature missing from UI
4. **Haunting mode has no GUI** - Backend works but no page to configure
5. **System Monitor page missing** - No real-time monitoring graphs

---

## 💡 **FUTURE ENHANCEMENTS (Post-MVP)**

- [ ] Add 2FA for Streamlit dashboard
- [ ] Mobile-responsive design improvements
- [ ] Dark/Light theme toggle
- [ ] Export forensics to PDF report
- [ ] Face recognition accuracy metrics
- [ ] Pattern threat level auto-escalation
- [ ] Webhook integration for custom alerts
- [ ] System tray icon for Windows
- [ ] Auto-start daemon on system boot
- [ ] Cloud backup of snapshots

---

**Made with 💕 by your AI Developer Waifu**  
**Let's make Senthium the best security system ever! 🚀**
