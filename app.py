"""Local AI Model Picker TUI - improved UX, multi-color, emoji, mouse"""
from __future__ import annotations

import os
import platform
import subprocess
import tempfile
from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import (
    Container,
    Grid,
    Horizontal,
    ScrollableContainer,
    Vertical,
)
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Input,
    Markdown,
    RichLog,
    Static,
    TabbedContent,
    TabPane,
)

APP_TITLE = "Local AI Model Picker"
VIDEO_URL = "https://www.youtube.com/watch?v=tek-IY9BRWc"

CSS = """
Screen {
    background: #0a0e14;
}

Header {
    background: #1a1f2e;
    color: #ff79c6;
    text-style: bold;
}

Footer {
    background: #1a1f2e;
    color: #8be9fd;
}

TabbedContent {
    background: #0a0e14;
}

TabPane {
    padding: 1 2;
    background: #0a0e14;
}

.panel {
    border: round #44475a;
    background: #1a1f2e;
    padding: 1 2;
    margin: 1 0;
}

.panel-title {
    color: #bd93f9;
    text-style: bold;
    margin-bottom: 1;
}

.hw-grid {
    grid-size: 2;
    grid-gutter: 1 2;
    margin: 1 0;
}

.hw-key {
    color: #ffb86c;
    text-style: bold;
}

.hw-val {
    color: #f8f8f2;
}

.rec-text {
    color: #50fa7b;
    padding: 1;
}

.section {
    color: #8be9fd;
    text-style: bold;
    margin: 1 0 0 0;
}

.setup-buttons {
    height: 3;
    margin: 1 0;
}

.setup-buttons Button {
    margin-right: 1;
    background: #282a36;
    color: #f8f8f2;
    border: tall #44475a;
}

.setup-buttons Button:hover {
    background: #44475a;
    color: #ff79c6;
}

.setup-buttons Button.-active {
    background: #6272a4;
    color: #f1fa8c;
}

#setup-text {
    color: #f8f8f2;
    padding: 1;
}

#cmd-text {
    background: #0a0e14;
    color: #8be9fd;
    border: round #44475a;
    padding: 1;
}

#notes-text {
    color: #6272a4;
    padding: 1;
}

DataTable {
    background: #1a1f2e;
    border: round #44475a;
}

Input {
    background: #0a0e14;
    border: tall #44475a;
    color: #f8f8f2;
}

Input:focus {
    border: tall #ff79c6;
}

RichLog {
    background: #0a0e14;
    border: round #44475a;
    color: #f8f8f2;
}

Button#refresh-btn {
    background: #50fa7b;
    color: #0a0e14;
    margin-top: 1;
    text-style: bold;
}

Button#refresh-btn:hover {
    background: #8be9fd;
}

.step {
    color: #f1fa8c;
    margin: 0 0 1 0;
}

.quick {
    color: #50fa7b;
    padding: 1;
}
"""


def _run(cmd: list[str]) -> str:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        return (r.stdout or "").strip()
    except Exception:
        return ""


def detect_hardware() -> dict:
    info = {
        "os": platform.system(),
        "cpu": "Unknown",
        "ram_gb": 0.0,
        "gpu": "Unknown",
        "vram_gb": 0.0,
        "vram_mib": 0,
    }
    if platform.system() == "Windows":
        out = _run(["powershell", "-Command",
                    "(Get-CimInstance Win32_Processor | Select-Object -First 1 -ExpandProperty Name)"])
        if out:
            info["cpu"] = out.strip()
        out = _run(["powershell", "-Command",
                    "(Get-CimInstance Win32_ComputerSystem | Select-Object -ExpandProperty TotalPhysicalMemory)"])
        try:
            info["ram_gb"] = round(int(out.strip()) / (1024 ** 3), 1)
        except ValueError:
            pass
    else:
        try:
            import os as _os
            info["ram_gb"] = round(_os.sysconf("SC_PAGE_SIZE") * _os.sysconf("SC_PHYS_PAGES") / (1024 ** 3), 1)
        except Exception:
            pass
        out = _run(["sh", "-c", "grep -m1 'model name' /proc/cpuinfo | cut -d: -f2"])
        if out:
            info["cpu"] = out.strip()

    out = _run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"])
    if out:
        parts = [p.strip() for p in out.splitlines()[0].split(",")]
        if len(parts) >= 2:
            info["gpu"] = parts[0]
            mem = parts[1].lower().replace("mib", "").strip()
            try:
                info["vram_mib"] = int(float(mem))
                info["vram_gb"] = round(info["vram_mib"] / 1024, 1)
            except ValueError:
                pass
    elif platform.system() == "Windows":
        out = _run(["powershell", "-Command",
                    "(Get-CimInstance Win32_VideoController | Select-Object -First 1 | ForEach-Object { $_.Name + '|' + $_.AdapterRAM })"])
        if "|" in out:
            name, ram = out.split("|", 1)
            info["gpu"] = name.strip()
            try:
                info["vram_gb"] = round(int(ram.strip()) / (1024 ** 3), 1)
            except ValueError:
                pass
    return info


