"""Local AI Model Picker - native desktop GUI (Tkinter) - redesigned"""
from __future__ import annotations

import json
import os
import platform
import subprocess
import tempfile
import threading
import urllib.request
import urllib.error
from pathlib import Path

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

APP_TITLE = "Local AI Model Picker"
VIDEO_URL = "https://www.youtube.com/watch?v=tek-IY9BRWc"

# ---------- theme ----------
BG = "#0b0f14"
PANEL = "#151a23"
BORDER = "#2a3140"
FG = "#e6edf3"
MUTED = "#8b949e"
ACCENT = "#58a6ff"
SUCCESS = "#3fb950"
WARN = "#d29922"
ERR = "#f85149"
INPUT_BG = "#0b0f14"
CARD = "#1c2333"

# ---------- data ----------

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
    # ---- curated picks from live HuggingFace data ----
    ("Qwen3.8-27B (HF top)", "Dense", "~16 GB", "HF: 7.6M downloads, 19k likes — most popular local pick"),
    ("Qwen3-14B", "Dense", "~9 GB (Q4)", "HF: 12.9M downloads; great 8-12 GB all-rounder"),
    ("Qwen3-8B", "Dense", "~5 GB (Q4)", "HF: 6.9M downloads; fits 6-8 GB cards easily"),
    ("Qwen3-4B", "Dense", "~3 GB (Q4)", "HF: 5.7M downloads; strong 4 GB card model"),
    ("Llama-3.1-8B-Instruct", "Dense", "~5 GB (Q4)", "HF: 4.3M downloads, 8.8k likes; classic reliable 8B"),
    ("GPT-OSS-20b (openai)", "MoE", "~4 GB (MXFP4)", "HF: 5.8M downloads; runs fully on 8 GB GPU"),
    ("GPT-OSS-120b", "MoE", "~18 GB (MXFP4)", "HF: 2.4M downloads; needs 24 GB+ or big RAM"),
    ("Mistral-7B-Instruct v0.2", "Dense", "~4 GB (Q4)", "HF: 1.5M downloads; fast lightweight chat"),
    ("Qwen2.5-7B-Instruct", "Dense", "~4.5 GB (Q4)", "HF: 6M downloads; solid coder/chat baseline"),
    ("Qwen2.5-Coder-14B", "Dense", "~9 GB (Q4)", "HF: 1.9M downloads; best local coding 14B"),
    ("Qwen3-Coder-30B-A3B", "MoE", "~4 GB min", "HF: 1.5M downloads; coding MoE, 3B active"),
    ("DeepSeek-R1-distill-8B tier", "Dense", "~5 GB (Q4)", "HF: DeepSeek-R1 1.6M downloads (full R1 = 671B)"),
    ("GLM-5.3 (zai-org)", "MoE", "~8 GB min", "HF: 2M downloads, 2.4k likes; strong reasoning"),
    ("GLM-5.3-Flash", "MoE", "~4 GB min", "HF: 6.4M downloads; fast GLM variant"),
    ("DeepSeek-V4-Flash-0731", "MoE", "~8 GB min", "HF: 2.7M downloads, 4.1k likes; new 2026 flagship-class flash"),
    ("Ornith-1.5-35B-A3B", "MoE", "~4 GB min", "HF: 4.2M downloads; Qwen3.6-class MoE alternative"),
    ("Ornith-1.5-9B", "Dense", "~6 GB (Q4)", "HF: 5.7M downloads; popular small model"),
    ("Gemma-4-31B-it (google)", "Dense", "~18 GB (Q4)", "HF: 7.2M downloads, 4.3k likes; top dense open model"),
    ("Nemotron-3-Nano-30B-A3B (nvidia)", "MoE", "~5 GB min", "HF: 1.6M downloads; efficient Nvidia MoE"),
    ("Nemotron-3-Nano-4B (nvidia)", "Dense", "~3 GB (Q4)", "HF: 1.9M downloads; tiny fast assistant"),
    ("Qwen3.8-27B-Uncensored", "Dense", "~16 GB", "HF: 2.5M downloads, 1.9k likes; uncensored local pick"),
    ("Dolphin-2.9.1-yi-1.5-34b", "Dense", "~19 GB (Q4)", "HF: 4.8M downloads; uncensored 34B"),
    ("MiniMax-H3", "MoE", "~8 GB min", "HF: 6.4M downloads, 6.7k likes; rising 2026 model"),
    ("Ternary-Bonsai-2-27B", "Ternary", "~6 GB", "HF: 1.7M downloads, 3k likes; extreme quant research pick"),
    ("Qwen3.5-9B", "Dense", "~6 GB (Q4)", "HF: 6.3M downloads, 2.3k likes; newest 9B gen"),
]

VRAM_TIERS = [
    ("2 GB", "Link 3 tiny (8B, Q3) / Qwen3-0.6B", "Petal-size GPUs & iGPU; tiny chatbots, 4k ctx"),
    ("4 GB", "Qwen3-4B / Qwen 3.6 35B (Q4, experts in RAM)", "15/16 models fit with 32 GB RAM; ~33 tok/s"),
    ("6 GB", "Qwen3-8B (Q4) / Qwen 3.6 35B + 2 GB cache", "Room for MoE cache; 8B dense fully on card"),
    ("8 GB", "K2 Horizon (32k ctx) / Qwen 3.6 (128k ctx)", "Context is what you buy here; gpt-oss-20b fits"),
    ("12 GB", "Qwen3.6 ~51 tok/s / Mistral-7B fast", "AutoFit pulls more experts on-card; prefill ~860 tok/s"),
    ("16 GB", "Qwen 3.8 27B (GSQ RCO, fits fully)", "Dense 27B fully resident; best quality under 100B"),
    ("24 GB", "Gemma-4-31B (Q4) / Qwen3.8-27B (Q8)", "RTX 4090/5090 class; 31B dense + long context"),
    ("32 GB", "Qwen3-32B (Q8) / GLM-5.3 (Q4 MoE)", "Apple M-series & pro cards; near-lossless quants"),
    ("48 GB", "gpt-oss-120b (MXFP4) / 70B-class (Q4)", "Workstation tier; 120B MoE fully on card"),
    ("80 GB+", "DeepSeek V4.1 Flash (763B, 3-tier offload)", "Card / RAM / SSD offload; Strata-class decode"),
]

