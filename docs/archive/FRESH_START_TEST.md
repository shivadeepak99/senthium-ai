# 🆕 FRESH START - Clean Testing Protocol

## ✅ Step 1: Logs Cleaned
- ✅ Old logs backed up to: `logs_backup_20251113_193523/`
- ✅ Fresh `logs/` folder created
- ✅ Fresh `logs/security/snapshots/` folder created
- ✅ Clean slate for debugging!

---

## 🧪 Step 2: Test Protocol (Do in Order!)

### Test A: Enroll Yourself FIRST ⚠️
**This is CRITICAL! System needs to know who you are!**

1. Open GUI: http://localhost:8501
2. Go to **"🎓 AI Training"** tab
3. Click **"Start Recording"**
4. Look at camera for 60 seconds (move head around)
5. Click **"Stop & Save Training"**
6. Enter name: "Shiva" (or your name)
7. Click **"💾 Save to Database"**

**Verify enrollment:**
```powershell
# Check if face was saved
Get-Content config/faces/authorized.json

# Should show your name with encoding data, NOT empty {}
```

---

### Test B: Manual Security Check (Verify Recognition Works)

**Before starting daemon, test if recognition works:**

1. Go to **"🔍 Security Check"** tab
2. Click **"🚀 Run Security Check Now"**

**Expected Result (If Enrolled):**
```
✅ AUTHORIZED: Shiva
Total Faces: 1
Authorized: 1
Unauthorized: 0
```

**If You See This Instead:**
```
⚠️ Unauthorized: 1
🚨 SECURITY ALERT!
```
= Enrollment didn't work or tolerance too low! Try enrolling again!

---

### Test C: Start Daemon (Fresh Logs!)

1. Go to **"📊 Dashboard"** tab
2. Click **"🟢 Start Daemon"** button
3. Wait 5 seconds
4. Should show: **"🟢 Running (PID: XXXX)"**

**Verify daemon started:**
```powershell
# Check logs (should be fresh!)
Get-Content logs/senthium.log -Tail 20

# Should see:
# [INFO] 🚀 Senthium Daemon starting...
# [INFO] ✅ AI Security enabled
# [INFO] 📸 Camera initialized
```

---

### Test D: Watch Live Activity (Real-Time!)

1. Go to **"📜 Live Logs"** tab
2. Enable **"🔄 Auto-refresh"** checkbox
3. Click **"🔍 Security Checks"** tab
4. Wait 10-15 seconds

**Expected (If Enrolled Correctly):**
```
[DEBUG] 🔍 Performing security check...
[DEBUG] 👥 Detected 1 face(s)
[DEBUG] ✅ Recognized: Shiva (0.42)
[INFO] 🟢 AUTHORIZED: Shiva
```
*This should appear every 5-10 seconds!*

**If You See This Instead:**
```
[WARNING] ❌ Unknown face detected!
[WARNING] 🚨 Saving snapshot - 1 intruder(s) detected!
```
= **YOU'RE NOT ENROLLED!** Stop daemon, go back to Test A!

---

### Test E: Intruder Detection (After Enrollment!)

**Only do this AFTER you see "✅ Recognized: YourName" in logs!**

1. Keep Live Logs → Security Checks tab open
2. Show unknown face to camera (friend, photo, phone)
3. Watch the logs in real-time!

**Expected Behavior:**
```
[WARNING] ❌ Unknown face detected!
[WARNING] 🚨 Saving snapshot - 1 intruder(s) detected!
[WARNING] ⏱️ TIER 1: Intruder detected, waiting 3s before locking...
[CRITICAL] 🔒 TIER 2: Lock delay exceeded - LOCKING NOW!
[WARNING] 🔒 LOCKING SCREEN TO BLOCK INTRUDER!
```

**Then:**
- 🔒 **Screen LOCKS** (after 3 seconds)
- 📸 **Snapshot saved**: Check Live Logs → Snapshot History tab
- 📧 **Email sent**: Check inbox at `shivadeepak.dev@gmail.com`
- 🔔 **Desktop notification**: Should pop up

---

## 🔍 Debugging Guide

### Issue: "No logs in Live Logs tab"
**Check:**
```powershell
# Is daemon running?
Get-Content daemon.pid

# Is log file being created?
Test-Path logs/senthium.log

# View raw logs
Get-Content logs/senthium.log -Tail 20
```