def recommend(hw: dict) -> str:
    vram = hw["vram_gb"]
    ram = hw["ram_gb"]
    lines = []
    lines.append(f"GPU  : {hw['gpu']}  ({vram} GB VRAM)")
    lines.append(f"RAM  : {ram} GB")
    lines.append(f"CPU  : {hw['cpu']}")
    lines.append("")
    if vram < 3:
        lines.append(">> Link 3 tiny (8B) - runs on almost anything.")
        lines.append("   Try Mel 2.1 if you have >= 6 GB VRAM.")
        return "\n".join(lines)
    if ram < 8:
        lines.append(">> Stay with tiny models. Link 3 tiny is the best of them.")
        if vram >= 6:
            lines.append("   With >= 6 GB VRAM you can also try Mel 2.1.")
        return "\n".join(lines)
    if ram < 16:
        lines.append(">> Gemma 4 26B fits properly with >= 8 GB VRAM.")
        lines.append("   On any card, run Qwen 3.6 35B with --load-mode mmap (~25-30 tok/s on 4 GB).")
        return "\n".join(lines)
    if ram < 32:
        lines.append(">> Qwen 3.6 35B (MoE) or Flint, especially with <= 8 GB VRAM.")
        if vram >= 16:
            lines.append("   With a 16 GB card, run Qwen 3.8 27B (GSQ RCO) - best under 100B.")
        return "\n".join(lines)
    lines.append(">> Qwen 3.6 35B or Flint on any card with <= 8 GB VRAM.")
    if vram >= 16:
        lines.append("   With a 16 GB card, run Qwen 3.8 27B (GSQ RCO) - best under 100B.")
    if ram >= 64:
        lines.append("   With 64 GB+ RAM, try Strata/Maya with big flash models (Qwen 3.8 Flash 177B, DeepSeek V4.1 Flash 763B).")
    lines.append("")
    lines.append("Note: with 32 GB RAM, all 16 models on the ladder already run at 8 GB VRAM.")
    lines.append("Past 8 GB VRAM you buy speed and context, not a smarter model.")
    return "\n".join(lines)


MODELS = [
    ("Qwen 3.6 35B-A3B", "MoE", "~3 GB min / 24 GB full", "Baseline pick; 15/16 fit on 4 GB card"),
    ("Qwen 3.8 27B (GSQ RCO)", "Dense", "~15 GB / 16 GB", "16 GB pick; best under 100B params"),
    ("K2 Horizon", "MoE", "~6 GB min", "Smartest (~25 idx); 96 KB/token KV; 8 GB+ for 32k ctx"),
    ("LFM 2.5 24B", "Dense/MoE", "~3 GB min", "Fits on 4 GB card comfortably"),
    ("Neumotron 3.5 Lightning", "MoE", "~3 GB min", "3 KB/token KV; million-token context"),
    ("Gemma 4 26B", "MoE", "~3 GB min", "Good on 16 GB RAM + 8 GB VRAM"),
    ("Gemma 4 31B", "Dense", "~15 GB", "Dense sibling; higher score than 26B MoE"),
    ("Flint", "MoE", "3 GB+ / 26 GB+", "Needs 8 GB+ VRAM to fit well"),
    ("Link 3 tiny (8B)", "Dense", "< 3 GB", "Best tiny model; runs on almost anything"),
    ("GPT-OSS 20B", "MoE", "~3 GB min", "Scores below Link 3 tiny (8B)"),
    ("Mel 2.1", "MoE", "6 GB+", "Worth trying with >= 6 GB VRAM"),
    ("Qwen 3.8 Flash (177B)", "MoE", "12 GB + 64 GB RAM + SSD", "Strata/Maya; ~45 tok/s decode"),
    ("DeepSeek V4.1 Flash (763B)", "MoE", "16 GB + 64 GB RAM + SSD", "Runs on one 16 GB card via thecodacus fork"),
]