SETUPS = {
    "llama.cpp": """llama.cpp (recommended, most compatible)
- Free & open source; runs on Nvidia/AMD/Intel/Apple/CPU.
Steps:
  1. Install Git, CMake, a C++ compiler.
  2. git clone https://github.com/ggml-org/llama.cpp
  3. Build for your hardware (CUDA example below).
  4. Run llama-server, point at a Hugging Face model (auto-downloads).
  5. Open the printed port in your browser for a chat UI.
Build (Nvidia/CUDA):
  cmake -B build -DGGML_CUDA=ON
  cmake --build build --config Release -j
Run:
  ./build/bin/llama-server -hf unsloth/Qwen3.6-35B-A3B-GGUF -hff Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf -c 32768 -ctk q8_0 -ctv q8_0 --no-mmproj --port 8080 --fit-target 512 -ub 1024 --moe-cache-mib 2048
  6. Use --fit-target 512 so MoE models fit on small VRAM.
Tips:
  - --fit-target 512 makes almost any MoE <40B fit on 4 GB.
  - Drop -ub 1024/--moe-cache-mib on tight VRAM.
  - Add --load-mode mmap if short on RAM.
  - Set -t to ~half your cores (MoE gets slower when every core is busy).
  - Keep -ctk/-ctv q8_0 to halve context VRAM.
  - K2 Horizon on 8 GB needs -ot attn_v_exps=CPU (disables auto-fit).""",
    "Ollama": """Ollama (friendly wrapper)
- Easiest way to run local models; pulls models by name.
Steps:
  1. Download Ollama from ollama.com and install.
  2. ollama pull qwen3.6:35b
  3. ollama run qwen3.6:35b
  4. (Optional) point apps at http://localhost:11434""",
    "LM Studio": """LM Studio (friendly GUI app)
- Desktop app with model browser, chat, and local server.
Steps:
  1. Download LM Studio, install.
  2. Search & download a GGUF (e.g. Qwen 3.6 35B).
  3. Load model, start chat or local server.
  4. Adjust context size and GPU offload in the UI.""",
    "Cline Desktop": """Cline Desktop (free & open source)
- Checks your hardware and shows which models run well.
Steps:
  1. Download from cline.gg/desktop-codacus
  2. Add local provider (Ollama/LM Studio/llama.cpp endpoint).
  3. Ask it to build/run tasks.""",
    "vLLM / SGLang": """vLLM / SGLang (server-focused)
- Built for servers where the whole model sits on big GPUs.
- Use when you have enough VRAM to hold the model fully.""",
    "MLX": """MLX (Apple silicon)
- Built for Apple silicon (M-series).""",
    "Strata / Maya": """Strata / Maya (exotic, 64 GB+ RAM)
- Overlap SSD streaming with expert caching.
- Run huge MoE models (177B-763B) on 12-16 GB VRAM + 64 GB RAM + SSD.""",
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


def get_commands(name):
    """Return commands adjusted for the current OS (Metal on macOS, CUDA elsewhere)."""
    cmds = [list(c) for c in COMMANDS.get(name, [])]
    if platform.system() == "Darwin":
        if name == "llama.cpp":
            cmds[0] = ["Build (Apple Metal)",
                       "cmake -B build -DGGML_METAL=ON\n"
                       "cmake --build build --config Release -j"]
        elif name == "Ollama":
            cmds.insert(0, ["Install (Homebrew)", "brew install ollama"])
        elif name == "MLX":
            cmds = [("Install MLX", "pip install mlx mlx-lm"),
                    ("Run model", "python -m mlx_lm.generate --model mlx-community/Qwen3.8-27B-4bit")]
    elif platform.system() == "Linux":
        if name == "llama.cpp":
            cmds[0] = ["Build (CUDA)", "cmake -B build -DGGML_CUDA=ON\ncmake --build build --config Release -j"]
    else:  # Windows
        if name == "Ollama":
            cmds.insert(0, ["Install", "winget install Ollama.Ollama"])
    return cmds

NOTES = [
    "Flags never run all together - treat as a starting point.",
    "On tight VRAM: drop -ub 1024 and --moe-cache-mib 2048.",
    "Short on RAM: add --load-mode mmap.",
    "Expert cache (--moe-cache-mib) only helps small batches (<=32 tokens): generation, not prefill.",
    "K2 Horizon on 8 GB needs -ot attn_v_exps=CPU (disables auto-fit).",
    "DeepSeek V4.1 Flash = 763B (552B backbone + 197B Engram + 14B MTP + 0.5B vision).",
    "Threads: -t ~half your cores (MoE gets slower when every core is busy).",
    "Context: keep -ctk/-ctv q8_0 (halves context VRAM).",
]

# ---------- helpers ----------

def _run(cmd):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        return (r.stdout or "").strip()
    except Exception:
        return ""


def detect_hardware():
    info = {"os": platform.system(), "cpu": "Unknown", "ram_gb": 0.0,
            "gpu": "Unknown", "vram_gb": 0.0, "vram_mib": 0}
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
    elif platform.system() == "Darwin":
        # macOS: sysctl based detection
        cpu = _run(["sysctl", "-n", "machdep.cpu.brand_string"])
        if cpu:
            info["cpu"] = cpu.strip()
        mem = _run(["sysctl", "-n", "hw.memsize"])
        try:
            info["ram_gb"] = round(int(mem.strip()) / (1024 ** 3), 1)
        except (ValueError, OSError):
            pass
        # GPU via system_profiler (Apple Silicon = unified memory, VRAM = RAM)
        disp = _run(["system_profiler", "SPDisplaysDataType"])
        gpu_name = "Unknown GPU"
        for line in disp.splitlines():
            if "Chipset Model" in line:
                gpu_name = line.split(":", 1)[1].strip()
                break
        info["gpu"] = gpu_name
        if "Apple" in gpu_name or "Apple" in info["cpu"]:
            # Apple Silicon: unified memory — treat RAM as available VRAM
            info["vram_gb"] = info["ram_gb"]
            info["vram_mib"] = int(info["ram_gb"] * 1024)
            info["gpu"] = f"{gpu_name} (Apple Silicon, unified memory)"
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


def recommend(hw):
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


def auto_suggest_model(hw):
    vram = hw["vram_gb"]
    ram = hw["ram_gb"]
    if vram < 3 or ram < 8:
        return "Link 3 tiny (8B)"
    if ram < 16:
        return "Gemma 4 26B"
    if ram < 32:
        return "Qwen 3.6 35B" if vram < 16 else "Qwen 3.8 27B (GSQ RCO)"
    if vram >= 16:
        return "Qwen 3.8 27B (GSQ RCO)"
    return "Qwen 3.6 35B"


def fetch_models_online():
    results = []
    seen = set()
    urls = [
        "https://huggingface.co/api/models?pipeline_tag=text-generation&library=gguf&sort=downloads&direction=-1&limit=25",
        "https://huggingface.co/api/models?pipeline_tag=text-generation&sort=downloads&direction=-1&limit=20",
        "https://huggingface.co/api/models?search=uncensored&sort=downloads&direction=-1&limit=10",
        "https://huggingface.co/api/models?search=GGUF&sort=likes&direction=-1&limit=10",
    ]
    for url in urls:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "LocalAIModelPicker/1.0"})
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            for m in data:
                mid = m.get("id") or m.get("modelId")
                if not mid or mid in seen:
                    continue
                seen.add(mid)
                results.append({
                    "id": mid,
                    "downloads": m.get("downloads", 0),
                    "likes": m.get("likes", 0),
                    "tags": ", ".join(m.get("tags", [])[:6]),
                })
        except Exception:
            continue
    if not results:
        return None
    results.sort(key=lambda x: x["downloads"] + x["likes"] * 100, reverse=True)
    results = results[:50]
    # persist fetched data to local model database
    try:
        cache = Path(__file__).parent / "models_cache.json"
        cache.write_text(json.dumps(results, indent=2), encoding="utf-8")
    except Exception:
        pass
    return results


