# 🎮 Local AI Model Picker (GUI)

Native desktop app (no TUI, no WebUI) based on Codacus' video
"What's the Best AI Model Your GPU Can Actually Run? 4GB to 16GB VRAM"
(https://www.youtube.com/watch?v=tek-IY9BRWc).

## 🚀 Quickest start
- 🪟 Windows: double-click `dist/LocalAIModelPicker.exe` (no Python needed), or `run.bat`
- 🍎 macOS / 🐧 Linux: `chmod +x run.sh && ./run.sh`

## ✨ Features
- 🖥️ Hardware: auto-detects OS, CPU, RAM, GPU, VRAM
- 💡 Recommend: picks a model + tier from your VRAM/RAM
- 🛠️ Setup: guides for 7 backends (llama.cpp, Ollama, LM Studio, Cline, vLLM, MLX, Strata)
- 📊 Models: 13-model ladder + VRAM tiers + live HuggingFace fetch (incl. uncensored)
- ⌨️ Command: starter command + notes + copy/run + customize choice
- 🏠 Home: quick start + hardware snapshot + actions
- ℹ️ About: creator credits + YouTube reference
- 🔄 Auto-suggest updated model button
- 📋 Copy & ▶ Run commands in new terminal
- 🖱️ Clickable buttons everywhere

## 📁 Files
- `gui.py` - GUI app source (Tkinter)
- `app.py` - TUI app source (optional)
- `dist/LocalAIModelPicker.exe` - Windows standalone (no Python)
- `run.bat` / `run.ps1` - Windows launchers
- `run.sh` - macOS/Linux launcher
- `transcript.txt` - full transcript (607 snippets)
- `fetch_transcript.py` - re-fetch transcript
- `STEP_BY_STEP.md` - detailed guide

## ⌨️ Usage
1. Launch the app
2. Home tab shows quick start + your hardware
3. Recommend tab shows suggested model; click "Suggest updated model"
4. Setup tab: pick backend, read guide, copy/run commands
5. Models tab: browse ladder or fetch live from HuggingFace
6. Command tab: copy/run starter command, customize choice
7. About tab: credits

## 👤 About
Creator: Nyi Min
Reference: https://www.youtube.com/watch?v=tek-IY9BRWc (Codacus)
"""
path">
D:\AI_Choice\README.md