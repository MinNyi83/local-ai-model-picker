#Requires -Version 5.1
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "[1/4] Checking Python..." -ForegroundColor Cyan
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Python not found. Install Python 3.10+ from https://www.python.org/downloads/ (add to PATH)." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "[2/4] Upgrading pip..." -ForegroundColor Cyan
python -m pip install --upgrade pip | Out-Null

Write-Host "[3/4] Installing dependencies (textual, youtube-transcript-api)..." -ForegroundColor Cyan
python -m pip install textual youtube-transcript-api
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to install dependencies." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "[4/4] Launching Local AI Model Picker (GUI)..." -ForegroundColor Cyan
python gui.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "App exited with an error." -ForegroundColor Red
    Read-Host "Press Enter to exit"
}