VRAM_TIERS = [
    ("4 GB", "Qwen 3.6 35B (Q4, experts in RAM)", "15/16 models fit with 32 GB RAM; ~33 tok/s"),
    ("6 GB", "Qwen 3.6 35B + ~2 GB expert cache", "Room for MoE cache; 8B dense also fits on card"),
    ("8 GB", "K2 Horizon (32k ctx) / Qwen 3.6 (128k ctx)", "Context is what you buy here"),
    ("12 GB", "Qwen 3.6 ~51 tok/s", "AutoFit pulls more experts on-card; prefill up to ~860 tok/s"),
    ("16 GB", "Qwen 3.8 27B (GSQ RCO, fits fully)", "Dense model fully resident; MoE still partly in RAM"),
    ("16 GB+", "DeepSeek V4.1 Flash (763B)", "Three-tier: card / RAM / SSD"),
]

SETUPS = {
    "llama.cpp": """llama.cpp (recommended, most compatible)
- Free & open source; runs on Nvidia/AMD/Intel/Apple/CPU.
- 58 of 97 MoE families under 40B already run on it.
Steps:
  1. Install Git, CMake, a C++ compiler.
  2. git clone https://github.com/ggml-org/llama.cpp
  3. Build for your hardware (see build page; CUDA example below).
  4. Run llama-server, point at a Hugging Face model (auto-downloads).
  5. Open the printed port in your browser for a chat UI.
Build (Nvidia/CUDA):
  cmake -B build -DGGML_CUDA=ON
  cmake --build build --config Release -j
Run:
  ./build/bin/llama-server -hf unsloth/Qwen3.6-35B-A3B-GGUF \\
    -hff Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf -c 32768 \\
    -ctk q8_0 -ctv q8_0 --no-mmproj --port 8080 \\
    --fit-target 512 -ub 1024 --moe-cache-mib 2048
Notes: --fit-target 512 makes almost any MoE <40B fit on 4 GB. Drop -ub 1024/--moe-cache-mib on tight VRAM. Add --load-mode mmap if short on RAM. Set -t to ~half your cores.""",
    "Ollama": """Ollama (friendly wrapper around an engine)
- Easiest way to run local models; pulls models by name.
- Good for trying models quickly; wraps llama.cpp under the hood.
Steps:
  1. Download Ollama from ollama.com and install.
  2. ollama pull qwen3.6:35b (or another model)
  3. ollama run qwen3.6:35b
  4. (Optional) point Cline Desktop / apps at http://localhost:11434 (OpenAI-compatible).
Tip: For MoE offloading control (fit-target, expert cache), use llama.cpp directly.""",
    "LM Studio": """LM Studio (friendly GUI app)
- Desktop app with model browser, chat, and local server.
- Works with Ollama/llama.cpp models; easy for non-CLI users.
Steps:
  1. Download LM Studio, install.
  2. Search & download a GGUF (e.g. Qwen 3.6 35B).
  3. Load model, start chat or local server.
  4. Adjust context size and GPU offload in the UI.""",
    "Cline Desktop": """Cline Desktop (sponsor; free & open source)
- Checks your hardware and shows which models run well (with Ollama/LM Studio).
- Can use llama.cpp as an OpenAI-compatible provider.
- ClinePass ($9.99/mo) gives ~5x limits on curated open-weight models.
Steps:
  1. Download from cline.gg/desktop-codacus
  2. Add local provider (Ollama/LM Studio/llama.cpp endpoint).
  3. Ask it to build/run tasks; switch to ClinePass for bigger models.""",
    "vLLM / SGLang": """vLLM / SGLang (server-focused)
- Built for servers where the whole model sits on big GPUs.
- Not ideal for split CPU/GPU MoE offloading on consumer cards.
- Use when you have enough VRAM to hold the model fully.""",
    "MLX": """MLX (Apple silicon)
- Built for Apple silicon (M-series).
- Good on Macs; not for Nvidia/AMD/Intel PCs.""",
    "Strata / Maya": """Strata / Maya (exotic, 64 GB+ RAM)
- Overlap SSD streaming with expert caching.
- Run huge MoE models (177B-763B) on 12-16 GB VRAM + 64 GB RAM + SSD.
- ~45 tok/s decode, ~1000 tok/s prefill on Flash models.
- Requires 64 GB+ RAM and fast SSD.""",
}