def load_cached_models():
    try:
        cache = Path(__file__).parent / "models_cache.json"
        if cache.exists():
            return json.loads(cache.read_text(encoding="utf-8"))
    except Exception:
        pass
    return None


def estimate_vram(model_id: str) -> str:
    """Estimate VRAM from a HuggingFace model name (param count + quant hints)."""
    import re
    name = model_id.split("/")[-1]
    low = name.lower()

    # known models whose names don't carry a param count: (total B, active B or None)
    special = {
        "deepseek-v3": (671, 37), "deepseek-v3.2": (671, 32), "deepseek-r1": (671, 37),
        "deepseek-v4-flash-0731": (671, 32), "deepseek-v4.1-flash": (671, 32),
        "gpt-oss-20b": (21, None), "gpt-oss-120b": (117, None),
        "k2-horizon": (32, 2),
    }
    for key, (total, active) in special.items():
        if key in low:
            total_b, active_b = total, active
            break
    else:
        # total params: 14B, 0.6B, 120b, 35B-A3B (take first X B token)
        m = re.search(r"(\d+(?:\.\d+)?)\s?b(?![a-z0-9])", low)
        # small models: 125m / 160m / 135m
        if not m:
            mm = re.search(r"(\d+(?:\.\d+)?)\s?m(?![a-z0-9])", low)
            if mm and float(mm.group(1)) < 10000:
                total_b, active_b = float(mm.group(1)) / 1000.0, None
            else:
                return "unknown"
        else:
            total_b, active_b = float(m.group(1)), None
            # active params for MoE: -A3B / -a4b
            ma = re.search(r"-a(\d+(?:\.\d+)?)b", low)
            if ma:
                active_b = float(ma.group(1))
    if total_b < 0.05:
        return "unknown"

    # quant detection
    if any(k in low for k in ("q8", "q8_0")):
        q, qname = 1.05, "Q8"
    elif any(k in low for k in ("mxfp4", "nvfp4", "4bit", "int4", "gpt-oss")):
        q, qname = 0.55, "4-bit"
    elif any(k in low for k in ("bf16", "fp16", "safetensors")) and "gguf" not in low:
        q, qname = 2.1, "BF16"
    else:
        q, qname = 0.62, "Q4"  # GGUF Q4_K_M default

    if active_b is not None:
        # MoE: experts live in RAM, active part on card
        mn = round(active_b * q + 1.0, 1)
        mx = round(total_b * q + 1.0, 1)
        return f"~{mn} GB min / {mx} GB full ({qname})"
    gb = round(total_b * q + 0.8, 1)
    return f"~{gb} GB ({qname})"


def _run_command(cmd, tag, root):
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
        messagebox.showinfo("Launched", f"Launched: {tag}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to run: {e}")


def copy_to_clipboard(root, text):
    root.clipboard_clear()
    root.clipboard_append(text)
    root.update()
    messagebox.showinfo("Copied", "Copied to clipboard")


# ---------- UI helpers ----------

# colorful button palette: kind -> (bg, fg, hover-bg, hover-fg)
BUTTON_KINDS = {
    "primary":  ("#1f6feb", "#ffffff", "#388bfd", "#ffffff"),
    "success":  ("#238636", "#ffffff", "#2ea043", "#ffffff"),
    "neutral":  ("#21262d", "#e6edf3", "#30363d", "#ffffff"),
    "purple":   ("#8957e5", "#ffffff", "#a371f7", "#ffffff"),
    "orange":   ("#d29922", "#1c1c1c", "#e3b341", "#1c1c1c"),
    "pink":     ("#db61a2", "#ffffff", "#f778ba", "#ffffff"),
    "teal":     ("#39c5cf", "#0b0f14", "#56d4dd", "#0b0f14"),
    "danger":   ("#da3633", "#ffffff", "#f85149", "#ffffff"),
}


def make_button(parent, text, command, kind="primary"):
    bg, fg, hbg, hfg = BUTTON_KINDS.get(kind, BUTTON_KINDS["neutral"])
    b = tk.Button(parent, text=text, command=command, bg=bg, fg=fg,
                  activebackground=hbg, activeforeground=hfg,
                  relief="flat", padx=14, pady=6, font=("Segoe UI", 10, "bold"),
                  cursor="hand2", borderwidth=0, highlightthickness=0)
    b.bind("<Enter>", lambda e: (b.config(bg=hbg, fg=hfg)) if str(b["state"]) != "disabled" else None)
    b.bind("<Leave>", lambda e: b.config(bg=bg, fg=fg))
    return b


# colorful accent per panel title emoji
PANEL_ACCENTS = ["#58a6ff", "#3fb950", "#d29922", "#db61a2", "#a371f7", "#39c5cf", "#f0883e", "#f85149"]


