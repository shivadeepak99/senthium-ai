# Senthium v0.1 Validation Script
# This script validates that all components are properly set up

Write-Host ""
Write-Host "🔍 Senthium v0.1 Validation Script" -ForegroundColor Cyan
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host ""

$ErrorCount = 0

# Function to test a condition
function Test-Step {
    param(
        [string]$Name,
        [scriptblock]$Test
    )
    
    Write-Host "✓ Testing: $Name..." -ForegroundColor Yellow -NoNewline
    try {
        $result = & $Test
        if ($result) {
            Write-Host " PASS" -ForegroundColor Green
            return $true
        } else {
            Write-Host " FAIL" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host " ERROR: $_" -ForegroundColor Red
        return $false
    }
}

# Check Python version
if (Test-Step "Python 3.9+" {
    $pyVersion = python --version 2>&1
    $pyVersion -match "Python 3\.(9|1[0-9]|[2-9][0-9])"
}) {
    Write-Host "  Version: $(python --version)" -ForegroundColor Gray
} else {
    $ErrorCount++
    Write-Host "  ERROR: Python 3.9+ required!" -ForegroundColor Red
}

# Check virtual environment
if (Test-Step "Virtual Environment" {
    $null -ne $env:VIRTUAL_ENV
}) {
    Write-Host "  Active: $env:VIRTUAL_ENV" -ForegroundColor Gray
} else {
    $ErrorCount++
    Write-Host "  WARNING: Virtual environment not activated!" -ForegroundColor Yellow
    Write-Host "  Run: .\venv\Scripts\Activate.ps1" -ForegroundColor Yellow
}

# Check if dependencies are installed
Write-Host ""
Write-Host "✓ Checking Dependencies..." -ForegroundColor Yellow
$dependencies = @("psutil", "pytest", "colorlog", "pyyaml", "black", "flake8")
foreach ($dep in $dependencies) {
    $installed = pip list 2>$null | Select-String $dep
    if ($installed) {
        Write-Host "  ✓ $dep" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $dep (missing)" -ForegroundColor Red
        $ErrorCount++
    }
}

# Check project structure
Write-Host ""
Write-Host "✓ Checking Project Structure..." -ForegroundColor Yellow
$requiredDirs = @(
    "src\daemon",
    "src\cli",
    "src\rules",
    "src\ipc",
    "src\utils",
    "tests",
    "docs",
    "config",
    "scripts",
    "logs"
)

foreach ($dir in $requiredDirs) {
    if (Test-Path $dir) {
        Write-Host "  ✓ $dir" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $dir (missing)" -ForegroundColor Red
        $ErrorCount++
    }
}

# Check required files
Write-Host ""
Write-Host "✓ Checking Required Files..." -ForegroundColor Yellow
$requiredFiles = @(
    "src\daemon\monitor.py",
    "src\utils\logger.py",
    "tests\test_monitor.py",
    "requirements.txt",
    "setup.py",
    "pytest.ini",
    ".gitignore",
    "README.md",
    "LICENSE"
)

foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "  ✓ $file" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $file (missing)" -ForegroundColor Red
        $ErrorCount++
    }
}

# Run tests
Write-Host ""
Write-Host "✓ Running Tests..." -ForegroundColor Yellow
try {
    $testResult = pytest --tb=short -v 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  All tests passed!" -ForegroundColor Green
        Write-Host ""
        Write-Host $testResult
    } else {
        Write-Host "  Some tests failed!" -ForegroundColor Red
        Write-Host ""
        Write-Host $testResult
        $ErrorCount++
    }
} catch {
    Write-Host "  ERROR: Could not run tests" -ForegroundColor Red
    Write-Host "  Make sure pytest is installed: pip install pytest" -ForegroundColor Yellow
    $ErrorCount++
}

# Test monitor module
Write-Host ""
Write-Host "✓ Testing Monitor Module (3 seconds)..." -ForegroundColor Yellow
try {
    $job = Start-Job -ScriptBlock {
        param($pwd)
        Set-Location $pwd
        if ($env:VIRTUAL_ENV) {
            & "$env:VIRTUAL_ENV\Scripts\Activate.ps1"
        }
        Set-Location src
        python -m daemon.monitor 2>&1
    } -ArgumentList (Get-Location)
    
    Start-Sleep -Seconds 3
    Stop-Job $job
    $output = Receive-Job $job
    Remove-Job $job
    
    if ($output -match "Senthium System Monitor") {
        Write-Host "  Monitor module working!" -ForegroundColor Green
    } else {
        Write-Host "  Monitor module test unclear" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ERROR: Could not test monitor module" -ForegroundColor Red
    $ErrorCount++
}

# Summary
Write-Host ""
Write-Host ("=" * 60) -ForegroundColor Cyan
if ($ErrorCount -eq 0) {
    Write-Host "✅ All validation checks passed!" -ForegroundColor Green
    Write-Host ""
    Write-Host "🎉 Version 0.1 is ready!" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "  1. Run: cd src; python -m daemon.monitor" -ForegroundColor White
    Write-Host "  2. Review: version_0.1.md for completion checklist" -ForegroundColor White
    Write-Host "  3. Commit: git add . && git commit -m 'feat: v0.1 complete'" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host "❌ Validation failed with $ErrorCount error(s)" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please fix the errors above and run this script again." -ForegroundColor Yellow
    Write-Host ""
}

Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host ""
