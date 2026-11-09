#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

echo "[1/4] Checking Python..."
if ! command -v python3 >/dev/null 2>&1; then
    echo "python3 not found. Install Python 3.10+ (e.g. brew install python)."
    exit 1
fi

echo "[2/4] Upgrading pip..."
python3 -m pip install --upgrade pip >/dev/null 2>&1 || true

echo "[3/4] Installing dependencies (textual, youtube-transcript-api)..."
python3 -m pip install textual youtube-transcript-api

echo "[4/4] Launching Local AI Model Picker (GUI)..."
python3 gui.py