def make_panel(parent, title, accent=None):
    if accent is None:
        n = getattr(make_panel, "_n", 0)
        accent = PANEL_ACCENTS[n % len(PANEL_ACCENTS)]
        make_panel._n = n + 1
    outer = tk.Frame(parent, bg=CARD, highlightbackground=accent, highlightthickness=1)
    hdr = tk.Frame(outer, bg=CARD)
    hdr.pack(fill="x", padx=14, pady=(10, 4))
    # colored accent bar + title
    tk.Frame(hdr, bg=accent, width=4, height=18).pack(side="left", padx=(0, 8))
    tk.Label(hdr, text=title, bg=CARD, fg=accent, font=("Segoe UI", 12, "bold")).pack(side="left")
    return outer


def make_scrollable(parent):
    canvas = tk.Canvas(parent, bg=BG, highlightthickness=0)
    scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
    frame = tk.Frame(canvas, bg=BG)
    frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    win = canvas.create_window((0, 0), window=frame, anchor="nw")
    # stretch content to full canvas width (fixes empty gap on the right)
    canvas.bind("<Configure>", lambda e: canvas.itemconfigure(win, width=e.width))
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # mouse wheel scrolling over the whole tab
    def _on_wheel(event):
        if canvas.winfo_containing(event.x_root, event.y_root) is not None:
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    canvas.bind_all("<MouseWheel>", _on_wheel)
    return frame


# ---------- GUI ----------

