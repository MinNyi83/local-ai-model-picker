@echo off
setlocal
cd /d "%~dp0"

echo [1/4] Checking Python...
where python >nul 2>nul
if errorlevel 1 (
    echo Python not found. Please install Python 3.10+ from https://www.python.org/downloads/
    echo Make sure to check "Add python.exe to PATH".
    pause
    exit /b 1
)

echo [2/4] Upgrading pip...
python -m pip install --upgrade pip >nul 2>&1

echo [3/4] Installing dependencies (textual, youtube-transcript-api)...
python -m pip install textual youtube-transcript-api
if errorlevel 1 (
    echo Failed to install dependencies.
    pause
    exit /b 1
)

echo [4/4] Launching Local AI Model Picker (GUI)...
python gui.py
if errorlevel 1 (
    echo App exited with an error.
    pause
)
endlocal
