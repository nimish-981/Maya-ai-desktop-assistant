@echo off
title Maya Holographic AI Assistant
cd /d "%~dp0"
echo ==================================================
echo Launching Maya Holographic Cyber HUD...
echo ==================================================
venv_312\Scripts\python.exe run_desktop_app.py
if errorlevel 1 (
    echo Native desktop window unavailable, starting local web server...
    start http://localhost:8080
    venv_312\Scripts\python.exe Web_maya\app.py
)
pause
