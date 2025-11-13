@echo off
echo ========================================
echo SENTHIUM DAEMON - FOREGROUND TEST
echo ========================================
echo.
echo This will run the daemon in FOREGROUND mode
echo so you can see all the logs in real-time!
echo.
echo Press Ctrl+C to stop
echo.
echo ========================================
echo.

python -m src.daemon.core --config config/config.yaml --log-level DEBUG

pause
