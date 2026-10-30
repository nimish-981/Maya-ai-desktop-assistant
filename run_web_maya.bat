@echo off
title MAYA // CYBER COMPANION OS - WEB RUNTIME
cd /d "%~dp0"
echo =============================================================
echo   MAYA // CYBER COMPANION OS - WEB RUNTIME
echo   Local Address: http://localhost:8080
echo   Tools Loaded: 198 Multi-Agent Automation Tools
echo =============================================================
venv_312\Scripts\python.exe run_web_ui.py
pause

