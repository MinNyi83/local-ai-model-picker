# 🎮 Local AI Model Picker (GUI)

Native desktop app (no TUI, no WebUI) based on Codacus' video
"What's the Best AI Model Your GPU Can Actually Run? 4GB to 16GB VRAM"
(https://www.youtube.com/watch?v=tek-IY9BRWc).

## 🚀 Quickest start
- 🪟 Windows: `run.bat` (or build the exe — see 📁 Files)
- 🍎 macOS: double-click `run_mac.command` (first time: `chmod +x run_mac.command`)
- 🐧 Linux: `chmod +x run.sh && ./run.sh`

## 🍎 macOS build (on a Mac)
```bash
chmod +x build_mac.sh
./build_mac.sh
open dist/LocalAIModelPicker.app   # or drag into /Applications
```
- 🧠 Apple Silicon (M-series): auto-detects unified memory (RAM = VRAM)
- ⚡ llama.cpp builds with Metal (`-DGGML_METAL=ON`) — commands adjust automatically
- 📦 Also bundles `transcript.txt`, `BEGINNER_GUIDE.md`, `models_cache.json`

## ✨ Features
- 🖥️ Hardware: auto-detects OS, CPU, RAM, GPU, VRAM
- 💡 Recommend: picks a model + tier from your VRAM/RAM
- 🛠️ Setup: guides for 7 backends (llama.cpp, Ollama, LM Studio, Cline, vLLM, MLX, Strata)
- 📊 Models: 45-model database + 10-tier VRAM ladder + live HuggingFace fetch (incl. uncensored, auto-saved)
- ⌨️ Command: starter command + notes + copy/run + customize choice
- 🏠 Home: quick start + hardware snapshot + actions
- ℹ️ About: creator credits + YouTube reference
- 🔄 Auto-suggest updated model button
- 📋 Copy & ▶ Run commands in new terminal
- 🖱️ Clickable buttons everywhere

## 📁 Files
- `gui.py` - GUI app source (Tkinter)
- `app.py` - TUI app source (optional)
- `run.bat` / `run.ps1` - Windows launchers
- `run.sh` / `run_mac.command` - macOS/Linux launchers
- `build_mac.sh` - build a macOS .app bundle (run on a Mac)
- `transcript.txt` - full transcript (607 snippets)
- `models_cache.json` - saved HuggingFace model data
- `fetch_transcript.py` - re-fetch transcript
- `BEGINNER_GUIDE.md` - beginner guide (also in-app)
- `STEP_BY_STEP.md` - detailed guide

💡 To get the Windows `.exe`: run `pyinstaller --onefile --windowed --name "LocalAIModelPicker" --add-data "transcript.txt;." --add-data "BEGINNER_GUIDE.md;." --add-data "models_cache.json;." gui.py`

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