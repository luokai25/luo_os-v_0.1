<div align="center">

# 𝗟𝗨𝗢 𝗢𝗦 𝘃𝟭.𝟬

**The AI-Native Operating System — Runs in Any Browser**

*Created by **Luo Kai** (luokai25 · luokai0)*

</div>

---

## What is LuoOS?

LuoOS is a **full computer that runs in your browser** — like Zed OS / JSLinux, but powered by a state-of-the-art local AI. No cloud. No API keys. Everything on YOUR machine.

**LUOKAI** is the AI core: always listening, always learning, always improving itself.

## Quick Start

```bash
# 1. Clone
git clone https://github.com/luokai25/luo_os-v_0.1
cd luo_os-v_0.1

# 2. Start AI (for full intelligence)
ollama serve &
ollama pull mistral

# 3. Run LuoOS
./start.sh      # Mac/Linux
start.bat       # Windows

# 4. Open in browser
# http://localhost:3000
```

> **Or just open `index.html` in your browser for the sandbox OS** (no AI features without server)

## Features

| Feature | Details |
|---------|---------|
| 🖥️ **Full Desktop OS** | Runs entirely in browser. Taskbar, sidebar, window manager, drag/resize |
| 🤖 **LUOKAI AI** | Always-on agent with voice, vision, code execution, web browsing |
| 🎤 **24/7 Voice** | Say "Luo" anywhere — LUOKAI wakes and responds without pressing anything |
| 🔄 **Co-Evolution** | AI gets harder benchmarks as it improves → never stops getting smarter |
| 💻 **Luo Terminal** | Linux + Windows commands + custom `luo` commands |
| 🌐 **Luo Browser** | Built-in web browser |
| 📁 **Luo Files** | Full file manager |
| 💻 **Luo Code** | Code editor with AI assistance + execution |
| 🎨 **Luo Studio** | AI image/video/website generation |
| 👁️ **Luo Vision** | Object detection, image captioning, VQA |
| ⚙️ **Luo Settings** | 200+ customizable settings |
| 🎵 **Luo Music** | YouTube streaming, local playback |
| 📝 **Luo Notes** | Notes with AI improvement |
| 🔧 **4,146 Skills** | 20 domains: programming, AI, science, business, health... |

## Architecture

```
LuoOS Browser Sandbox          Real Machine Layer
━━━━━━━━━━━━━━━━━━━━━━━━      ━━━━━━━━━━━━━━━━━━━━
index.html                     luo_server.py (Flask)
├── Desktop (JS)         ←→    ├── LUOKAI Agent
├── Window Manager             ├── Ollama (Mistral/LLaMA)
├── 11 Apps                    ├── Voice Daemon (24/7)
├── Luo Terminal               ├── Co-Evolution Engine
└── File Manager               └── 4,146 Skills
```

## The Co-Evolution Algorithm

LuoOS includes a unique self-improvement engine:

```
LUOKAI improves → generates harder tests → passes them → even harder tests → ∞
```

1. **CHALLENGER** generates increasingly hard tests
2. **LUOKAI** solves them using Tree-of-Thought reasoning
3. **EVALUATOR** scores answers 0-10
4. Failures become **training data** (Axolotl + PEFT LoRA)
5. Difficulty increases as scores improve → **never plateaus**

## Voice — Always On

```
Mic → VAD → "Luo" detected → LUOKAI responds → speaks back → back to listening
No button press needed. Works 24/7.
```

## Apps

| App | Name | Description |
|-----|------|-------------|
| 🤖 | **Luo AI** | LUOKAI chat interface |
| 🌐 | **Luo Browser** | Web browser |
| ⌨️ | **Luo Terminal** | Shell with custom `luo` commands |
| 📁 | **Luo Files** | File manager |
| 💻 | **Luo Code** | AI code editor |
| 📝 | **Luo Notes** | Smart notes |
| 🎨 | **Luo Studio** | AI media creator |
| 👁️ | **Luo Vision** | Computer vision |
| 🎵 | **Luo Music** | Music player |
| ⚙️ | **Luo Settings** | OS settings |
| ℹ️ | **About** | System info |

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| Ctrl+L | Open LUOKAI |
| Ctrl+T | Open Terminal |
| Ctrl+B | Open Browser |
| Ctrl+E | Open Code Editor |
| Ctrl+F | Open Files |

## Legal

**© 2025 Luo Kai (luokai25). All rights reserved.**

LuoOS, LUOKAI, Luo AI, Luo Browser, Luo Terminal, Luo Files, Luo Studio, Luo Vision, Luo Music, Luo Notes, Luo Code, Luo Settings — all names, concepts, and implementations are intellectual property of Luo Kai.

Built with ❤️ from 60+ open-source projects. See [SOURCES.md](SOURCES.md).
