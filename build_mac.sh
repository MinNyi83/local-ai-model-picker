#!/bin/bash
# Build a macOS .app bundle (run this ON a Mac, not Windows)
# Usage: bash build_mac.sh
set -e
cd "$(dirname "$0")"

python3 -m pip install --upgrade pip
python3 -m pip install pyinstaller
python3 -m pip install -r requirements.txt 2>/dev/null || true

pyinstaller --windowed \
    --name "LocalAIModelPicker" \
    --osx-bundle-identifier com.nyimin.localaimodelpicker \
    --add-data "transcript.txt:." \
    --add-data "BEGINNER_GUIDE.md:." \
    --add-data "models_cache.json:." \
    --clean gui.py

echo ""
echo "Build complete!"
echo "  App bundle : dist/LocalAIModelPicker.app"
echo "  To install : drag LocalAIModelPicker.app into /Applications"
echo "  To run     : open dist/LocalAIModelPicker.app"
