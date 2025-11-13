# 📜 Live Logs Feature - Real-Time Daemon Monitoring

## What's New? ✨

Added a **Live Logs** tab to the GUI so you can see exactly what the daemon is doing in real-time! No more guessing if it's working!

## How to Use 🚀

### 1. **Start the Daemon**
- Go to **📊 Dashboard** tab
- Click **"🟢 Start Daemon"** button
- Wait for status to show "🟢 Running"

### 2. **View Live Logs**
- Click **📜 Live Logs** in the sidebar
- Check the **"🔄 Auto-refresh"** checkbox (enabled by default)
- Logs will update every 3 seconds automatically!

### 3. **What You'll See**

#### 📑 **Four Log Tabs:**

**1. 🔍 Security Checks**
- Face detection events
- Recognition results (authorized/unknown)
- Intruder alerts
- Snapshot creation logs

**Example:**
```
2025-11-13 14:30:45 [DEBUG] 🔍 Performing security check...
2025-11-13 14:30:45 [DEBUG] 👥 Detected 1 face(s)
2025-11-13 14:30:45 [DEBUG] ✅ Recognized: YourName (0.42)
2025-11-13 14:30:50 [WARNING] ❌ Unknown face detected!
2025-11-13 14:30:50 [WARNING] 🚨 Saving snapshot - 1 intruder(s) detected!
```

**2. 📊 Daemon Activity**
- Daemon start/stop events
- System initialization
- Poll cycles
- Configuration changes

**Example:**
```
2025-11-13 14:25:00 [INFO] 🚀 Senthium Daemon starting...
2025-11-13 14:25:01 [INFO] 📸 Camera monitor initialized
2025-11-13 14:25:01 [INFO] 🔐 Security Manager initialized
2025-11-13 14:25:01 [INFO] ✅ Daemon started successfully (PID: 12345)
```

**3. 🚨 Alerts & Events**
- Warnings
- Errors
- Critical security events
- System lock events

**Example:**
```
2025-11-13 14:30:50 [WARNING] 🚨 INTRUDER DETECTED! Locking system in 3 seconds...
2025-11-13 14:30:53 [INFO] 🔒 System locked due to unauthorized access
2025-11-13 14:31:20 [ERROR] ❌ Camera capture failed
```

**4. 📸 Snapshot History**
- Visual gallery of all snapshots
- Intruder vs Security snapshot counts
- File size and timestamp info
- Delete individual snapshots

## Features 🎯

### ✅ **Real-Time Updates**
- Auto-refreshes every 3 seconds when enabled
- Toggle on/off with checkbox
- See daemon activity as it happens

### ✅ **Smart Filtering**
- Each tab shows only relevant logs
- No clutter - easy to read
- Most recent entries shown first

### ✅ **Status Indicators**
- **Daemon Status:** 🟢 Running / 🔴 Stopped
- **Security Status:** 🔐 ACTIVE / ⏸️ PAUSED
- **PID Display:** Shows process ID when running

### ✅ **Snapshot Management**
- View all snapshots in gallery
- See which are intruders vs old security snapshots
- Delete unwanted snapshots with one click
- File info (size, timestamp)

## How to Know if Daemon is Working 🔍

### ✅ **Signs it's Working:**

**Dashboard:**
- Status shows "🟢 Running" with PID number
- "Daemon Status" metric is green

**Live Logs Tab:**
- Security Checks shows recent detections
- Daemon Activity shows poll cycles
- Timestamps are recent (within last few seconds)

**Expected Behavior:**
```
Every 5-10 seconds you should see:
🔍 Performing security check...
👥 Detected N face(s)
✅ Recognized: YourName (confidence)
```

### ❌ **Signs it's NOT Working:**

**Dashboard:**
- Status shows "🔴 Stopped"
- No PID displayed

**Live Logs Tab:**
- No recent logs (timestamps old)
- Security Checks tab empty
- "Log file not found" error