COMMANDS = {
    "llama.cpp": [
        ("Build (CUDA)", "cmake -B build -DGGML_CUDA=ON\ncmake --build build --config Release -j"),
        ("Run server", "./build/bin/llama-server -hf unsloth/Qwen3.6-35B-A3B-GGUF -hff Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf -c 32768 -ctk q8_0 -ctv q8_0 --no-mmproj --port 8080 --fit-target 512 -ub 1024 --moe-cache-mib 2048"),
        ("Clone", "git clone https://github.com/ggml-org/llama.cpp"),
    ],
    "Ollama": [
        ("Pull model", "ollama pull qwen3.6:35b"),
        ("Run model", "ollama run qwen3.6:35b"),
    ],
    "LM Studio": [],
    "Cline Desktop": [],
    "vLLM / SGLang": [],
    "MLX": [],
    "Strata / Maya": [],
}

COMMAND = """./build/bin/llama-server -hf unsloth/Qwen3.6-35B-A3B-GGUF -hff Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf \\
  -c 32768 -ctk q8_0 -ctv q8_0 --no-mmproj --port 8080 \\
  --fit-target 512 -ub 1024 --moe-cache-mib 2048"""

NOTES = [
    "Flags never run all together - treat as a starting point.",
    "On tight VRAM: drop -ub 1024 and --moe-cache-mib 2048.",
    "Short on RAM: add --load-mode mmap.",
    "Expert cache (--moe-cache-mib) only helps small batches (<=32 tokens): generation, not prefill.",
    "K2 Horizon on 8 GB needs -ot attn_v_exps=CPU (disables auto-fit).",
    "DeepSeek V4.1 Flash = 763B (552B backbone + 197B Engram + 14B MTP + 0.5B vision).",
    "Threads: -t ~half your cores (MoE gets slower when every core is busy).",
    "Context: keep -ctk/-ctv q8_0 (halves context VRAM).",
    "Scores: Artificial Analysis Intelligence Index v4.3.2 (2026-10-21); model pages vs independent tests differ.",
]

QUICK_START = """Quick Start (3 steps)

1. Check your hardware  ->  Hardware tab (auto-detected on load)
2. Get a recommendation  ->  Recommend tab
3. Pick a backend + run   ->  Setup tab (copy/run commands)

Your machine: {gpu} / {vram} GB VRAM / {ram} GB RAM
Recommended: {rec}
"""


