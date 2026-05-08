# 📜 Complete Logging Guide - What Gets Logged Where

**All logs go to: `logs/senthium.log`** (when daemon runs with DEBUG level)

---

## 🎯 What's Being Logged Now:

### 1. 🔍 **Security Checks** (`src/vision/security_manager.py`)

**Every Security Check:**
```
[INFO] 🔍 Performing security check #X...
[DEBUG] 📸 Capturing frame from camera...
[DEBUG] ✅ Frame captured: (480, 640, 3)
[DEBUG] 🔎 Detecting and encoding faces...
```

**When Faces Detected:**
```
[INFO] 👥 Detected N face(s) - analyzing...
[DEBUG] 🧠 Recognizing face 1/N...
[INFO] ✅ Recognized: shiv (confidence: 0.47)
```

**When Authorized:**
```
[INFO] 🟢 AUTHORIZED: shiv
```

**When Intruder Detected:**
```
[WARNING] ❌ Unknown face #1 detected!
[WARNING] 🚨 INTRUDER ALERT! Saving snapshot - N unauthorized face(s)!
[INFO] 📸 Snapshot saved: logs/security/snapshots/intruder_YYYYMMDD_HHMMSS.jpg
[DEBUG] 🗑️ Cleaned up N old snapshot(s)
[WARNING] ⏱️ TIER 1: Intruder detected, waiting Xs before locking...
[CRITICAL] 🔒 TIER 2: Lock delay exceeded - LOCKING NOW!
```

**When Action Taken:**
```
[WARNING] 🔒 LOCKING SCREEN TO BLOCK INTRUDER!
[INFO] ✅ Screen locked successfully - intruder blocked!
[WARNING] 📧 ALERT SENT: Unauthorized access - system locked!
```

**When Critical App Running:**
```
[WARNING] 🎬 CRITICAL APP RUNNING: python.exe
[WARNING] ⚠️ Suppressing lock action to protect ongoing work!
[WARNING] 📧 SILENT ALERT SENT: Intruder detected, but critical app protected!
```

---

### 2. 👁️ **Face Detection** (`src/vision/detector.py`)

**Every Frame:**
```
[DEBUG] DNN detected 200 potential faces
[DEBUG] Face 0: confidence=0.9908, threshold=0.5
[DEBUG] ✅ Face accepted: box=(349, 827, 574, 621)
[DEBUG] Total faces accepted: 1
[DEBUG] 👤 Detected 1 face(s)
```

**Embedding Generation:**
```
[DEBUG] Face region (padded): (315, 288, 3), resized to: (224, 224, 3)
[DEBUG] Generated embedding: shape=(128,), first 5 values=[-0.136...]
```

---

### 3. 🧠 **Face Recognition** (`src/vision/recognizer.py`)

**Every Recognition:**
```
[DEBUG] Known encoding: shape=(128,), first 5=[-0.182...]
[DEBUG] Query encoding: shape=(128,), first 5=[-0.096...]
[DEBUG] Comparing to shivadeepak: distance=4.1880, tolerance=0.6
[DEBUG] Comparing to shiv: distance=0.3542, tolerance=0.6
[DEBUG] ✅ MATCH FOUND: shiv (distance=0.3542, confidence=0.65)
[DEBUG] ✅ Recognized: shiv (confidence: 0.65)
```

**When No Match:**
```
[DEBUG] ❌ NO MATCH: closest=shiv, distance=0.7738 > tolerance=0.6
[DEBUG] ❌ Unknown face (closest: shiv, distance: 0.77)
```

---

### 4. 🔐 **System Actions** (`src/actions/system_actions.py`)

**Screen Lock:**
```
[INFO] 🔒 Screen LOCKED! Intruder blocked!
```

**Sleep:**
```
[WARNING] 😴 PUTTING COMPUTER TO SLEEP!
[INFO] 😴 Computer put to SLEEP!
```

**Alarm:**
```
[INFO] 🔔 Alarm sound played!
```

**Shutdown:**
```
[WARNING] 🚨 SHUTDOWN initiated in 60s!
[INFO] ✅ Shutdown cancelled
```

---

### 5. 👻 **Haunting Mode** (`src/effects/haunting_mode.py`)