class App:
    def __init__(self, root):
        self.root = root
        root.title(APP_TITLE)
        root.geometry("1040x760")
        root.minsize(900, 640)
        root.configure(bg=BG)

        self.hw = detect_hardware()
        self.current_commands = []
        self.all_models = [list(m) for m in MODELS]
        # auto-load cached HuggingFace models from previous sessions
        cached = load_cached_models()
        if cached:
            self._merge_online_models(cached)

        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("TNotebook", background=BG, borderwidth=0, tabmargins=(4, 4, 0, 0))
        style.configure("TNotebook.Tab", background="#161b22", foreground="#8b949e",
                        padding=(14, 8), font=("Segoe UI", 10, "bold"))
        style.map("TNotebook.Tab",
                  background=[("selected", "#1f6feb"), ("active", "#21262d")],
                  foreground=[("selected", "#ffffff"), ("active", "#e6edf3")])
        style.configure("Vertical.TScrollbar", background="#21262d", troughcolor=BG,
                        bordercolor=BG, arrowcolor="#8b949e")
        style.map("Vertical.TScrollbar", background=[("active", "#30363d")])

        # colorful app header
        header = tk.Frame(root, bg="#161b22", highlightbackground="#2a3140", highlightthickness=1)
        header.pack(fill="x", padx=10, pady=(10, 0))
        tk.Label(header, text="🤖 Local AI Model Picker", bg="#161b22", fg="#58a6ff",
                 font=("Segoe UI", 15, "bold")).pack(side="left", padx=14, pady=8)
        tk.Label(header, text="💻 detect → 🎯 recommend → 🛠️ setup → 🚀 run",
                 bg="#161b22", fg="#8b949e", font=("Segoe UI", 10)).pack(side="left", padx=8)
        tk.Label(header, text="📺 based on Codacus video", bg="#161b22", fg="#d29922",
                 font=("Segoe UI", 9)).pack(side="right", padx=14)

        nb = ttk.Notebook(root)
        nb.pack(fill="both", expand=True, padx=10, pady=10)
        self.nb = nb
        nb.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        self.tab_beginner = tk.Frame(nb, bg=BG)
        self.tab_home = tk.Frame(nb, bg=BG)
        self.tab_hw = tk.Frame(nb, bg=BG)
        self.tab_rec = tk.Frame(nb, bg=BG)
        self.tab_setup = tk.Frame(nb, bg=BG)
        self.tab_models = tk.Frame(nb, bg=BG)
        self.tab_cmd = tk.Frame(nb, bg=BG)
        self.tab_about = tk.Frame(nb, bg=BG)
        self.tab_online = tk.Frame(nb, bg=BG)

        nb.add(self.tab_beginner, text="🐣 Beginner")
        nb.add(self.tab_home, text="🏠 Home")
        nb.add(self.tab_hw, text="🖥️ Hardware")
        nb.add(self.tab_rec, text="💡 Recommend")
        nb.add(self.tab_setup, text="🛠️ Setup")
        nb.add(self.tab_models, text="📊 Models")
        nb.add(self.tab_cmd, text="⌨️ Command")
        nb.add(self.tab_online, text="🌐 Online")
        nb.add(self.tab_about, text="ℹ️ About")

        self._build_beginner()
        self._build_home()
        self._build_hw()
        self._build_rec()
        self._build_setup()
        self._build_models()
        self._build_cmd()
        self._build_online()
        self._build_about()

        # colorful status bar
        sb = tk.Frame(root, bg="#161b22", highlightbackground="#2a3140", highlightthickness=1)
        sb.pack(fill="x", side="bottom", padx=10, pady=(0, 10))
        self.status_bar = tk.Label(sb, text="🟢 Ready — pick a tab to begin",
                                   bg="#161b22", fg="#3fb950", font=("Segoe UI", 9),
                                   anchor="w", padx=12, pady=5)
        self.status_bar.pack(fill="x")
        tk.Label(sb, text="✨ v1.0 • by Nyi Min", bg="#161b22", fg="#8b949e",
                 font=("Segoe UI", 9)).pack(side="right", padx=12)

        self._update_hw()

    def _build_beginner(self):
        f = self.tab_beginner
        p = make_panel(f, "🐣 Beginner-Friendly Guide")
        p.pack(fill="both", expand=True, padx=12, pady=10)
        t = tk.Text(p, wrap="word", bg=INPUT_BG, fg=FG, relief="flat", padx=12, pady=12, font=("Segoe UI", 10))
        t.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        guide_path = Path(__file__).parent / "BEGINNER_GUIDE.md"
        try:
            content = guide_path.read_text(encoding="utf-8")
        except Exception:
            content = "Beginner guide not found. See BEGINNER_GUIDE.md in the app folder."
        t.insert("1.0", content)
        t.config(state="disabled")

    def _build_home(self):
        f = self.tab_home
        p = make_panel(f, "Quick Start")
        p.pack(fill="x", padx=12, pady=10)
        self.home_quick = tk.Text(p, height=7, wrap="word", bg=INPUT_BG, fg=FG, relief="flat", padx=10, pady=8, font=("Consolas", 10))
        self.home_quick.pack(fill="x", padx=12, pady=(0, 12))

        p2 = make_panel(f, "Hardware snapshot")
        p2.pack(fill="x", padx=12, pady=10)
        snap = tk.Frame(p2, bg=CARD)
        snap.pack(fill="x", padx=12, pady=(0, 12))
        self.home_gpu = tk.Label(snap, text="GPU: ...", bg=CARD, fg=FG, font=("Segoe UI", 10))
        self.home_gpu.pack(anchor="w", pady=2)
        self.home_vram = tk.Label(snap, text="VRAM: ...", bg=CARD, fg=FG, font=("Segoe UI", 10))
        self.home_vram.pack(anchor="w", pady=2)
        self.home_ram = tk.Label(snap, text="RAM: ...", bg=CARD, fg=FG, font=("Segoe UI", 10))
        self.home_ram.pack(anchor="w", pady=2)

        p3 = make_panel(f, "Actions")
        p3.pack(fill="x", padx=12, pady=10)
        ab = tk.Frame(p3, bg=CARD)
        ab.pack(fill="x", padx=12, pady=(0, 12))
        make_button(ab, "🔄 Refresh hardware", self._update_hw, "success").pack(side="left", padx=4)
        make_button(ab, "➡️ Go to Recommend", lambda: self._select_tab(3)).pack(side="left", padx=4)
        make_button(ab, "➡️ Go to Setup", lambda: self._select_tab(4)).pack(side="left", padx=4)

        p4 = make_panel(f, "💡 Suggestions")
        p4.pack(fill="both", expand=True, padx=12, pady=10)
        self.sugg_text = tk.Text(p4, height=6, wrap="word", bg=INPUT_BG, fg=FG, relief="flat", padx=10, pady=8, font=("Segoe UI", 10))
        self.sugg_text.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.sugg_text.insert("1.0", "Tips will appear here after hardware detection.")
        self.sugg_text.config(state="disabled")

    def _select_tab(self, idx):
        for w in self.root.winfo_children():
            if isinstance(w, ttk.Notebook):
                w.select(idx)
                break

    def _on_tab_changed(self, _event=None):
        if not hasattr(self, "status_bar"):
            return
        try:
            idx = self.nb.index(self.nb.select())
        except Exception:
            return
        names = ["🐣 Beginner", "🏠 Home", "🖥️ Hardware", "💡 Recommend", "🛠️ Setup",
                 "📊 Models", "⌨️ Command", "🌐 Online", "ℹ️ About"]
        tips = [
            "New here? Follow the beginner guide step by step.",
            "Overview of your machine and quick actions.",
            "Detected hardware — refresh any time.",
            "Get a model suggestion for your GPU/RAM.",
            "Pick a backend and follow the setup guide.",
            "Browse the model database (scrollable).",
            "Copy or run ready-made commands.",
            "Fetch the latest models from HuggingFace.",
            "Credits and references.",
        ]
        if 0 <= idx < len(names):
            self.status_bar.config(text=f"🟢 {names[idx]} — {tips[idx]}", fg="#3fb950")

    def _build_hw(self):
        f = self.tab_hw
        p = make_panel(f, "System Hardware")
        p.pack(fill="both", expand=True, padx=12, pady=10)
        g = tk.Frame(p, bg=CARD)
        g.pack(fill="x", padx=12, pady=(0, 12))
        self.hw_labels = {}
        rows = [("OS", "os"), ("CPU", "cpu"), ("RAM", "ram"), ("GPU", "gpu"), ("VRAM", "vram")]
        for i, (label, key) in enumerate(rows):
            tk.Label(g, text=label + ":", bg=CARD, fg=WARN, font=("Segoe UI", 10, "bold")).grid(row=i, column=0, sticky="w", padx=4, pady=4)
            lbl = tk.Label(g, text="...", bg=CARD, fg=FG, font=("Segoe UI", 10))
            lbl.grid(row=i, column=1, sticky="w", padx=4, pady=4)
            self.hw_labels[key] = lbl
        make_button(p, "🔄 Refresh hardware", self._update_hw, "success").pack(anchor="w", padx=12, pady=(0, 12))

    def _build_rec(self):
        f = self.tab_rec
        p = make_panel(f, "Recommended setup for your machine")
        p.pack(fill="both", expand=True, padx=12, pady=10)
        self.rec_text = tk.Text(p, wrap="word", bg=INPUT_BG, fg=SUCCESS, relief="flat", padx=10, pady=10, font=("Consolas", 10))
        self.rec_text.pack(fill="both", expand=True, padx=12, pady=(0, 8))
        sb = tk.Frame(p, bg=CARD)
        sb.pack(fill="x", padx=12, pady=(0, 12))
        make_button(sb, "✨ Suggest updated model", self._suggest_updated, "purple").pack(side="left", padx=4)
        self.suggest_label = tk.Label(sb, text="Suggested: ...", bg=CARD, fg=ACCENT, font=("Segoe UI", 10, "bold"))
        self.suggest_label.pack(side="left", padx=10)

    def _build_setup(self):
        f = make_scrollable(self.tab_setup)
        p = make_panel(f, "🛠️ Step 1: Choose a backend")
        p.pack(fill="x", padx=12, pady=10)
        row = tk.Frame(p, bg=CARD)
        row.pack(fill="x", padx=12, pady=(0, 12))
        self.backend_var = tk.StringVar(value="llama.cpp")
        cb = ttk.Combobox(row, textvariable=self.backend_var, values=list(SETUPS.keys()), state="readonly", width=22)
        cb.pack(side="left", padx=4)
        cb.bind("<<ComboboxSelected>>", lambda e: self._show_setup(self.backend_var.get()))
        make_button(row, "📖 Show guide", lambda: self._show_setup(self.backend_var.get()), "neutral").pack(side="left", padx=4)
        make_button(row, "✅ Use suggested model", self._apply_suggestion, "success").pack(side="left", padx=4)

        p2 = make_panel(f, "📖 Step 2: Read the guide")
        p2.pack(fill="both", expand=True, padx=12, pady=10)
        self.setup_text = tk.Text(p2, wrap="word", bg=INPUT_BG, fg=FG, relief="flat", padx=12, pady=12, font=("Consolas", 10))
        self.setup_text.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        p3 = make_panel(f, "⚡ Step 3: Copy & Run commands")
        p3.pack(fill="x", padx=12, pady=10)
        self.cmd_frame = tk.Frame(p3, bg=CARD)
        self.cmd_frame.pack(fill="x", padx=12, pady=(0, 12))
        self._show_setup(self.backend_var.get())

        p4 = make_panel(f, "💡 Beginner tips")
        p4.pack(fill="x", padx=12, pady=10)
        tips = tk.Text(p4, height=6, wrap="word", bg=INPUT_BG, fg=MUTED, relief="flat", padx=12, pady=8, font=("Segoe UI", 10))
        tips.pack(fill="x", padx=12, pady=(0, 12))
        tips.insert("1.0", "- Start with Ollama if you are new (no compiling needed).\n"
                           "- Use llama.cpp for maximum speed and control.\n"
                           "- Copy a command, then Run it to open a new terminal automatically.\n"
                           "- Out of memory? Drop -ub 1024 and --moe-cache-mib 2048 from the command.\n"
                           "- Low on RAM? Add --load-mode mmap.\n"
                           "- Set -t to about half your CPU cores for MoE models.")
        tips.config(state="disabled")

    def _show_setup(self, name):
        guide = SETUPS.get(name, "")
        if platform.system() == "Darwin":
            guide += ("\n\nmacOS notes:\n"
                      "  - Apple Silicon uses Metal (build with -DGGML_METAL=ON).\n"
                      "  - Unified memory = RAM acts as VRAM, so bigger models fit.\n"
                      "  - Ollama/LM Studio installers are drag-and-drop friendly.")
        guide = f"Suggested model for your hardware: {auto_suggest_model(self.hw)}\n\n" + guide
        self.setup_text.config(state="normal")
        self.setup_text.delete("1.0", "end")
        self.setup_text.insert("1.0", guide)
        self.setup_text.config(state="disabled")
        for w in self.cmd_frame.winfo_children():
            w.destroy()
        cmds = get_commands(name)
        self.current_commands = cmds
        if not cmds:
            tk.Label(self.cmd_frame, text="No runnable commands for this backend.", bg=CARD, fg=MUTED).pack(anchor="w")
            return
        for i, (label, cmd) in enumerate(cmds):
            r = tk.Frame(self.cmd_frame, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
            r.pack(fill="x", pady=4, padx=2)
            tk.Label(r, text=label + ":", bg=CARD, fg=WARN, font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=8, pady=(6, 2))
            t = tk.Text(r, height=3, wrap="word", bg=INPUT_BG, fg=ACCENT, relief="flat", padx=6, pady=4, font=("Consolas", 9))
            t.insert("1.0", cmd)
            t.config(state="disabled")
            t.pack(fill="x", padx=8, pady=2)
            bb = tk.Frame(r, bg=CARD)
            bb.pack(anchor="w", padx=8, pady=(2, 6))
            make_button(bb, "📋 Copy", lambda c=cmd: copy_to_clipboard(self.root, c), "neutral").pack(side="left", padx=2)
            make_button(bb, "▶ Run", lambda c=cmd, t=label: _run_command(c, t, self.root), "primary").pack(side="left", padx=2)

    def _build_models(self):
        f = self.tab_models
        p = make_panel(f, "Model ladder (under 40B params + flash models)")
        p.pack(fill="both", expand=True, padx=12, pady=10)
        cols = ("Model", "Type", "VRAM", "Notes")
        tree = ttk.Treeview(p, columns=cols, show="headings", height=12)
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=170 if c != "Notes" else 300)
        for row in self.all_models:
            tree.insert("", "end", values=row)
        sb = ttk.Scrollbar(p, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        tree.pack(side="left", fill="both", expand=True, padx=(12, 0), pady=(0, 12))
        sb.pack(side="right", fill="y", padx=(0, 12), pady=(0, 12))

        p2 = make_panel(f, "VRAM tiers")
        p2.pack(fill="x", padx=12, pady=10)
        cols2 = ("VRAM", "Recommended model", "Notes")
        tree2 = ttk.Treeview(p2, columns=cols2, show="headings", height=10)
        for c in cols2:
            tree2.heading(c, text=c)
            tree2.column(c, width=90 if c == "VRAM" else 280)
        for row in VRAM_TIERS:
            tree2.insert("", "end", values=row)
        # highlight the tier matching this machine's GPU
        try:
            vram = float(self.hw.get("vram_gb", 0))
            best = None
            for i, row in enumerate(VRAM_TIERS):
                t = row[0].replace("+", "").replace(" GB", "")
                if vram >= float(t):
                    best = i
            if best is not None:
                tree2.selection_set(tree2.get_children()[best])
                tree2.see(tree2.get_children()[best])
                tk.Label(p2, text=f"⬆️ Your {vram} GB GPU matches the highlighted row below",
                         bg=CARD, fg=SUCCESS, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=14, pady=(4, 0))
        except Exception:
            pass
        sb2 = ttk.Scrollbar(p2, orient="vertical", command=tree2.yview)
        tree2.configure(yscrollcommand=sb2.set)
        tree2.pack(side="left", fill="both", expand=True, padx=(12, 0), pady=(0, 12))
        sb2.pack(side="right", fill="y", padx=(0, 12), pady=(0, 12))

        p3 = make_panel(f, "Online model data (HuggingFace)")
        p3.pack(fill="x", padx=12, pady=10)
        make_button(p3, "🔄 Update models (online)", self._update_models_online, "primary").pack(anchor="w", padx=12, pady=(0, 8))
        self.online_text = tk.Text(p3, height=7, wrap="word", bg=INPUT_BG, fg=ACCENT, relief="flat", padx=10, pady=8, font=("Consolas", 9))
        self.online_text.pack(fill="x", padx=12, pady=(0, 12))
        self.online_text.insert("1.0", "Click 'Update models (online)' to fetch latest models from HuggingFace (incl. uncensored).")
        self.online_text.config(state="disabled")

    def _build_online(self):
        f = self.tab_online
        p = make_panel(f, "Online model update (HuggingFace)")
        p.pack(fill="x", padx=12, pady=10)
        row = tk.Frame(p, bg=CARD)
        row.pack(fill="x", padx=12, pady=(0, 8))
        make_button(row, "🔄 Update models (online)", self._update_models_online, "primary").pack(side="left", padx=4)
        make_button(row, "📋 Show updated models", self._show_updated_models, "neutral").pack(side="left", padx=4)
        self.online_status = tk.Label(row, text="Status: idle", bg=CARD, fg=MUTED, font=("Segoe UI", 10))
        self.online_status.pack(side="left", padx=10)
        p_choice = make_panel(f, "Choose model (from online data)")
        p_choice.pack(fill="x", padx=12, pady=10)
        cr = tk.Frame(p_choice, bg=CARD)
        cr.pack(fill="x", padx=12, pady=(0, 8))
        self.online_choice = ttk.Combobox(cr, values=[], width=46, state="readonly")
        self.online_choice.pack(side="left", padx=4)
        make_button(cr, "📋 Show details", self._show_online_choice, "neutral").pack(side="left", padx=4)
        self.online_choice_detail = tk.Text(p_choice, height=4, wrap="word", bg=INPUT_BG, fg=FG, relief="flat", padx=10, pady=8, font=("Consolas", 9))
        self.online_choice_detail.pack(fill="x", padx=12, pady=(0, 12))
        self.online_choice_detail.insert("1.0", "Select a model above and click 'Show details'.")
        self.online_choice_detail.config(state="disabled")

        p2 = make_panel(f, "Updated models")
        p2.pack(fill="both", expand=True, padx=12, pady=10)
        cols = ("Model", "VRAM", "Downloads", "Likes", "Tags")
        self.online_tree = ttk.Treeview(p2, columns=cols, show="headings", height=16)
        for c in cols:
            self.online_tree.heading(c, text=c)
            self.online_tree.column(c, width=300 if c == "Model" else 150 if c == "VRAM" else 95)
        sb3 = ttk.Scrollbar(p2, orient="vertical", command=self.online_tree.yview)
        self.online_tree.configure(yscrollcommand=sb3.set)
        self.online_tree.pack(side="left", fill="both", expand=True, padx=(12, 0), pady=(0, 12))
        sb3.pack(side="right", fill="y", padx=(0, 12), pady=(0, 12))
        self.online_text2 = tk.Text(p2, height=6, wrap="word", bg=INPUT_BG, fg=ACCENT, relief="flat", padx=10, pady=8, font=("Consolas", 9))
        self.online_text2.pack(fill="x", padx=12, pady=(0, 12))
        self.online_text2.insert("1.0", "Fetched models will appear here.")
        self.online_text2.config(state="disabled")

    def _show_updated_models(self):
        data = fetch_models_online()
        self.online_tree.delete(*self.online_tree.get_children())
        if not data:
            self.online_status.config(text="Status: failed (offline?)", fg=ERR)
            return
        for m in data:
            self.online_tree.insert("", "end", values=(m["id"], estimate_vram(m["id"]), m["downloads"], m.get("likes", 0), m["tags"]))
        self.online_status.config(text=f"Status: {len(data)} models fetched", fg=SUCCESS)

    def _update_models_online(self):
        self.online_status.config(text="Status: fetching...", fg=WARN)
        self.online_text.config(state="normal")
        self.online_text.delete("1.0", "end")
        self.online_text.insert("1.0", "Fetching models from HuggingFace (background)...")
        self.online_text.config(state="disabled")

        def worker():
            data = fetch_models_online()
            self.root.after(0, lambda d=data: self._finish_online_update(d))

        threading.Thread(target=worker, daemon=True).start()

    def _finish_online_update(self, data):
        if not data:
            self.online_status.config(text="Status: failed (offline?)", fg=ERR)
            self.online_text.config(state="normal")
            self.online_text.delete("1.0", "end")
            self.online_text.insert("1.0", "Failed to fetch (offline or error). Keeping bundled list.")
            self.online_text.config(state="disabled")
            return
        self.online_status.config(text=f"Status: {len(data)} models fetched", fg=SUCCESS)
        self.online_text.config(state="normal")
        self.online_text.delete("1.0", "end")
        lines = [f"{m['id']}  (downloads: {m['downloads']})" for m in data]
        self.online_text.insert("1.0", "\n".join(lines))
        self.online_text.config(state="disabled")
        # update choice combobox
        if hasattr(self, "online_choice"):
            self.online_choice["values"] = [m["id"] for m in data]
            if data:
                self.online_choice.set(data[0]["id"])
        # update tree
        self.online_tree.delete(*self.online_tree.get_children())
        for m in data:
            self.online_tree.insert("", "end", values=(m["id"], estimate_vram(m["id"]), m["downloads"], m.get("likes", 0), m["tags"]))
        # merge into app model database
        self._merge_online_models(data)

    def _merge_online_models(self, data):
        existing = {m[0] for m in self.all_models}
        added = 0
        for m in data:
            name = m["id"].split("/")[-1]
            if name in existing:
                continue
            existing.add(name)
            note = f"HF: {m['id']} • {m['downloads']:,} dl"
            if m.get("likes"):
                note += f" • {m['likes']:,} likes"
            self.all_models.append((name, "🌐 Live", estimate_vram(m["id"]), note))
            added += 1
        # refresh models treeview (widgets may not exist yet during startup)
        if hasattr(self, "tab_models"):
            for w in self.tab_models.winfo_children():
                for c in w.winfo_children():
                    if isinstance(c, ttk.Treeview):
                        c.delete(*c.get_children())
                        for row in self.all_models:
                            c.insert("", "end", values=row)
        if hasattr(self, "online_status"):
            self.online_status.config(text=f"Status: {len(data)} fetched, {added} new added to DB", fg=SUCCESS)
        return added

    def _show_online_choice(self):
        mid = self.online_choice.get()
        if not mid:
            return
        self.online_choice_detail.config(state="normal")
        self.online_choice_detail.delete("1.0", "end")
        vram = estimate_vram(mid)
        self.online_choice_detail.insert(
            "1.0",
            f"Model: {mid}\n"
            f"Estimated VRAM: {vram}\n\n"
            f"Search HuggingFace for GGUF variants with this name, then run it with "
            f"llama-server or 'ollama pull' (for Ollama-compatible names).",
        )
        self.online_choice_detail.config(state="disabled")

    def _build_cmd(self):
        f = self.tab_cmd
        p = make_panel(f, "Starter command (llama-server)")
        p.pack(fill="x", padx=12, pady=10)
        self.cmd_text = tk.Text(p, height=5, wrap="word", bg=INPUT_BG, fg=ACCENT, relief="flat", padx=10, pady=8, font=("Consolas", 10))
        self.cmd_text.insert("1.0", COMMAND)
        self.cmd_text.config(state="disabled")
        self.cmd_text.pack(fill="x", padx=12, pady=(0, 8))
        bb = tk.Frame(p, bg=CARD)
        bb.pack(fill="x", padx=12, pady=(0, 12))
        make_button(bb, "📋 Copy command", lambda: copy_to_clipboard(self.root, COMMAND), "neutral").pack(side="left", padx=4)
        make_button(bb, "▶ Run command", lambda: _run_command(COMMAND, "primary", self.root), "primary").pack(side="left", padx=4)

        p2 = make_panel(f, "Notes")
        p2.pack(fill="x", padx=12, pady=10)
        notes = tk.Text(p2, height=8, wrap="word", bg=INPUT_BG, fg=MUTED, relief="flat", padx=10, pady=8, font=("Consolas", 9))
        notes.insert("1.0", "\n".join(f"- {n}" for n in NOTES))
        notes.config(state="disabled")
        notes.pack(fill="x", padx=12, pady=(0, 12))

        p3 = make_panel(f, "Customize choice")
        p3.pack(fill="x", padx=12, pady=10)
        cz = tk.Frame(p3, bg=CARD)
        cz.pack(fill="x", padx=12, pady=(0, 12))
        tk.Label(cz, text="Model:", bg=CARD, fg=FG, font=("Segoe UI", 10)).pack(side="left", padx=4)
        self.model_var = tk.StringVar(value=auto_suggest_model(self.hw))
        ttk.Combobox(cz, textvariable=self.model_var, values=[m[0] for m in MODELS], width=28).pack(side="left", padx=4)
        tk.Label(cz, text="Backend:", bg=CARD, fg=FG, font=("Segoe UI", 10)).pack(side="left", padx=4)
        self.backend_var2 = tk.StringVar(value="llama.cpp")
        ttk.Combobox(cz, textvariable=self.backend_var2, values=list(SETUPS.keys()), width=16).pack(side="left", padx=4)
        make_button(cz, "✅ Apply suggestion", self._apply_suggestion, "success").pack(side="left", padx=4)

    def _build_about(self):
        f = self.tab_about
        p = make_panel(f, "About")
        p.pack(fill="both", expand=True, padx=12, pady=10)
        info = tk.Text(p, wrap="word", bg=INPUT_BG, fg=FG, relief="flat", padx=12, pady=12, font=("Segoe UI", 10))
        info.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        text = (
            "Local AI Model Picker\n"
            "Version: 1.0\n\n"
            "Creator: Nyi Min\n\n"
            "Based on the YouTube video:\n"
            '"What\'s the Best AI Model Your GPU Can Actually Run? 4GB to 16GB VRAM"\n'
            "by Codacus\n"
            f"{VIDEO_URL}\n\n"
            "Credit & Reference:\n"
            "- Codacus (YouTube) - original VRAM ladder research\n"
            "  " + VIDEO_URL + "\n"
            "- HuggingFace - live model data (incl. uncensored)\n"
            "- llama.cpp, Ollama, LM Studio, Cline Desktop - backends\n\n"
            "Features:\n"
            "- Hardware detection (GPU/VRAM/RAM/CPU)\n"
            "- Auto-suggest model based on your hardware\n"
            "- Setup guides for 7 backends\n"
            "- Live model data fetch from HuggingFace\n"
            "- Copy & Run commands in new terminal\n"
            "- Native desktop GUI (no web, no TUI)\n"
        )
        info.insert("1.0", text)
        info.config(state="disabled")

    def _suggest_updated(self):
        m = auto_suggest_model(self.hw)
        self.suggest_label.config(text=f"Suggested: {m}")
        self.rec_text.config(state="normal")
        self.rec_text.delete("1.0", "end")
        self.rec_text.insert("1.0", recommend(self.hw) + f"\n\n>>> Auto-suggested (updated): {m}")
        self.rec_text.config(state="disabled")
        self.model_var.set(m)

    def _apply_suggestion(self):
        m = auto_suggest_model(self.hw)
        self.model_var.set(m)
        messagebox.showinfo("Suggestion", f"Suggested model: {m}\nBackend: {self.backend_var2.get()}")

    def _update_hw(self):
        self.hw = detect_hardware()
        self.home_gpu.config(text=f"GPU: {self.hw['gpu']}")
        self.home_vram.config(text=f"VRAM: {self.hw['vram_gb']} GB")
        self.home_ram.config(text=f"RAM: {self.hw['ram_gb']} GB")
        quick = ("Quick Start\n\n"
                 "1. Check your hardware  ->  Hardware tab (auto-detected on load)\n"
                 "2. Get a recommendation  ->  Recommend tab\n"
                 "3. Pick a backend + run   ->  Setup tab (copy/run commands)\n\n"
                 f"Your machine: {self.hw['gpu']} / {self.hw['vram_gb']} GB VRAM / {self.hw['ram_gb']} GB RAM\n"
                 f"Auto-suggested model: {auto_suggest_model(self.hw)}\n")
        self.home_quick.config(state="normal")
        self.home_quick.delete("1.0", "end")
        self.home_quick.insert("1.0", quick)
        self.home_quick.config(state="disabled")
        # suggestions
        vram = self.hw["vram_gb"]
        ram = self.hw["ram_gb"]
        sugg = []
        sugg.append(f"Your GPU has {vram} GB VRAM and {ram} GB RAM.")
        if ram < 16:
            sugg.append("Consider upgrading RAM to 32 GB to run more models.")
        if vram < 8:
            sugg.append("A GPU with 8+ GB VRAM unlocks K2 Horizon and longer context.")
        sugg.append("Use --fit-target 512 to fit MoE models on small VRAM.")
        sugg.append("Keep -ctk/-ctv q8_0 to halve context memory.")
        sugg.append("Set threads to ~half your CPU cores for MoE models.")
        if ram >= 64:
            sugg.append("With 64 GB+ RAM, try Strata/Maya for 763B models.")
        self.sugg_text.config(state="normal")
        self.sugg_text.delete("1.0", "end")
        self.sugg_text.insert("1.0", "\n".join("- " + s for s in sugg))
        self.sugg_text.config(state="disabled")
        vals = {
            "os": self.hw["os"],
            "cpu": self.hw["cpu"],
            "ram": f"{self.hw['ram_gb']} GB",
            "gpu": self.hw["gpu"],
            "vram": f"{self.hw['vram_gb']} GB ({self.hw['vram_mib']} MiB)",
        }
        for k, v in vals.items():
            self.hw_labels[k].config(text=v)
        self.rec_text.config(state="normal")
        self.rec_text.delete("1.0", "end")
        self.rec_text.insert("1.0", recommend(self.hw))
        self.rec_text.config(state="disabled")
        try:
            self.suggest_label.config(text=f"Suggested: {auto_suggest_model(self.hw)}")
        except Exception:
            pass


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