**Solution:**
- Daemon not running → Start from Dashboard
- No log file → Check permissions, restart daemon

---

### Issue: "System detecting me as intruder"
**Check:**
```powershell
# Are you enrolled?
Get-Content config/faces/authorized.json

# Should NOT be empty {}
```

**Solution:**
- Empty file → Not enrolled! Do Test A!
- Has data but still intruder → Tolerance too low or poor training
- Try enrolling again with better lighting

---

### Issue: "No actions taken on intruder"
**Check:**
```powershell
# Check if actions are configured
Get-Content config/config.yaml | Select-String "auto_lock|auto_sleep|play_alarm"

# Check alert log
Get-Content logs/security/alerts.jsonl -Tail 5
```

**Possible Reasons:**
1. **Critical app running** (python.exe, obs64.exe, etc.)
   - Check logs for: "INTRUDER DETECTED (but XXX is running)"
   - System suppresses lock to protect your work
   
2. **Alert cooldown** (5 minutes between alerts)
   - Check last alert timestamp
   - Wait 5 minutes and try again
   
3. **Lock disabled in config**
   - `auto_lock_on_intruder: false`
   - Change to `true` in Settings

4. **Daemon not actually running**
   - Check PID file and process

---

### Issue: "Screen didn't lock"
**Debug:**
```powershell
# Check if lock command succeeded
Get-Content logs/senthium.log | Select-String "LOCK|lock"

# Check system actions log
Get-Content logs/senthium.log | Select-String "screen_lock|SystemActions"
```

**If you see:**
- "✅ Screen locked successfully" → It DID lock! You just unlocked quickly
- "❌ Failed to lock screen" → Permission issue or Windows security blocking
- "🎬 Screen lock suppressed" → Critical app protection active

---

## 📊 Success Indicators

**✅ System Working Correctly:**
- Live Logs shows security checks every 5-10 seconds
- Your name appears as "✅ Recognized"
- Intruder triggers lock + snapshot + alert
- Fresh logs being created in `logs/`

**❌ System NOT Working:**
- Live Logs tab empty
- Daemon status shows "🔴 Stopped"
- No new files in `logs/`
- Always detected as "Unknown"

---

## 🎯 Quick Command Reference

**Check enrollment:**
```powershell
Get-Content config/faces/authorized.json
```

**Check daemon status:**
```powershell
Get-Content daemon.pid
Get-Process -Id (Get-Content daemon.pid)
```

**View real-time logs:**
```powershell
Get-Content logs/senthium.log -Tail 20 -Wait
```

**Check security alerts:**
```powershell
Get-Content logs/security/alerts.jsonl | Select-Object -Last 5
```

**Check recent snapshots:**
```powershell
Get-ChildItem logs/security/snapshots/ | Sort-Object LastWriteTime -Descending | Select-Object -First 5
```

**Stop daemon:**
```powershell
# From GUI: Dashboard → Stop Daemon
# OR kill process:
Stop-Process -Id (Get-Content daemon.pid) -Force
```

---

## 💡 Expected Timeline

**Proper Test Sequence:**
1. **Enroll** (2 min) → File saved to `config/faces/authorized.json`
2. **Manual check** (30 sec) → Verify "✅ AUTHORIZED"
3. **Start daemon** (30 sec) → PID file created, logs start
4. **Watch logs** (1 min) → See "✅ Recognized: YourName" every 5-10s
5. **Test intruder** (30 sec) → Screen locks, snapshot saved, alert sent

**Total time: ~5 minutes to full working system!**

---

## 🚨 Common Mistakes

1. ❌ Starting daemon BEFORE enrolling
   - Result: You're detected as intruder!
   - Fix: Enroll FIRST!

2. ❌ Not waiting for auto-refresh
   - Result: Logs look empty
   - Fix: Wait 10-15 seconds for first check

3. ❌ Critical app running during test
   - Result: No lock action
   - Fix: Close Python IDEs, OBS, etc.

4. ❌ Unlocking screen immediately
   - Result: Think it didn't lock
   - Fix: Watch Live Logs to confirm lock was triggered

---

**Ready? Start with Test A (Enrollment)!** 💕✨

Let me know what you see at each step!