**Initialization:**
```
[INFO] 👻 TTS engine initialized for haunting mode
[INFO] 👻 Haunting mode initialized (enabled: True)
```

**Haunting Execution:**
```
[INFO] 👻 Haunting executed! Level: 2, Effects: ['tts_whisper', 'screen_flash']
[DEBUG] 👻 Speaking whisper (L2): "I see you..."
[DEBUG] 👻 Screen flash x3 (L2)
[DEBUG] 👻 Showing creepy message (L2): INTRUDER ALERT
```

---

### 6. 🔔 **Alerts & Notifications** (`src/alerts/notifier.py`)

**Alert Sent:**
```
[INFO] 📧 Alert sent via email
[INFO] 📱 Alert sent via Discord
[WARNING] Alert cooldown active (Xs remaining)
```

---

### 7. 🎯 **Daemon Core** (`src/daemon/core.py`)

**Daemon Startup:**
```
[INFO] 🌸 Senthium Daemon Initializing...
[INFO] ✅ AI Security enabled (face recognition active)
[INFO] 🛡️ Face recognizer initialized (tolerance: 0.6)
[DEBUG] Setting up signal handlers...
[DEBUG] Transitioning to MONITORING state...
[DEBUG] Entering main loop...
```

**Main Loop:**
```
[DEBUG] Loop iteration X
[DEBUG] About to gather metrics...
[DEBUG] Got metrics: CPU=54.8%
[DEBUG] About to check security (enabled=True)...
[DEBUG] poll_count=X, interval=1, modulo=0
[DEBUG] 🎯 RUNNING SECURITY CHECK NOW!
```

**State Transitions:**
```
[INFO] 🔥 Rules matched - transitioning to ACTIVE state
[INFO] 💤 Returning to MONITORING state (activity ended)
```

---

## 🚀 How to See ALL These Logs:

### **Option 1: GUI - Live Logs (Best!)**
1. Go to **📜 Live Logs** page
2. Enable **🔄 Auto-refresh**
3. Click **🔍 Security Checks** tab
4. Watch real-time logs!

### **Option 2: Terminal - Tail Logs**
```powershell
Get-Content logs/senthium.log -Wait -Tail 50
```

### **Option 3: Terminal - Run Daemon in Foreground**
```powershell
$env:PYTHONPATH = "E:\GPls\senthium-ai-modern"
python src/daemon/core.py --config config/config.yaml --log-level DEBUG
```
Logs appear directly in terminal in real-time!

---

## 📊 Log Levels Explained:

| Level | When Used | Example |
|-------|-----------|---------|
| **DEBUG** | Technical details | Face distances, embeddings, modulo checks |
| **INFO** | Normal operations | Recognized user, alarm played, system started |
| **WARNING** | Attention needed | Intruder detected, critical app running, lock delay |
| **ERROR** | Something failed | Camera error, lock failed, TTS failed |
| **CRITICAL** | Emergency! | Intruder lockdown, repeat offender |

---

## 🎯 What You Can Track:

✅ **Every security check** (#1, #2, #3...)  
✅ **Face detection** (how many faces, confidence scores)  
✅ **Face recognition** (distances, tolerance, match/no-match)  
✅ **Intruder detection** (who, when, actions taken)  
✅ **Screen locks** (success/failure)  
✅ **Alerts sent** (email, Discord, cooldown)  
✅ **Critical apps** (protection active)  
✅ **Snapshots saved** (path, cleanup)  
✅ **Haunting effects** (whispers, flashes, messages)  
✅ **Daemon state** (MONITORING, ACTIVE, LOCKED)  

---

## 🔧 Troubleshooting:

**No logs appearing?**
1. Check daemon is running: Dashboard → Should show "🟢 Running"
2. Check log level: Must be **DEBUG** (not INFO)
3. Restart daemon: Dashboard → **🔄 Restart**
4. Wait 10-15 seconds for first security check

**Logs too verbose?**
- Change log level to INFO in `streamlit_app.py` line 346
- Will hide DEBUG logs (embeddings, distances) but keep important stuff

**Want more logs?**
- All major operations already logged!
- If something specific missing, ask me to add it! 💕

---

**Now you have FULL VISIBILITY into everything Senthium does! 🎉🔍**
