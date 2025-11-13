# Restart Daemon Script
# Stops old daemon and starts new one with updated code

Write-Host "🔄 Restarting Senthium Daemon with snapshot fix..." -ForegroundColor Cyan

# Stop existing daemon
Write-Host "`n1️⃣ Stopping existing daemon..." -ForegroundColor Yellow
$oldPid = Get-Content "daemon.pid" -ErrorAction SilentlyContinue
if ($oldPid) {
    try {
        Stop-Process -Id $oldPid -Force -ErrorAction SilentlyContinue
        Write-Host "✅ Stopped daemon (PID: $oldPid)" -ForegroundColor Green
        Start-Sleep -Seconds 2
    } catch {
        Write-Host "⚠️ Daemon already stopped" -ForegroundColor Yellow
    }
} else {
    Write-Host "⚠️ No daemon PID file found" -ForegroundColor Yellow
}

# Clean up old PID file
Remove-Item "daemon.pid" -ErrorAction SilentlyContinue

# Start new daemon
Write-Host "`n2️⃣ Starting daemon with updated code..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "python -m src.daemon.core --config config/config.yaml --log-level INFO" -WindowStyle Normal

Write-Host "`n✅ Daemon restarted!" -ForegroundColor Green
Write-Host "📋 Check logs/senthium.log for security check messages" -ForegroundColor Cyan
Write-Host "📸 Snapshots now only saved for INTRUDERS (not authorized users)" -ForegroundColor Cyan
Write-Host ""
Write-Host "Test it:" -ForegroundColor Yellow
Write-Host "  1. Sit in front of camera - NO snapshots created" -ForegroundColor Gray
Write-Host "  2. Show unknown face - ONE intruder_*.jpg created" -ForegroundColor Gray
Write-Host ""
