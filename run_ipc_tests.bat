@echo off
REM Batch script to run IPC tests with environment variable set
REM Works in CMD (not PowerShell)

echo Cleaning up old processes and PID files...
taskkill /F /IM python.exe >nul 2>&1
timeout /t 1 /nobreak >nul
if exist senthium.pid del senthium.pid

echo.
echo Setting SENTHIUM_ENABLE_IPC=true
set SENTHIUM_ENABLE_IPC=true

echo.
echo Running IPC integration tests...
python -m pytest tests/test_integration.py::TestIPCCommunication -v --tb=short

echo.
echo Cleaning up...
taskkill /F /IM python.exe >nul 2>&1
if exist senthium.pid del senthium.pid

echo.
echo Done!
pause