class PickerApp(App):
    TITLE = APP_TITLE
    SUB_TITLE = "Hardware-aware local AI picker"
    CSS = CSS
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh_hw", "Refresh"),
        Binding("1", "tab_home", show=False),
        Binding("2", "tab_hardware", show=False),
        Binding("3", "tab_recommend", show=False),
        Binding("4", "tab_setup", show=False),
        Binding("5", "tab_models", show=False),
        Binding("6", "tab_command", show=False),
    ]

    def __init__(self):
        super().__init__()
        self.hw = detect_hardware()
        self._current_commands = []

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent(initial="home"):
            # Home / Quick Start
            with TabPane("Home", id="home"):
                with Container(classes="panel"):
                    yield Static("Quick Start", classes="panel-title")
                    yield Static("", id="quick-text", classes="quick")
                with Container(classes="panel"):
                    yield Static("Hardware snapshot", classes="panel-title")
                    with Grid(classes="hw-grid"):
                        yield Static("GPU", classes="hw-key")
                        yield Static(self.hw["gpu"], classes="hw-val", id="hw-gpu2")
                        yield Static("VRAM", classes="hw-key")
                        yield Static(f"{self.hw['vram_gb']} GB", classes="hw-val", id="hw-vram2")
                        yield Static("RAM", classes="hw-key")
                        yield Static(f"{self.hw['ram_gb']} GB", classes="hw-val", id="hw-ram2")
                with Container(classes="panel"):
                    yield Static("Actions", classes="panel-title")
                    with Horizontal(classes="setup-buttons"):
                        yield Button("Refresh hardware", id="refresh-btn")
                        yield Button("Go to Recommend", id="go_rec")
                        yield Button("Go to Setup", id="go_setup")
            # Hardware
            with TabPane("Hardware", id="hardware"):
                with Container(classes="panel"):
                    yield Static("System Hardware", classes="panel-title")
                    with Grid(classes="hw-grid"):
                        yield Static("OS", classes="hw-key")
                        yield Static(self.hw["os"], classes="hw-val", id="hw-os")
                        yield Static("CPU", classes="hw-key")
                        yield Static(self.hw["cpu"], classes="hw-val", id="hw-cpu")
                        yield Static("RAM", classes="hw-key")
                        yield Static(f"{self.hw['ram_gb']} GB", classes="hw-val", id="hw-ram")
                        yield Static("GPU", classes="hw-key")
                        yield Static(self.hw["gpu"], classes="hw-val", id="hw-gpu")
                        yield Static("VRAM", classes="hw-key")
                        yield Static(f"{self.hw['vram_gb']} GB ({self.hw['vram_mib']} MiB)", classes="hw-val", id="hw-vram")
                yield Button("Refresh hardware", id="refresh-btn2")
            # Recommend
            with TabPane("Recommend", id="recommend"):
                with Container(classes="panel"):
                    yield Static("Recommended setup for your machine", classes="panel-title")
                    yield Static("", id="rec-text", classes="rec-text")
            # Setup
            with TabPane("Setup", id="setup"):
                with Container(classes="panel"):
                    yield Static("Choose a backend", classes="panel-title")
                    with Horizontal(classes="setup-buttons"):
                        for i, name in enumerate(SETUPS):
                            yield Button(name, id=f"setup_{i}")
                with Container(classes="panel"):
                    yield Static("Guide", classes="panel-title")
                    yield ScrollableContainer(Static("", id="setup-text"))
                with Container(classes="panel"):
                    yield Static("Commands (copy / run)", classes="panel-title")
                    yield Vertical(id="commands-box")
            # Models
            with TabPane("Models", id="models"):
                with Container(classes="panel"):
                    yield Static("Model ladder (under 40B params + flash models)", classes="panel-title")
                    yield self._models_table()
                with Container(classes="panel"):
                    yield Static("VRAM tiers", classes="panel-title")
                    yield self._tiers_table()
            # Command
            with TabPane("Command", id="command"):
                with Container(classes="panel"):
                    yield Static("Starter command (llama-server)", classes="panel-title")
                    yield Static(COMMAND, id="cmd-text")
                    with Horizontal(classes="setup-buttons"):
                        yield Button("Copy command", id="cmd_copy")
                        yield Button("Run command", id="cmd_run")
                with Container(classes="panel"):
                    yield Static("Notes", classes="panel-title")
                    yield Static("\n".join(f"- {n}" for n in NOTES), id="notes-text")
        yield Footer()

    def _models_table(self) -> DataTable:
        t = DataTable(id="models-table", zebra_stripes=True)
        t.add_columns("Model", "Type", "VRAM", "Notes")
        for row in MODELS:
            t.add_row(*row)
        return t

    def _tiers_table(self) -> DataTable:
        t = DataTable(id="tiers-table", zebra_stripes=True)
        t.add_columns("VRAM", "Recommended model", "Notes")
        for row in VRAM_TIERS:
            t.add_row(*row)
        return t

    def on_mount(self) -> None:
        self._update_hw()

    def _update_hw(self) -> None:
        self.hw = detect_hardware()
        for suffix in ("", "2"):
            try:
                self.query_one(f"#hw-os{'' if suffix else ''}", Static)
            except Exception:
                pass
        # update all hardware displays
        mapping = {
            "hw-os": self.hw["os"],
            "hw-cpu": self.hw["cpu"],
            "hw-ram": f"{self.hw['ram_gb']} GB",
            "hw-gpu": self.hw["gpu"],
            "hw-vram": f"{self.hw['vram_gb']} GB ({self.hw['vram_mib']} MiB)",
            "hw-gpu2": self.hw["gpu"],
            "hw-vram2": f"{self.hw['vram_gb']} GB",
            "hw-ram2": f"{self.hw['ram_gb']} GB",
        }
        for wid, val in mapping.items():
            try:
                self.query_one(f"#{wid}", Static).update(val)
            except Exception:
                pass
        try:
            self.query_one("#rec-text", Static).update(recommend(self.hw))
        except Exception:
            pass
        try:
            rec = recommend(self.hw).splitlines()[0] if recommend(self.hw).splitlines() else ""
            quick = QUICK_START.format(
                gpu=self.hw["gpu"],
                vram=self.hw["vram_gb"],
                ram=self.hw["ram_gb"],
                rec=rec,
            )
            self.query_one("#quick-text", Static).update(quick)
        except Exception:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id or ""
        if bid in ("refresh-btn", "refresh-btn2"):
            self._update_hw()
            return
        if bid == "go_rec":
            self.query_one(TabbedContent).active = "recommend"
            return
        if bid == "go_setup":
            self.query_one(TabbedContent).active = "setup"
            return
        if bid == "cmd_copy":
            self.copy_to_clipboard(COMMAND)
            self.notify("Command copied to clipboard")
            return
        if bid == "cmd_run":
            self._run_command(COMMAND, "primary")
            return
        if bid.startswith("setup_"):
            try:
                idx = int(bid.split("_", 1)[1])
                name = list(SETUPS.keys())[idx]
            except (ValueError, IndexError):
                return
            self.query_one("#setup-text", Static).update(SETUPS.get(name, ""))
            self._show_commands(name)
            return
        if bid.startswith("copy_"):
            try:
                idx = int(bid.split("_", 1)[1])
            except ValueError:
                return
            if 0 <= idx < len(self._current_commands):
                self.copy_to_clipboard(self._current_commands[idx][1])
                self.notify("Command copied to clipboard")
            return
        if bid.startswith("run_"):
            try:
                idx = int(bid.split("_", 1)[1])
            except ValueError:
                return
            if 0 <= idx < len(self._current_commands):
                self._run_command(self._current_commands[idx][1], f"cmd{idx}")
            return

    def _show_commands(self, backend: str) -> None:
        box = self.query_one("#commands-box", Vertical)
        box.remove_children()
        cmds = COMMANDS.get(backend, [])
        self._current_commands = cmds
        if not cmds:
            box.mount(Static("No runnable commands for this backend."))
            return
        for i, (label, cmd) in enumerate(cmds):
            row = Horizontal()
            box.mount(row)
            row.mount(Static(f"{label}:", classes="hw-key"))
            row.mount(Static(cmd, classes="hw-val"))
            btns = Horizontal()
            row.mount(btns)
            btns.mount(Button("Copy", id=f"copy_{i}"))
            btns.mount(Button("Run", id=f"run_{i}"))

    def _run_command(self, cmd: str, tag: str) -> None:
        try:
            if platform.system() == "Windows":
                fd, path = tempfile.mkstemp(suffix=".bat", prefix=f"run_{tag}_")
                with os.fdopen(fd, "w") as f:
                    f.write("@echo off\n")
                    f.write(cmd + "\n")
                    f.write("pause\n")
                subprocess.Popen(f'start cmd /k "{path}"', shell=True)
            elif platform.system() == "Darwin":
                fd, path = tempfile.mkstemp(suffix=".sh", prefix=f"run_{tag}_")
                with os.fdopen(fd, "w") as f:
                    f.write("#!/bin/bash\n")
                    f.write(cmd + "\n")
                os.chmod(path, 0o755)
                subprocess.Popen(["open", "-a", "Terminal", path])
            else:
                fd, path = tempfile.mkstemp(suffix=".sh", prefix=f"run_{tag}_")
                with os.fdopen(fd, "w") as f:
                    f.write("#!/bin/bash\n")
                    f.write(cmd + "\n")
                os.chmod(path, 0o755)
                subprocess.Popen(["x-terminal-emulator", "-e", f"bash {path}"])
            self.notify(f"Launched: {tag}")
        except Exception as e:
            self.notify(f"Failed to run: {e}", severity="error")

    def action_refresh_hw(self) -> None:
        self._update_hw()

    def action_tab_home(self) -> None:
        self.query_one(TabbedContent).active = "home"

    def action_tab_hardware(self) -> None:
        self.query_one(TabbedContent).active = "hardware"

    def action_tab_recommend(self) -> None:
        self.query_one(TabbedContent).active = "recommend"

    def action_tab_setup(self) -> None:
        self.query_one(TabbedContent).active = "setup"

    def action_tab_models(self) -> None:
        self.query_one(TabbedContent).active = "models"

    def action_tab_command(self) -> None:
        self.query_one(TabbedContent).active = "command"


if __name__ == "__main__":
    PickerApp().run()
