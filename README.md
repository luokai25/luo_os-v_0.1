# Luo OS v0.1
### A Free Operating System for Humans and AI Agents
*Created by Luo Kai (luokai25)*

## Vision
Luo OS is a free, open-source operating system built for both humans and AI agents.
Every tool, every feature, forever free. No paywalls. No limits.

## Architecture
- **Kernel**: Linux-based
- **UI**: Full GUI desktop with windows and mouse support
- **AI Core**: Local AI agent built into the OS — not an app, part of the system
- **Compatibility**: Run Windows apps natively via Wine layer
- **Shell**: Bash + PowerShell

## Folder Structure
- `kernel/`   — Linux-based kernel patches and config
- `ui/`       — Window manager and desktop environment
- `ai_core/`  — Local AI agent daemon
- `compat/`   — Windows compatibility layer
- `shell/`    — Shell environment
- `drivers/`  — Hardware drivers
- `apps/`     — Built-in free applications
- `docs/`     — Architecture and vision documentation

## Principles
1. Free for everyone — humans and AI agents
2. AI is part of the OS, not an add-on
3. Open source forever
4. Built by Luo Kai

## Status
🚧 v0.1 — In active development

## How to Run Luo OS v0.1

### Requirements
```bash
pip install tkinter
```

### Launch
```bash
python3 luo_os.py
```

### Boot Modes
- **Human Mode** — Full GUI desktop
- **AI Agent Mode** — AI core terminal
- **Safe Mode** — Minimal shell

## File Structure
```
luo_os-v_0.1/
├── luo_os.py        ← Main launcher (start here)
├── kernel/          ← Kernel config
├── ui/              ← Desktop GUI
├── ai_core/         ← Local AI daemon
├── compat/          ← Windows/Android compat
├── shell/           ← Luo shell
├── drivers/         ← Hardware drivers
├── apps/            ← Built-in free apps
└── docs/            ← Architecture + roadmap
```
