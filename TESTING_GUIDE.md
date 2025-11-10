# 🧪 Senthium AI - Testing Guide & Feature Documentation

**Version:** 0.6.0  
**Date:** November 10, 2025  
**Purpose:** Complete guide for testing all features and understanding system behavior

---

## 📋 Table of Contents

1. [System Overview](#system-overview)
2. [Features & Capabilities](#features--capabilities)
3. [Page-by-Page Testing Guide](#page-by-page-testing-guide)
4. [Expected Behaviors](#expected-behaviors)
5. [Testing Checklist](#testing-checklist)
6. [Troubleshooting](#troubleshooting)

---

## 🎯 System Overview

**Senthium AI** is an intelligent security system with two main components:

### Core Components

1. **Streamlit Dashboard** (`streamlit_app.py`)
   - Web-based GUI for monitoring and configuration
   - Runs on: `http://localhost:8501`
   - Start with: `.\venv311\Scripts\streamlit.exe run streamlit_app.py`

2. **Background Daemon** (Optional)
   - 24/7 automated monitoring service
   - Runs independently in background
   - Performs face recognition checks every 5-10 seconds

### AI Technology Stack

- **Face Detection:** OpenCV DNN (ResNet-10 SSD)
- **Face Recognition:** DeepFace 0.0.95 (Facenet CNN)
- **Embedding:** 128-dimensional facial encodings
- **Matching:** Euclidean distance with 0.6 tolerance

---

## 🚀 Features & Capabilities

### ✅ Face Recognition Security
- ✅ Enroll authorized users via webcam or file upload
- ✅ Real-time face detection and recognition
- ✅ Multi-face detection support
- ✅ Persistent storage of facial encodings
- ✅ Remove enrolled users

### ✅ Security Enforcement Actions
- ✅ **Lock Screen** - Instantly lock Windows when intruder detected
- ✅ **Sleep Computer** - Put system to sleep (optional, disabled by default)
- ✅ **Play Alarm Sound** - Audible alert (ascending beep pattern)
- ✅ Configurable per-action enable/disable

### ✅ Multi-Channel Alerts
- ✅ **Discord Webhook** - Instant alerts to Discord server
- ✅ **Email (SMTP)** - Email alerts with full details
- ✅ **Telegram Bot** - Mobile push notifications
- ✅ **Desktop Notifications** - Windows 10/11 toast notifications
- ✅ **Sound Alerts** - System beep on detection
- ✅ **File Logging** - JSONL logs for audit trail

### ✅ Dashboard Features
- ✅ Real-time alert feed
- ✅ Statistics: total alerts, unknown faces, authorized access
- ✅ Visual alert cards with gradient styling
- ✅ Daemon status indicator
- ✅ Recent alerts timeline

---

## 📱 Page-by-Page Testing Guide

### 1️⃣ **Dashboard Page (Home)**

**What You See:**
```
┌─────────────────────────────────────────────────┐
│ 🔒 Senthium AI Security - Dashboard             │
├─────────────────────────────────────────────────┤
│                                                  │
│  [Total Alerts] [Unknown Faces] [Authorized]   │
│       42            12              30          │
│                                                  │
│  🚨 Recent Security Alerts                      │
│  ┌──────────────────────────────────────────┐  │
│  │ ⚠️ Unauthorized Access                    │  │
│  │ 1 unknown face detected                   │  │
│  │ 2024-11-10 14:23:45                       │  │
│  │ [View Snapshot] [View Details]            │  │
│  └──────────────────────────────────────────┘  │
│                                                  │
│  ┌──────────────────────────────────────────┐  │
│  │ ✅ Authorized Access                      │  │
│  │ 1 known face: shivadeepak                 │  │
│  │ 2024-11-10 14:20:12                       │  │
│  └──────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

**What Happens When You Click:**
- **Refresh Dashboard Button** → Reloads page, fetches latest alerts from `logs/security/alerts.jsonl`
- **View Snapshot Link** → Opens saved webcam image from `logs/security/snapshots/`
- **View Details Button** → Expands alert card showing full JSON data

**Expected Behavior:**
- Alert cards auto-load from most recent first
- Red gradient for unauthorized alerts
- Green gradient for authorized access
- Metrics show cumulative counts since system start
- Empty state message if no alerts yet: "No alerts yet. System is monitoring..."

**Testing Steps:**
1. Open dashboard - should see welcome message
2. If daemon running - should see recent alerts
3. Click "Refresh" - page reloads instantly
4. Check metrics numbers match alert count

---

### 2️⃣ **Face Enrollment Page**

**What You See:**
```
┌─────────────────────────────────────────────────┐
│ 👤 Face Enrollment                               │
├─────────────────────────────────────────────────┤
│                                                  │
│ Enter person's name: [____________]              │
│                                                  │
│ ┌─────────────────┬─────────────────────────┐  │
│ │ 📸 Capture from │ 📁 Upload Image         │  │
│ │    Webcam       │                         │  │
│ └─────────────────┴─────────────────────────┘  │
│                                                  │
│ ### Take a photo using your webcam              │
│                                                  │
│         [📸 Take Photo]                          │
│                                                  │
│ ─────────────────────────────────────────────   │
│ ### 📸 Captured Photo                           │
│ [Image Preview: John Doe]                       │
│                                                  │
│ [✅ Enroll This Face]  [🔄 Retake Photo]        │
│                                                  │
└─────────────────────────────────────────────────┘

┌─────────────────┐
│ 📋 Enrolled     │
│    Users        │
├─────────────────┤
│ ✅ 2 user(s)    │
│                 │
│ ▶ shivadeepak   │
│ ▶ alice         │
└─────────────────┘
```

**What Happens When You Click:**

#### **📸 Capture from Webcam Tab:**
1. **Enter Name** → Type user's name (required)
2. **"📸 Take Photo" Button** → 
   - Camera LED blinks
   - Captures single frame from webcam
   - Shows preview below button
   - Error if no name entered: "⚠️ Please enter a name first!"
   - Error if camera fails: "❌ Failed to capture image from webcam"

3. **"✅ Enroll This Face" Button** → 
   - Saves temp file: `temp_webcam_capture.jpg`
   - Runs DeepFace face detection
   - Generates 128-dim facial encoding
   - Saves to `config/faces/authorized.json`
   - Success: "✅ Successfully enrolled {name}!" + 🎈 balloons
   - Failure: "❌ Enrollment failed - no face detected or error occurred"
   - Clears preview, returns to input state

4. **"🔄 Retake Photo" Button** →
   - Clears current preview
   - Returns to input state
   - Can take new photo

#### **📁 Upload Image Tab:**
1. **File Uploader** → Accepts .jpg, .jpeg, .png
2. **Shows Preview** → Displays uploaded image
3. **"🎯 Enroll Face" Button** →
   - Same enrollment process as webcam
   - Saves temp file: `temp_upload.jpg`
   - Success/failure same as above

#### **Enrolled Users Sidebar:**
- **Expander "👤 {name}"** → Click to expand user details
  - Shows face encoding count
  - Shows "🗑️ Remove {name}" button
- **"🗑️ Remove" Button** →
  - Deletes user from `authorized.json`
  - Success: "Removed {name}"
  - Page refreshes, user disappears

**Expected Behavior:**
- Webcam initializes on first photo capture (may take 2-3 seconds)
- Preview shows BGR→RGB converted image (natural colors)
- Enrollment works if at least 1 clear face visible
- Multiple attempts allowed if face not detected
- Enrolled users persist across app restarts
- Same person can be enrolled multiple times (adds more encodings for better accuracy)

**Testing Steps:**
1. **Test Webcam Capture:**
   - Enter name: "TestUser1"
   - Click "📸 Take Photo"
   - Verify preview appears
   - Click "✅ Enroll This Face"
   - Check success message + balloons
   - Verify user appears in sidebar

2. **Test File Upload:**
   - Switch to "📁 Upload Image" tab
   - Upload a clear face photo
   - Enter name: "TestUser2"
   - Click "🎯 Enroll Face"
   - Verify success

3. **Test Removal:**
   - Expand "TestUser1" in sidebar
   - Click "🗑️ Remove TestUser1"
   - Verify user removed

4. **Test Error Handling:**
   - Try taking photo without name → should error
   - Upload image with no face → should fail enrollment
   - Take photo covering face → should fail

---

### 3️⃣ **Security Check Page**

**What You See:**
```
┌─────────────────────────────────────────────────┐
│ 🔍 Security Check                                │
├─────────────────────────────────────────────────┤
│                                                  │
│ Manually trigger a security check to see who is │
│ in front of the camera right now.               │
│                                                  │
│         [🔍 Run Security Check]                  │
│                                                  │
│ ─────────────────────────────────────────────   │
│                                                  │
│ ### 🎯 Check Results                            │
│                                                  │
│ ✅ AUTHORIZED ACCESS                            │
│ • Detected faces: 1                             │
│ • Authorized: shivadeepak                       │
│ • Unknown faces: 0                              │
│ • Timestamp: 2024-11-10 14:30:22                │
│                                                  │
│ [Captured Image Preview]                        │
│                                                  │
└─────────────────────────────────────────────────┘
```

**What Happens When You Click:**

1. **"🔍 Run Security Check" Button** →
   - Shows spinner: "Performing security check..."
   - Camera captures frame
   - OpenCV detects faces in frame
   - DeepFace generates encodings for each face
   - Compares against `authorized.json`
   - Calculates Euclidean distances
   - Matches if distance < 0.6 tolerance

**Possible Results:**

#### ✅ **Authorized Access (Green)**
```
✅ AUTHORIZED ACCESS
• Detected faces: 1
• Authorized: shivadeepak
• Unknown faces: 0
```
**What Happened:**
- Found 1+ faces
- All faces matched authorized users
- No enforcement actions triggered
- Logged to `alerts.jsonl` as "authorized_access"

#### ⚠️ **Unauthorized Access (Red)**
```
⚠️ UNAUTHORIZED ACCESS!
• Detected faces: 2
• Authorized: shivadeepak
• Unknown faces: 1 ⚠️
```
**What Happened:**
- Found 2 faces
- 1 matched, 1 didn't match anyone
- **Enforcement actions triggered:**
  1. ✅ Played alarm sound (if enabled)
  2. 🔒 Locked screen immediately (if enabled)
  3. 💤 Put computer to sleep (if enabled)
  4. 📧 Sent alerts to all configured channels
- Logged to `alerts.jsonl` as "unauthorized_access"
- Snapshot saved to `logs/security/snapshots/`

#### ℹ️ **No Faces Detected**
```
ℹ️ No faces detected in camera view
```
**What Happened:**
- Camera working, but no faces visible
- No actions taken
- Not logged as alert

#### ❌ **Error**
```
❌ Security check failed: [error message]
```
**What Happened:**
- Camera initialization failed
- DeepFace encoding error
- File system error
- Check logs for details

**Expected Behavior:**
- Takes 2-5 seconds to complete check
- Shows captured image after check
- Results stay on screen until next check
- Can run check repeatedly
- Each check is independent

**Testing Steps:**
1. **Test Authorized Access:**
   - Ensure you're enrolled
   - Look at camera
   - Click "Run Security Check"
   - Should see green "AUTHORIZED ACCESS"
   - Your name should appear in results

2. **Test Unauthorized Access:**
   - Have someone not enrolled look at camera
   - OR show a photo of different person
   - Click "Run Security Check"
   - Should see red "UNAUTHORIZED ACCESS!"
   - **Expected enforcement (if enabled):**
     - Hear alarm beeps
     - Screen locks immediately
     - Email/Discord alerts sent

3. **Test No Face:**
   - Point camera at wall/empty space
   - Click "Run Security Check"
   - Should see "No faces detected"

4. **Test Multiple Faces:**
   - Have 2+ people in camera view
   - Mix authorized + unauthorized
   - Should detect both, flag unknown faces

---

### 4️⃣ **Settings Page**

**What You See:**
```
┌─────────────────────────────────────────────────┐
│ ⚙️ Settings                                      │
├─────────────────────────────────────────────────┤
│                                                  │
│ ### 🔧 Monitoring Parameters                    │
│ Security Check Interval: [5] seconds            │
│ Recognition Tolerance: [0.6] (0.0-1.0)          │
│ Camera Index: [0]                               │
│ Alert Cooldown: [300] seconds                   │
│ [💾 Save Monitoring Settings]                   │
│                                                  │
│ ─────────────────────────────────────────────   │
│                                                  │
│ ### 🔐 Intruder Action Settings                 │
│ ☑ Auto-lock screen on intruder                  │
│ ☐ Auto-sleep computer on intruder               │
│ ☑ Play alarm sound on intruder                  │
│ [💾 Save Action Settings]                       │
│                                                  │
│ ─────────────────────────────────────────────   │
│                                                  │
│ ### 📢 Alert Configuration                      │
│ ┌─────────────┬──────────┬────────┐            │
│ │ Active Alert│ Discord  │ Email  │            │
│ │ Channels: 2 │🟢 Active │🟢 Active│            │
│ └─────────────┴──────────┴────────┘            │
│                                                  │
│ ▼ 💜 Discord Webhook                            │
│   [Webhook URL: **********************]         │
│   ☑ Enable Discord Alerts                       │
│   [💾 Save Config] [🧪 Test Alert]              │
│                                                  │
│ ▼ ✉️ Email (SMTP)                               │
│   Server: [smtp.gmail.com]  Port: [587]         │
│   Username: [your@email.com]                    │
│   Password: [********]                          │
│   Recipient: [alerts@email.com]                 │
│   ☑ Enable Email Alerts                         │
│   [💾 Save Config] [🧪 Test Alert]              │
│                                                  │
│ ▼ 💬 Telegram Bot                               │
│   Bot Token: [********]                         │
│   Chat ID: [123456789]                          │
│   ☑ Enable Telegram Alerts                      │
│   [💾 Save Config]                              │
│                                                  │
│ ▼ 🖥️ Desktop & System Alerts                    │
│   ☑ Windows Toast Notifications                 │
│   ☑ Sound Alerts                                │
│   ☑ Log Alerts to File                          │
│   [💾 Save System Config]                       │
│                                                  │
│ ▼ 📋 View Alert Configuration Summary           │
│   [Full text summary of all settings]           │
│   [⬇️ Download Configuration as JSON]           │
│                                                  │
│ ─────────────────────────────────────────────   │
│                                                  │
│ ### 🤖 Background Daemon                        │
│ ✅ Daemon Status: RUNNING (PID: 35716)          │
│ [▶️ Start] [⏹️ Stop] [🔄 Restart]                │
│                                                  │
└─────────────────────────────────────────────────┘
```

**What Happens When You Click:**

#### **Monitoring Parameters Section:**

1. **Security Check Interval** (default: 5s)
   - How often daemon checks for faces
   - Range: 1-300 seconds
   - Lower = more frequent checks, higher CPU usage

2. **Recognition Tolerance** (default: 0.6)
   - Sensitivity of face matching
   - 0.0 = exact match only (strict)
   - 1.0 = very loose matching
   - Recommended: 0.5-0.7

3. **Camera Index** (default: 0)
   - Which webcam to use
   - 0 = first camera
   - 1 = second camera (if multiple)

4. **Alert Cooldown** (default: 300s = 5min)
   - Minimum time between repeat alerts
   - Prevents spam if intruder stays in view

**"💾 Save Monitoring Settings"** →
- Updates `config.yaml`
- Success: "✅ Settings saved!"
- Info: "💡 Restart daemon to apply changes"
- Debug print in terminal

#### **Intruder Action Settings Section:**

**Checkboxes:**
- ☑ **Auto-lock screen** → Locks Windows on unauthorized face
- ☐ **Auto-sleep** → Sleeps computer (NUCLEAR OPTION)
- ☑ **Play alarm** → Beeps loudly (1000Hz→2000Hz)

**"💾 Save Action Settings"** →
- Updates `config.yaml` security section
- Updates live `SecurityManager` instance
- Success message
- Debug prints:
  ```
  🔍 DEBUG: Saving Actions - Lock=True, Sleep=False, Alarm=True
  ✅ DEBUG: Action config saved successfully!
  🔄 DEBUG: Updated SecurityManager config
  ```

#### **Alert Configuration Section:**

**Status Metrics (Top):**
- Shows how many channels are active
- Green 🟢 = enabled, White ⚪ = disabled

**💜 Discord Webhook:**

1. **Webhook URL Input** → Paste Discord webhook URL
2. **Enable Checkbox** → Toggle on/off
3. **"💾 Save Discord Config"** →
   - Saves to `config.yaml`
   - Updates `AlertNotifier` config
   - Also saves to `config/alert_settings_summary.json`
   - Debug prints:
     ```
     🔍 DEBUG: Saving Discord - Enabled=True, URL=SET
     ✅ DEBUG: Discord config saved successfully!
     🔄 DEBUG: Updated SecurityManager notifier config
     ```

4. **"🧪 Test Discord Alert"** →
   - Sends test webhook to Discord
   - Green embed: "🧪 Test Alert - Senthium AI"
   - Success: "✅ Test alert sent to Discord!"
   - Failure: Shows HTTP error code
   - Debug prints:
     ```
     🧪 DEBUG: Testing Discord webhook...
     ✅ DEBUG: Discord test alert sent successfully!
     ```

**✉️ Email (SMTP):**

1. **Server/Port** → SMTP server details
   - Gmail: `smtp.gmail.com:587`
   - Outlook: `smtp-mail.outlook.com:587`

2. **Username** → Your email address

3. **Password** → App-specific password (NOT your regular password!)
   - Gmail: Generate at https://myaccount.google.com/apppasswords

4. **Recipient** → Where to send alerts

5. **"💾 Save Email Config"** →
   - Saves all SMTP settings
   - Debug prints all fields

6. **"🧪 Test Email Alert"** →
   - Connects to SMTP server
   - Sends actual test email
   - Success: "✅ Test email sent to {recipient}!"
   - Failure: Shows connection error
   - Debug prints:
     ```
     🧪 DEBUG: Testing Email SMTP connection...
     🔗 DEBUG: Connecting to smtp.gmail.com:587...
     🔐 DEBUG: Logging in as your@email.com...
     📧 DEBUG: Sending test email to alerts@email.com...
     ✅ DEBUG: Email test sent successfully!
     ```

**💬 Telegram Bot:**

1. **Bot Token** → From @BotFather
2. **Chat ID** → Your Telegram chat ID
3. **"💾 Save Telegram Config"** → Saves settings

**🖥️ Desktop Alerts:**

1. **Toast Notifications** → Windows 10/11 popups
2. **Sound Alerts** → System beep
3. **Log to File** → Save to `logs/security/alerts.jsonl`
4. **"💾 Save System Config"** → Saves preferences

**📋 Configuration Summary:**

**"View Alert Configuration Summary" Expander** →
- Shows pretty text summary:
  ```
  ==================================================
  📢 ALERT CONFIGURATION SUMMARY
  ==================================================
  Generated: 2024-11-10T14:30:22
  Version: 0.6
  
  🔔 Active Alert Channels:
    ✅ Discord
    ✅ Email
    ✅ Desktop Notifications
  
  📊 Detailed Channel Status:
  
  💜 Discord: ✅ ENABLED
     Webhook configured: Yes
  
  ✉️ Email: ✅ ENABLED
     Server: smtp.gmail.com:587
     From: your@email.com
     To: alerts@email.com
  ```

**"⬇️ Download Configuration as JSON"** →
- Downloads timestamped JSON file
- Filename: `senthium_alert_config_20241110_143022.json`
- Contains full configuration snapshot

#### **Daemon Control Section:**

**Status Indicators:**
- 🟢 **RUNNING (PID: 35716)** → Daemon active
- ⚠️ **NOT RUNNING** → Daemon stopped

**Buttons:**

1. **"▶️ Start Daemon"** →
   - Launches background process
   - Takes 3-5 seconds
   - Success: "✅ Daemon started (PID: 12345)"
   - Failure: Error message + suggestion to run foreground
   - Creates PID file: `logs/daemon/senthium.pid`

2. **"⏹️ Stop Daemon"** →
   - Sends SIGTERM signal
   - Waits for graceful shutdown (10s timeout)
   - Success: "✅ Daemon stopped"
   - Clears PID file

3. **"🔄 Restart Daemon"** →
   - Stops → Waits 1s → Starts
   - Useful after changing settings

**Expected Behavior:**
- All settings persist across restarts
- Daemon must be restarted to pick up config changes
- Test buttons work immediately (no restart needed)
- Debug prints visible in terminal where Streamlit runs

**Testing Steps:**

1. **Test Monitoring Settings:**
   - Change interval to 10s
   - Save
   - Restart daemon
   - Verify daemon checks every 10s (watch logs)

2. **Test Discord Alerts:**
   - Enter webhook URL
   - Enable Discord
   - Save
   - Click "🧪 Test Alert"
   - Check Discord channel for test message
   - Verify terminal shows debug prints

3. **Test Email Alerts:**
   - Enter SMTP settings
   - Enable email
   - Save
   - Click "🧪 Test Alert"
   - Check inbox for test email
   - Verify terminal shows connection steps

4. **Test Intruder Actions:**
   - Enable "Auto-lock screen"
   - Enable "Play alarm"
   - Save
   - Go to Security Check page
   - Trigger unauthorized access
   - **Expected:** Hear alarm → Screen locks

5. **Test Daemon Control:**
   - Click "Start Daemon"
   - Wait for success message
   - Check status shows RUNNING
   - Click "Stop Daemon"
   - Verify status shows NOT RUNNING

---

## 🎯 Expected Behaviors

### When Daemon is Running

**Every 5-10 seconds (based on interval):**
1. Camera LED blinks briefly
2. Daemon captures frame
3. Detects faces
4. Compares to authorized users
5. Logs result

**If Authorized User Detected:**
- ✅ No action taken
- 📝 Logged as "authorized_access"
- 💾 Snapshot saved (optional)

**If Unauthorized User Detected:**
1. 🚨 **IMMEDIATE RESPONSE:**
   - Alarm sound plays (if enabled)
   - Screen locks (if enabled)
   - Computer sleeps (if enabled)

2. 📧 **ALERTS SENT TO:**
   - Discord webhook (if configured)
   - Email (if configured)
   - Telegram (if configured)
   - Desktop notification (if enabled)
   - File log (always)

3. 📸 **EVIDENCE SAVED:**
   - Snapshot: `logs/security/snapshots/alert_YYYYMMDD_HHMMSS.jpg`
   - Alert JSON: `logs/security/alerts.jsonl`

4. ⏱️ **COOLDOWN:**
   - Won't send another alert for 5 minutes (configurable)
   - Prevents spam if intruder stays

### File System Changes

**When Face Enrolled:**
- Creates/updates: `config/faces/authorized.json`
- Structure:
  ```json
  {
    "shivadeepak": [
      [0.123, -0.456, 0.789, ...],  // 128 numbers
      [0.234, -0.567, 0.890, ...]   // Another encoding
    ],
    "alice": [
      [0.345, -0.678, 0.901, ...]
    ]
  }
  ```

**When Alert Triggered:**
- Appends to: `logs/security/alerts.jsonl`
- Creates: `logs/security/snapshots/alert_YYYYMMDD_HHMMSS.jpg`

**When Settings Saved:**
- Updates: `config/config.yaml`
- Creates: `config/alert_settings_summary.json`

### Terminal Output (Debug Prints)

**When Streamlit App Runs:**
```
🔍 DEBUG: Saving Discord - Enabled=True, URL=SET
✅ DEBUG: Discord config saved successfully!
🔄 DEBUG: Updated SecurityManager notifier config

🧪 DEBUG: Testing Email SMTP connection...
🔗 DEBUG: Connecting to smtp.gmail.com:587...
🔐 DEBUG: Logging in as demonsaint.official@gmail.com...
📧 DEBUG: Sending test email to shivadeepak.dev@gmail.com...
✅ DEBUG: Email test sent successfully!
```

**When Daemon Runs:**
```
[DEBUG] Loop iteration 1
[DEBUG] _running=True, _shutdown_requested=False
✅ Authorized user recognized: 1 face(s)
⚠️ SECURITY ALERT! 1 unauthorized face(s) detected!
```

---

## ✅ Testing Checklist

### Phase 1: Basic Setup
- [ ] Streamlit app starts without errors
- [ ] Dashboard loads and shows empty state
- [ ] All 4 pages accessible (Dashboard, Enrollment, Security Check, Settings)
- [ ] No console errors in terminal

### Phase 2: Face Enrollment
- [ ] Webcam capture works - LED blinks, preview appears
- [ ] Can enroll user via webcam
- [ ] Can enroll user via file upload
- [ ] User appears in "Enrolled Users" sidebar
- [ ] Can remove enrolled user
- [ ] Enrollment fails gracefully if no face detected
- [ ] `authorized.json` file created/updated

### Phase 3: Security Check (Manual)
- [ ] Authorized user → Green "AUTHORIZED ACCESS" result
- [ ] Unauthorized person → Red "UNAUTHORIZED ACCESS!" result
- [ ] No face → "No faces detected" message
- [ ] Image preview appears after check
- [ ] Results stay visible until next check

### Phase 4: Enforcement Actions
- [ ] Enable "Auto-lock screen" in Settings
- [ ] Enable "Play alarm" in Settings
- [ ] Save settings
- [ ] Trigger unauthorized access
- [ ] **Expected:** Hear alarm beeps → Screen locks immediately
- [ ] Unlock screen, verify system still running

### Phase 5: Alert Channels

#### Discord:
- [ ] Create Discord webhook
- [ ] Enter webhook URL in Settings
- [ ] Enable Discord alerts
- [ ] Save config
- [ ] Click "🧪 Test Alert"
- [ ] Verify test message appears in Discord
- [ ] Terminal shows debug prints

#### Email:
- [ ] Enter SMTP settings (Gmail/Outlook)
- [ ] Use app-specific password
- [ ] Enable email alerts
- [ ] Save config
- [ ] Click "🧪 Test Alert"
- [ ] Verify test email received
- [ ] Terminal shows connection steps

#### Desktop Notifications:
- [ ] Enable "Windows Toast Notifications"
- [ ] Save config
- [ ] Trigger alert
- [ ] Verify Windows notification appears

### Phase 6: Daemon Operations
- [ ] Click "▶️ Start Daemon"
- [ ] Verify status shows "RUNNING (PID: xxxxx)"
- [ ] Wait 10 seconds, camera should blink
- [ ] Check `logs/security/alerts.jsonl` for new entries
- [ ] Trigger unauthorized access
- [ ] Verify alerts sent automatically
- [ ] Click "⏹️ Stop Daemon"
- [ ] Verify status shows "NOT RUNNING"

### Phase 7: Settings Persistence
- [ ] Change monitoring interval to 10s
- [ ] Save settings
- [ ] Close Streamlit app
- [ ] Reopen app
- [ ] Verify settings preserved

### Phase 8: Configuration Summary
- [ ] Open "View Alert Configuration Summary"
- [ ] Verify summary shows correct channel states
- [ ] Download JSON configuration
- [ ] Verify JSON contains all settings

### Phase 9: Error Handling
- [ ] Try enrolling without name → Should error
- [ ] Try enrolling image with no face → Should fail gracefully
- [ ] Disconnect camera, run security check → Should error clearly
- [ ] Enter invalid Discord webhook → Test should fail with error
- [ ] Enter wrong email password → Test should fail with error

### Phase 10: Performance
- [ ] App responsive (no lag when clicking buttons)
- [ ] Security check completes in < 5 seconds
- [ ] Daemon uses < 5% CPU when idle
- [ ] No memory leaks (check Task Manager over 30 min)

---

## 🐛 Troubleshooting

### Issue: "Daemon failed to start"

**Symptoms:**
```
[ERROR] Daemon failed to start
        The process may have crashed during initialization
```

**Causes:**
- PID file already exists from crashed daemon
- Camera in use by another app
- Missing dependencies

**Solutions:**
1. Check if daemon already running: `Get-Process | Select-String python`
2. Delete stale PID file: `Remove-Item logs/daemon/senthium.pid`
3. Close other camera apps (Zoom, Teams, etc.)
4. Check camera works: `.\venv311\Scripts\python.exe -c "import cv2; cv2.VideoCapture(0).read()"`

### Issue: "No faces detected"

**Symptoms:**
Security check always returns "No faces detected"

**Causes:**
- Poor lighting
- Face not centered
- Camera angle too extreme
- Face too far from camera

**Solutions:**
1. Improve lighting (face camera toward light)
2. Center face in camera view
3. Move closer to camera (1-3 feet optimal)
4. Face camera straight on

### Issue: "Enrollment failed"

**Symptoms:**
"❌ Enrollment failed - check logs for details"

**Causes:**
- No face in image
- Face too blurry
- Multiple faces (conflicting)
- Image too small

**Solutions:**
1. Use clear, well-lit photo
2. Ensure only one face visible
3. Image should be at least 200x200 pixels
4. Face should be front-facing

### Issue: Test email fails

**Symptoms:**
"❌ Error: Authentication failed"

**Causes:**
- Using regular password instead of app-specific password
- 2FA not enabled on Gmail
- Wrong SMTP server

**Solutions:**
1. **Gmail:** Generate app password at https://myaccount.google.com/apppasswords
2. Enable 2FA first (required for app passwords)
3. Use correct SMTP:
   - Gmail: `smtp.gmail.com:587`
   - Outlook: `smtp-mail.outlook.com:587`

### Issue: Screen doesn't lock

**Symptoms:**
Unauthorized access detected but screen doesn't lock

**Causes:**
- "Auto-lock screen" disabled in Settings
- Windows permissions issue

**Solutions:**
1. Check Settings → Intruder Actions → "Auto-lock screen" is checked
2. Save settings
3. Run Streamlit as Administrator (right-click → Run as admin)

### Issue: Camera permission denied

**Symptoms:**
"❌ Failed to capture image from webcam"

**Causes:**
- Camera blocked by Windows privacy settings
- Camera in use by another app
- Driver issue

**Solutions:**
1. **Windows Settings** → Privacy → Camera → Allow apps to access camera
2. Close Zoom/Teams/OBS
3. Restart camera: Unplug/replug USB

---

## 📊 Success Criteria

**You know the system is working when:**

✅ **Basic Flow:**
1. Enroll your face via webcam
2. Run security check → See "AUTHORIZED ACCESS"
3. Have friend stand in front of camera
4. Run security check → See "UNAUTHORIZED ACCESS!"
5. Screen locks immediately
6. Dashboard shows alert card

✅ **Daemon Flow:**
1. Start daemon
2. Walk away from computer
3. Someone else approaches
4. Alert sent to Discord/Email
5. Screen locks automatically
6. Check Dashboard - see alert with timestamp

✅ **Full Integration:**
1. All 4 alert channels configured
2. Daemon running 24/7
3. Unauthorized access triggers:
   - Alarm sound ✓
   - Screen lock ✓
   - Discord message ✓
   - Email ✓
   - Desktop notification ✓
   - File log ✓
4. Can review all alerts in Dashboard
5. Can download alert snapshots

---

## 🎓 Advanced Usage

### Multiple Enrollments for Better Accuracy

**Why:** Enroll same person 3-5 times in different conditions
- Different lighting
- Different angles
- With/without glasses
- Different expressions

**How:**
1. Enroll "Alice" with webcam (front-facing)
2. Enroll "Alice" again (side angle)
3. Enroll "Alice" again (different lighting)
4. System now has 3 encodings for Alice
5. Recognition more reliable

### Tuning Recognition Tolerance

**Too many false positives** (strangers recognized as you):
- **Decrease tolerance:** 0.6 → 0.5 → 0.4
- Stricter matching

**Too many false negatives** (you not recognized):
- **Increase tolerance:** 0.6 → 0.7 → 0.8
- Looser matching

### Alert Cooldown Strategy

**High security environment:**
- Cooldown: 60 seconds (1 minute)
- More frequent alerts

**Normal use:**
- Cooldown: 300 seconds (5 minutes)
- Balance between security and spam

### Daemon Auto-Start (Windows)

**Create scheduled task:**
1. Task Scheduler → Create Basic Task
2. Trigger: At log on
3. Action: Start program
4. Program: `E:\GPls\senthium-ai-modern\venv311\Scripts\streamlit.exe`
5. Arguments: `run E:\GPls\senthium-ai-modern\streamlit_app.py`
6. Done! App starts on Windows login

---

## 📝 Notes for Developers

### Key Files
- `streamlit_app.py` - Main GUI (946 lines)
- `src/vision/security_manager.py` - AI security orchestrator
- `src/vision/face_recognizer.py` - DeepFace integration
- `src/alerts/notifier.py` - Multi-channel alerts
- `src/actions/system_actions.py` - Lock/sleep/alarm
- `config/config.yaml` - All settings
- `config/faces/authorized.json` - Facial encodings

### Debug Mode
Run with full debug output:
```powershell
$env:SENTHIUM_DEBUG = "1"
.\venv311\Scripts\streamlit.exe run streamlit_app.py
```

### Testing Without Camera
Use static image instead:
```python
# In security_manager.py, replace camera.capture_frame() with:
frame = cv2.imread("test_face.jpg")
```

---

**Last Updated:** November 10, 2025  
**Version:** 0.6.0  
**Status:** ✅ All features implemented and tested
