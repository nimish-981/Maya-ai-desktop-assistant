@echo off
title Push Maya Cyber Companion OS to Hugging Face Spaces
cd /d "%~dp0"
echo ==============================================================
echo   MAYA CYBER COMPANION OS - HUGGING FACE SPACES DEPLOYER
echo   Remote: https://huggingface.co/spaces/Nimish981/maya-cyber-companion-os
echo ==============================================================
echo.
echo [!] When prompted:
echo     Username: Nimish981
echo     Password: Paste your HF Access Token (Write permissions)
echo               Get token at: https://huggingface.co/settings/tokens
echo.
git push -u origin main --force
pause

