@echo off
REM Senthium AI Daemon Starter
REM This script starts the daemon correctly with proper Python path

echo Starting Senthium AI Daemon...
echo.

set PYTHONPATH=%~dp0
.\venv311\Scripts\python.exe src\daemon\core.py --config config\config.yaml --log-level INFO

echo.
echo Daemon stopped.
pause
