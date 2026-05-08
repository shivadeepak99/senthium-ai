# ✅ TESTING CHECKLIST - Follow This Order!

## Current Status:
- ✅ Old logs backed up: `logs_backup_20251113_193523/` (726 old snapshots)
- ✅ Fresh logs folder: `logs/` (0 files)
- ✅ Fresh snapshots folder: `logs/security/snapshots/` (0 files)
- ⚠️ Daemon: NOT RUNNING
- ⚠️ Enrolled faces: NEED TO CHECK

---

## 🎯 DO THESE IN ORDER:

### [ ] Step 1: Check Current Enrollment Status
```powershell
Get-Content config/faces/authorized.json
```

**Expected:**
- If empty `{}` → Need to enroll!
- If has data → Already enrolled, verify name

---

### [ ] Step 2: Enroll Yourself (If Needed)
**GUI → 🎓 AI Training**
- [ ] Click "Start Recording"
- [ ] Record 60 second video (move head around)
- [ ] Click "Stop & Save Training"
- [ ] Enter your name
- [ ] Click "💾 Save to Database"
- [ ] See your name in "Currently Trained Users"

**Verify:**
```powershell
Get-Content config/faces/authorized.json
# Should show: {"YourName": {"encoding": [...], ...}}
```

---

### [ ] Step 3: Manual Security Check (Test Recognition)
**GUI → 🔍 Security Check**
- [ ] Click "🚀 Run Security Check Now"

**Expected Result:**
```
✅ AUTHORIZED: YourName
Total Faces: 1
✅ Authorized: 1
⚠️ Unauthorized: 0
```

**If shows "Unauthorized":**
- [ ] Not enrolled properly → Go back to Step 2!
- [ ] Tolerance too low → Check config (should be 0.6)

---

### [ ] Step 4: Start Daemon
**GUI → 📊 Dashboard**
- [ ] Click "🟢 Start Daemon"
- [ ] Wait 5 seconds
- [ ] Status shows: "🟢 Running (PID: XXXX)"

**Verify:**
```powershell
# Check PID file exists
Get-Content daemon.pid

# Check logs being created
Get-Content logs/senthium.log -Tail 10
```

**Expected in logs:**
```
[INFO] 🚀 Senthium Daemon starting...
[INFO] ✅ AI Security enabled (face recognition active)
[INFO] 📸 Camera monitor initialized
[INFO] ✅ Daemon started successfully
```

---

### [ ] Step 5: Watch Live Logs (Real-Time Monitoring)
**GUI → 📜 Live Logs**
- [ ] Enable "🔄 Auto-refresh" checkbox
- [ ] Click "🔍 Security Checks" tab
- [ ] Wait 10-15 seconds

**Expected (Every 5-10 seconds):**
```
[DEBUG] 🔍 Performing security check...
[DEBUG] 👥 Detected 1 face(s)
[DEBUG] ✅ Recognized: YourName (0.42)
[INFO] 🟢 AUTHORIZED: YourName
```

**If NOT seeing logs:**
- [ ] Daemon not running → Check Step 4
- [ ] Wait longer (first check takes 10-15 sec)
- [ ] Refresh page

**If seeing "Unknown face":**
- [ ] NOT ENROLLED! → Stop daemon, go to Step 2!

---

### [ ] Step 6: Test Intruder Detection
**ONLY do this AFTER seeing "✅ Recognized: YourName" in logs!**

**Test Setup:**
- [ ] Keep Live Logs open (Security Checks tab)
- [ ] Have unknown face ready (friend/photo/phone)
- [ ] Watch logs in real-time

**Actions:**
- [ ] Show unknown face to camera
- [ ] Watch logs for intruder detection

**Expected Logs:**
```
[WARNING] ❌ Unknown face detected!
[WARNING] 🚨 Saving snapshot - 1 intruder(s) detected!
[WARNING] ⏱️ TIER 1: Intruder detected, waiting 3s before locking...
[CRITICAL] 🔒 TIER 2: Lock delay exceeded - LOCKING NOW!
[WARNING] 🔒 LOCKING SCREEN TO BLOCK INTRUDER!
```

**Expected Actions:**
- [ ] Screen LOCKS (after 3 seconds)
- [ ] Snapshot saved (check "📸 Snapshot History" tab)
- [ ] Alert sent (check "🚨 Alerts & Events" tab)
- [ ] Email received (check `shivadeepak.dev@gmail.com`)

---

### [ ] Step 7: Verify All Outputs

**Check Fresh Logs Created:**
```powershell
# Should have new log file
Get-ChildItem logs/ -Recurse -File

# Should have intruder snapshot(s)
Get-ChildItem logs/security/snapshots/

# Should have alert entries
Get-Content logs/security/alerts.jsonl
```

**Expected Files:**
- `logs/senthium.log` → Daemon activity logs
- `logs/security/snapshots/intruder_YYYYMMDD_HHMMSS.jpg` → Intruder photo(s)
- `logs/security/alerts.jsonl` → Alert records

---

## 🔍 Troubleshooting Checklist

### Issue: "Live Logs is empty"
- [ ] Check daemon status (Dashboard → should be 🟢 Running)
- [ ] Check log file exists: `Test-Path logs/senthium.log`
- [ ] Wait 10-15 seconds for first check
- [ ] Try manual refresh (switch tabs)

### Issue: "Always detected as Unknown"
- [ ] Check enrollment: `Get-Content config/faces/authorized.json`
- [ ] If empty → Not enrolled! Do Step 2!
- [ ] If has data → Poor quality training, re-enroll with better lighting
- [ ] Check tolerance: Should be 0.6 in config

### Issue: "No actions on intruder"
- [ ] Check if critical app running (python.exe, etc.)
- [ ] Check logs for "🎬 Screen lock suppressed"
- [ ] Check alert cooldown (5 min between alerts)
- [ ] Verify config: `auto_lock_on_intruder: true`

### Issue: "Screen didn't lock"
- [ ] Check logs for "✅ Screen locked successfully"
- [ ] If locked → You just unlocked it quickly!
- [ ] If "Failed to lock" → Windows security blocking
- [ ] If "suppressed" → Critical app protection active

---

## 📝 Notes Space (Fill in your results)

**Step 1 - Enrollment Status:**
```
(Paste output of authorized.json here)
```

**Step 3 - Manual Check Result:**
```
(Write: AUTHORIZED or UNAUTHORIZED)
```

**Step 5 - Live Logs Output:**
```
(Paste first security check logs here)
```

**Step 6 - Intruder Test Result:**
```
Did screen lock? YES / NO
Snapshot created? YES / NO
Alert sent? YES / NO
```

---

## 🎯 Success Criteria

**System is working if:**
- ✅ You are recognized as authorized (not unknown)
- ✅ Security checks appear in logs every 5-10 seconds
- ✅ Intruder triggers lock + snapshot + alert
- ✅ Fresh logs/snapshots being created in `logs/`

**Time to completion: ~5 minutes**

---

**START WITH STEP 1 NOW!** 🚀

Report back what you see at each step! 💕
