@echo off
title Maya Voice Assistant
cd /d "%~dp0"
echo ==================================================
echo Starting Maya Voice Assistant...
echo ==================================================
venv_312\Scripts\python.exe main.py
if errorlevel 1 (
    echo.
    echo Maya exited with an error.
    pause
)
