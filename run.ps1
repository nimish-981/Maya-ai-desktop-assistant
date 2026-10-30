Set-Location -Path $PSScriptRoot
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "Starting Maya Voice Assistant..." -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
& "$PSScriptRoot\venv_312\Scripts\python.exe" "$PSScriptRoot\main.py"
