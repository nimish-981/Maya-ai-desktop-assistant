@echo off
title MAYA // CYBER COMPANION OS - FULL ENGINE WEB RUNTIME
color 0b
echo =========================================================
echo   MAYA // CYBER COMPANION OS - WEB RUNTIME (FULL ENGINE)
echo   Initializing local web runtime and core engine...
echo =========================================================

cd /d "%~dp0\.."
set PYTHON_EXE=venv_312\Scripts\python.exe
if not exist "%PYTHON_EXE%" (
    set PYTHON_EXE=python
)

echo Starting server from: %CD% with %PYTHON_EXE%
start "" http://localhost:8080
"%PYTHON_EXE%" Web_maya\app.py
pause
