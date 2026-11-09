#!/bin/bash
# Launch Local AI Model Picker on macOS
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
    echo "python3 not found."
    echo "Install it with: brew install python"
    echo "Or download from: https://www.python.org/downloads/"
    read -r -p "Press Enter to close..."
    exit 1
fi

# Tkinter ships with python.org builds; Homebrew needs python-tk
python3 -c "import tkinter" 2>/dev/null || {
    echo "Tkinter missing. Installing python-tk via Homebrew..."
    brew install python-tk || true
}

python3 gui.py
