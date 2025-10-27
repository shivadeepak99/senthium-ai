@echo off
echo.
echo ========================================
echo    Senthium AI - Streamlit Dashboard
echo ========================================
echo.
echo Starting Streamlit GUI...
echo Dashboard will open at http://localhost:8501
echo.
echo Press Ctrl+C to stop
echo.

venv\Scripts\python.exe -m streamlit run streamlit_app.py

pause