**What to do:**
1. Click "🟢 Start Daemon" in Dashboard
2. Wait 5 seconds
3. Check Live Logs - should see initialization logs
4. If still not working, check "🚨 Alerts & Events" tab for errors

## Testing the Snapshot Fix 🧪

### Test 1: Authorized User (You)
1. Start daemon from Dashboard
2. Go to Live Logs → Security Checks tab
3. Sit in front of camera for 30 seconds
4. **Expected:** See "✅ Recognized: YourName" logs
5. Go to Snapshot History tab
6. **Expected:** NO new snapshots created! ✅

### Test 2: Intruder Detection
1. Show unknown face to camera (friend/photo)
2. Watch Security Checks tab
3. **Expected:** See "🚨 Saving snapshot - 1 intruder(s) detected!"
4. Go to Snapshot History tab
5. **Expected:** ONE new `intruder_[timestamp].jpg` file! ✅
6. Check Alerts & Events tab
7. **Expected:** See "🚨 INTRUDER DETECTED! Locking system..."

### Test 3: Snapshot Cleanup
1. After 100+ intruder snapshots created
2. Check Snapshot History tab
3. **Expected:** Max 100 files shown
4. **Expected:** See log "🗑️ Cleaned up N old snapshots"

## Performance 📊

**Auto-Refresh Impact:**
- Reads log file every 3 seconds (minimal CPU)
- Shows last 30-100 lines (fast)
- No impact on daemon performance

**If experiencing lag:**
- Disable auto-refresh checkbox
- Manually refresh by clicking tab again
- Close Snapshot History images (most resource-intensive)

## Troubleshooting 🔧

### Issue: "Log file not found"
**Solution:** Start the daemon first. Logs are only created when daemon is running.

### Issue: Logs not updating
**Solution:** 
1. Check auto-refresh is enabled
2. Check daemon status (should be 🟢 Running)
3. Try manual refresh by switching tabs

### Issue: Too many old "security_*.jpg" snapshots
**Solution:** 
These are from BEFORE the fix. They're safe to delete:
1. Go to Snapshot History tab
2. Delete old security snapshots manually
3. Or run: `Remove-Item logs/security/snapshots/security_*.jpg`

### Issue: No security check logs appearing
**Solution:**
1. Check Dashboard - is security enabled? (should be 🔐 ACTIVE)
2. Check Settings - is "Enable Security" toggled on?
3. Restart daemon after enabling security

## Benefits 💪

**Before (Without Live Logs):**
- ❌ No idea if daemon is working
- ❌ Have to manually check log files
- ❌ Can't see real-time activity
- ❌ Blind troubleshooting

**After (With Live Logs):**
- ✅ See daemon activity in real-time
- ✅ Know immediately if security checks are running
- ✅ Watch intruder detection happen live
- ✅ Easy debugging with filtered logs
- ✅ Visual snapshot gallery
- ✅ Confidence that system is working!

## Quick Reference 📋

| Tab | What It Shows | Use Case |
|-----|--------------|----------|
| 🔍 Security Checks | Face detection, recognition | Verify security is working |
| 📊 Daemon Activity | System events, polls | Debug daemon issues |
| 🚨 Alerts & Events | Errors, warnings | Troubleshoot problems |
| 📸 Snapshot History | Saved images | Review intruders, cleanup |

## Tips & Tricks 💡

**1. Keep Auto-Refresh On**
- Best for monitoring in real-time
- See threats as they happen
- Know system is alive

**2. Check Alerts Tab First**
- If something seems wrong
- Shows errors and warnings
- Faster troubleshooting

**3. Use Snapshot History**
- Review who triggered alerts
- Delete false positives
- See if cleanup is working

**4. Monitor Security Checks**
- Verify YOU are being recognized (not intruder)
- Check recognition confidence (should be < 0.6)
- Ensure checks happening every 5-10 seconds

---

**Status:** ✅ Fully implemented and tested  
**Last Updated:** 2025-11-13  
**Impact:** HIGH - Essential for monitoring and debugging

Now you can SEE your daemon working in real-time! 🚀💕
