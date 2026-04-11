<div align="center">

<img src="https://img.shields.io/badge/LuoOS-v0.1-00c8ff?style=for-the-badge&logo=linux&logoColor=white"/>
<img src="https://img.shields.io/badge/AI--Native-OS-7c3aed?style=for-the-badge&logo=openai&logoColor=white"/>
<img src="https://img.shields.io/badge/Runs%20in-Browser-00ff9d?style=for-the-badge&logo=googlechrome&logoColor=black"/>
<img src="https://img.shields.io/badge/License-Proprietary-ff4d6d?style=for-the-badge"/>

<br/><br/>

```
  ██╗     ██╗   ██╗ ██████╗      ██████╗ ███████╗
  ██║     ██║   ██║██╔═══██╗    ██╔═══██╗██╔════╝
  ██║     ██║   ██║██║   ██║    ██║   ██║███████╗
  ██║     ██║   ██║██║   ██║    ██║   ██║╚════██║
  ███████╗╚██████╔╝╚██████╔╝    ╚██████╔╝███████║
  ╚══════╝ ╚═════╝  ╚═════╝      ╚═════╝ ╚══════╝
```

# LuoOS — v0.1

**The AI-Native Operating System. Runs entirely in your browser.**

*Designed and built by **Luo Kai** · [luokai25](https://github.com/luokai25)*

<br/>

[**Quick Start**](#-quick-start) · [**Features**](#-features) · [**Architecture**](#-architecture) · [**Apps**](#-built-in-apps) · [**API**](#-api-reference) · [**Roadmap**](#-roadmap)

</div>

---

## What is LuoOS?

LuoOS is a **complete desktop operating system that runs inside any modern web browser** — no installation, no virtual machine, no cloud dependency. It combines a fully functional browser-based desktop environment with **LUOKAI**, a deeply integrated AI agent that can control the OS, execute code, browse the web, process images, speak, and continuously improve itself.

Unlike traditional web apps with bolted-on AI features, LuoOS is designed **AI-first from the ground up** — the AI is the operating system.

```
Traditional OS + AI:    [OS] → [App] → [AI plugin]     ← AI is optional
LuoOS:                  [AI] ← [OS built around it]     ← AI is the core
```

---

## ✨ Features

| Category | Capability |
|----------|-----------|
| 🖥️ **Desktop Environment** | Full windowed OS in the browser — taskbar, sidebar, drag/resize windows, multi-app |
| 🤖 **LUOKAI AI Agent** | ReAct-based reasoning agent with planning, reflection, and tool use |
| 🎤 **Always-On Voice** | 24/7 wake-word detection — say "Luo" anywhere, no button press needed |
| 🔄 **Co-Evolution Engine** | Self-improvement loop — LUOKAI generates harder tests as it gets smarter |
| 💻 **Luo VS Code** | Full VS Code in the browser via code-server, shared workspace with Luo Files |
| 🧠 **Vector Memory** | Semantic long-term memory via ChromaDB — LUOKAI remembers across sessions |
| 🌐 **Luo Browser** | Built-in web browser with AI integration |
| 📁 **Luo Files** | Full file manager, synced with VS Code workspace |
| ⌨️ **Luo Terminal** | Shell with Linux commands + custom `luo` AI commands |
| 💻 **Luo Code** | Inline code editor with AI assistance and execution |
| 🎨 **Luo Studio** | AI-powered media and content creation |
| 👁️ **Luo Vision** | Object detection, image captioning, visual Q&A |
| 🎵 **Luo Music** | Audio playback and streaming |
| 📝 **Luo Notes** | Smart notes with AI improvement |
| 🔧 **4,146 Skills** | Curated skill library across 20 domains |
| 🐳 **Docker Ready** | Full containerized deployment |
| ⚙️ **Systemd Services** | Production-grade service management on Linux |

---

## 🚀 Quick Start

### Option 1 — Instant (no AI)

```bash
git clone https://github.com/luokai25/luo_os-v_0.1
cd luo_os-v_0.1

# Open the desktop OS directly in browser
open index.html        # macOS
xdg-open index.html    # Linux
# or drag index.html into any browser
```

### Option 2 — Full Stack (with LUOKAI AI)

```bash
git clone https://github.com/luokai25/luo_os-v_0.1
cd luo_os-v_0.1

# Install Python dependencies
pip install -r requirements.txt

# Start a local LLM (Ollama required for AI)
ollama serve &
ollama pull mistral        # Fast and capable (~4GB)
# ollama pull llama3       # Alternative
# ollama pull qwen2        # Multilingual

# Launch LuoOS
./start.sh                 # Mac / Linux
start.bat                  # Windows

# Open in browser → http://localhost:3000
```

### Option 3 — Docker

```bash
git clone https://github.com/luokai25/luo_os-v_0.1
cd luo_os-v_0.1

docker build -t luo_os .
docker run -p 3000:3000 -p 8080:8080 luo_os

# Open → http://localhost:3000
```

### Option 4 — CLI Only

```bash
pip install flask flask-cors requests

python3 luo_cli.py chat       # Interactive AI chat
python3 luo_cli.py server     # Web interface only
python3 luo_cli.py evolution  # Self-improvement mode
python3 luo_cli.py voice      # Voice interface
python3 luo_cli.py tui        # Rich terminal UI
```

---

## 🏗️ Architecture

LuoOS is structured in layered components — each independently useful, all deeply integrated.

```
┌──────────────────────────────────────────────────────────────────────┐
│                         LuoOS Browser Desktop                        │
│    index.html  ·  Window Manager  ·  12 Built-in Apps  ·  Sidebar   │
├──────────────────────────────────────────────────────────────────────┤
│                         luo_server.py  (Flask)                       │
│   /api/chat    /api/execute    /api/fs/*    /api/vscode/*            │
│   /api/voice   /api/evolution  /api/skills  /api/memory              │
├────────────────────────┬─────────────────────────────────────────────┤
│     LUOKAI Core        │         Supporting Systems                  │
│  ┌─────────────────┐   │   ┌──────────────┐  ┌────────────────────┐ │
│  │  ReAct Agent    │   │   │ Vector Memory│  │  Co-Evolution      │ │
│  │  (Reason+Act)   │   │   │  (ChromaDB)  │  │  Engine            │ │
│  └────────┬────────┘   │   └──────────────┘  └────────────────────┘ │
│           │            │   ┌──────────────┐  ┌────────────────────┐ │
│  ┌────────▼────────┐   │   │ Voice Layer  │  │  Skills Library    │ │
│  │  Tool Executor  │   │   │  (24/7 STT)  │  │  (4,146 entries)   │ │
│  │  (30+ tools)    │   │   └──────────────┘  └────────────────────┘ │
│  └─────────────────┘   │                                             │
├────────────────────────┴─────────────────────────────────────────────┤
│                     Local LLM Layer (Ollama)                         │
│              mistral  ·  llama3  ·  qwen2  ·  codellama              │
├──────────────────────────────────────────────────────────────────────┤
│              VS Code Layer  (code-server · port 8080)                │
│         ~/luo_workspace  ·  Shared with Luo Files app                │
└──────────────────────────────────────────────────────────────────────┘
```

### Core Components

#### LUOKAI Agent (`luokai/core/`)
The primary AI reasoning engine. Uses a **ReAct** (Reason + Act) loop: LUOKAI thinks through a problem, selects a tool, observes the result, and iterates until it has a complete answer. Supports streaming responses via Server-Sent Events.

#### Vector Memory (`luo_agent/memory/`)
Semantic long-term memory using ChromaDB. Memories are stored as embeddings and recalled by meaning, not keyword. The **autoDream** background process periodically consolidates memories — removing duplicates, resolving contradictions, and promoting patterns into stable long-term knowledge.

#### Tool Executor (`luo_agent/tools/`)
Over 30 tools across categories: filesystem operations, shell execution, web search and fetch, system introspection, Docker management, code analysis, and utilities. Tools are permission-gated — write/execute operations require explicit authorization.

#### Co-Evolution Engine (`luokai/evolution/`)
A closed-loop self-improvement system:
1. **CHALLENGER** generates a test at the current difficulty level
2. **LUOKAI** solves it using Tree-of-Thought reasoning
3. **EVALUATOR** scores the response 0–10
4. Poor responses feed back as training signals
5. As scores improve, difficulty increases — the ceiling always rises

#### Voice Layer (`luokai/voice/`)
Always-on speech interface with wake-word detection. Uses Whisper for offline speech-to-text and edge-tts / pyttsx3 for text-to-speech. No cloud. No button press.

#### VS Code Integration (`vscode/`)
Full Visual Studio Code running in the browser via code-server. Shares `~/luo_workspace` with the Luo Files app — files created in VS Code are instantly visible in the file manager and vice versa. Auto-starts with LuoOS.

---

## 📱 Built-in Apps

| Icon | App | Shortcut | Description |
|------|-----|----------|-------------|
| 🤖 | **LUOKAI** | `Ctrl+L` | Primary AI agent chat interface with streaming responses |
| 🌐 | **Luo Browser** | `Ctrl+B` | Built-in web browser with iframe navigation |
| ⌨️ | **Luo Terminal** | `Ctrl+T` | Shell with Linux commands + `luo <query>` AI integration |
| 📁 | **Luo Files** | `Ctrl+F` | File manager synced with VS Code workspace |
| 💻 | **Luo Code** | `Ctrl+E` | Inline code editor — Python, JS, Bash, HTML — with AI assist |
| 🖥️ | **Luo VS Code** | `Ctrl+V` | Full VS Code via code-server in an iframe window |
| 📝 | **Luo Notes** | — | Smart notes with AI rewriting and improvement |
| 🎨 | **Luo Studio** | — | AI-powered image, video, and website generation |
| 👁️ | **Luo Vision** | — | Object detection, captioning, visual question answering |
| 🎵 | **Luo Music** | — | Audio player and streaming |
| ⚙️ | **Luo Settings** | — | 200+ configurable system settings |
| ℹ️ | **About LuoOS** | — | System info, memory stats, agent status |

---

## 🖥️ Luo VS Code

LuoOS ships with a complete VS Code integration powered by [code-server](https://github.com/coder/code-server).

### Setup

```bash
# Install code-server (first time only, ~2 minutes)
bash vscode/install_code_server.sh

# Start LuoOS — code-server auto-starts with it
python3 luo_server.py

# Then click the VS Code icon in the sidebar (or press Ctrl+V)
```

### What's included

- **Shared workspace** at `~/luo_workspace` — visible in both VS Code and Luo Files
- **Pre-configured settings** — JetBrains Mono font, autosave, bracket colorization
- **Pre-installed extensions** — Python, ESLint, Prettier, GitLens, Code Runner, Material Icons
- **API control** — start, stop, and check status from the LuoOS backend

### Management

```bash
# CLI process manager
bash vscode/code_server_manager.sh start    # Start code-server
bash vscode/code_server_manager.sh stop     # Stop
bash vscode/code_server_manager.sh status   # Check running/port/PID
bash vscode/code_server_manager.sh restart  # Restart
```

### Architecture

```
LuoOS Desktop (port 3000)
    └── VS Code Window
            └── iframe → code-server (port 8080)
                            └── ~/luo_workspace
                                    └── (also mounted in Luo Files)
```

---

## 📡 API Reference

When running `luo_server.py`, the following REST endpoints are available at `http://localhost:3000`:

### AI & Chat

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/chat` | Send a message to LUOKAI (standard or streaming) |
| `POST` | `/api/chat/stream` | SSE streaming chat endpoint |
| `GET`  | `/api/status` | Agent status, model info, memory count |
| `GET`  | `/api/models` | List available Ollama models |
| `POST` | `/api/models/switch` | Switch the active model |

### Execution & Search

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/execute` | Execute code (Python, Bash, JS) |
| `POST` | `/api/search` | Web search |

### Memory & Skills

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/api/memory` | Retrieve stored memories |
| `POST` | `/api/memory/recall` | Semantic search over memories |
| `GET`  | `/api/skills` | List the skills library |
| `POST` | `/api/skills/<name>` | Invoke a named skill |

### Filesystem

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/fs/read` | Read a file |
| `POST` | `/api/fs/write` | Write a file |
| `POST` | `/api/fs/ls` | List a directory |

### Voice

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/voice/start` | Start the 24/7 voice listener |
| `POST` | `/api/voice/stop` | Stop voice listener |
| `GET`  | `/api/voice/status` | Check voice state |

### Evolution

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/evolution/start` | Start the co-evolution engine |
| `GET`  | `/api/evolution/stats` | Get current evolution metrics |

### VS Code

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/api/vscode/status` | Installed?, running?, port, workspace path |
| `POST` | `/api/vscode/start` | Launch code-server |
| `POST` | `/api/vscode/stop` | Stop code-server |
| `POST` | `/api/vscode/install` | Run install script in background |

---

## 📂 Project Structure

```
luo_os-v_0.1/
│
├── index.html                  # Browser desktop OS (all apps, window manager)
├── luo_server.py               # Main Flask backend (all API routes)
├── luo_cli.py                  # Unified CLI entry point
├── luo_os.py                   # Tkinter launcher (optional)
├── requirements.txt            # Python dependencies
│
├── luokai/                     # LUOKAI AI core
│   ├── core/
│   │   ├── luokai_agent.py     # Base agent
│   │   └── react_agent.py      # ReAct reasoning agent (streaming)
│   ├── voice/
│   │   └── always_on.py        # 24/7 wake-word voice interface
│   ├── evolution/
│   │   └── coevo.py            # Co-evolution self-improvement engine
│   ├── memory/                 # Memory interfaces
│   └── skills/                 # Skills library (4,146 entries)
│
├── luo_agent/                  # Agent framework
│   ├── core/
│   │   ├── config.py           # Configuration management
│   │   └── llm.py              # Ollama LLM client
│   ├── memory/
│   │   ├── memory.py           # File-based memory
│   │   └── vector_memory.py    # ChromaDB semantic memory
│   ├── tools/
│   │   └── tools.py            # 30+ tool implementations
│   ├── agents/
│   │   └── agent.py            # Core reasoning loop
│   └── ui/
│       ├── tui.py              # Rich terminal UI
│       └── terminal.py         # Terminal interface
│
├── vscode/                     # VS Code integration
│   ├── install_code_server.sh  # Auto-installer (latest release)
│   └── code_server_manager.sh  # start/stop/status/restart
│
├── ai_core/                    # Additional AI modules
│   ├── agent_api.py            # Socket API (port 7070)
│   ├── rest_api.py             # REST API (port 8080)
│   ├── multi_agent.py          # Multi-agent coordination
│   ├── daemon.py               # Always-on AI daemon
│   └── kairos.py               # Proactive background agent
│
├── apps/                       # Standalone app modules
├── shell/                      # Shell environment
├── kernel/                     # Kernel reference & configs
├── ui/                         # Desktop UI (Tkinter, dashboard)
├── compat/                     # Wine bridge, Android compat
├── docker/                     # Docker + supervisord configs
├── systemd/                    # Systemd service units
├── iso/                        # ISO build scripts
└── docs/                       # Architecture & roadmap docs
```

---

## ⚙️ Configuration

### Environment Variables

```bash
export LUO_MODEL=mistral               # Default Ollama model
export OLLAMA_URL=http://localhost:11434
export LUO_PORT=3000                   # Web server port
export LUO_WORKSPACE=~/luo_workspace   # VS Code workspace
```

### Systemd Services (Linux production)

```bash
sudo ./install_services.sh

sudo systemctl start luo-server        # Web interface
sudo systemctl start luo-agent         # AI daemon
sudo systemctl enable luo-server       # Auto-start on boot

sudo systemctl status luo-*            # Check all LuoOS services
journalctl -u luo-server -f            # Live logs
```

---

## 📦 Dependencies

### Core (required)
```
flask >= 3.0          Web framework
flask-cors            Cross-origin resource sharing
requests              HTTP client
ollama                Local LLM runtime (install separately)
```

### AI / Memory (recommended)
```
chromadb              Vector database for semantic memory
sentence-transformers Embedding models for memory search
```

### Voice (optional)
```
pyaudio               Microphone input
SpeechRecognition     Speech-to-text
pyttsx3               Text-to-speech (offline)
edge-tts              Neural TTS (online, high quality)
```

### UI (optional)
```
textual               Rich terminal UI
rich                  Formatted terminal output
```

Install everything:
```bash
pip install -r requirements.txt
```

---

## 🗺️ Roadmap

### v0.1 — Foundation ✅ Current
- [x] Browser desktop OS with window manager and 12 apps
- [x] LUOKAI ReAct agent with streaming responses
- [x] 30+ tool executor with permission gates
- [x] Three-tier memory (file, vector, session)
- [x] autoDream background memory consolidation
- [x] 24/7 voice interface with wake-word detection
- [x] Co-evolution self-improvement engine
- [x] VS Code integration via code-server (port 8080)
- [x] Shared workspace between VS Code and Luo Files
- [x] Multi-agent coordination framework
- [x] Docker and systemd deployment support
- [x] 4,146-entry skills library

### v0.2 — Intelligence Layer 🚧 In Progress
- [ ] KAIROS — proactive always-on background agent
- [ ] Persistent memory across full sessions
- [ ] Agent-to-agent HTTP communication protocol
- [ ] Plugin system for custom tools
- [ ] Real-time web dashboard with agent telemetry
- [ ] Package manager with auto-update
- [ ] ISO builder for bootable LuoOS image

### v0.3 — Network Layer
- [ ] Distributed agent mesh across multiple machines
- [ ] P2P agent communication protocol
- [ ] Cloud memory sync
- [ ] Remote LuoOS management interface

### v1.0 — Full OS Release
- [ ] Custom bootloader
- [ ] Native GUI (beyond browser)
- [ ] Full app store
- [ ] Android application compatibility
- [ ] Full Windows compatibility via Wine
- [ ] Security hardening and audit
- [ ] Complete documentation

---

## 🔗 Built On Open Source

LuoOS is built on and inspired by over 60 open-source projects. Major foundations include:

- **[Ollama](https://github.com/ollama/ollama)** — Local LLM runtime
- **[code-server](https://github.com/coder/code-server)** — VS Code in the browser
- **[ChromaDB](https://github.com/chroma-core/chroma)** — Vector database
- **[Flask](https://github.com/pallets/flask)** — Python web framework
- **[Redox OS](https://github.com/redox-os/redox)** — Rust microkernel reference
- **[Whisper](https://github.com/openai/whisper)** — Offline speech recognition

Full attribution: [SOURCES.md](SOURCES.md)

---

## ⚖️ Legal

**© 2025 Luo Kai (luokai25). All rights reserved.**

LuoOS, LUOKAI, Luo AI, Luo Browser, Luo Terminal, Luo Files, Luo Studio, Luo Vision, Luo Music, Luo Notes, Luo Code, Luo Settings, Luo VS Code — all names, product designs, and implementations in this repository are the intellectual property of Luo Kai.

The software is provided for viewing and evaluation purposes. Reproduction, redistribution, or commercial use requires explicit written permission from the author.

Open-source components used in this project retain their original licenses as credited in [SOURCES.md](SOURCES.md).

---

<div align="center">

Built with ❤️ by **Luo Kai**

*The OS that thinks.*

</div>

---

## 🧠 luo_memory — Living Cell Memory System

> *"Not a memory module. A memory organism."*

luo_memory is a biologically-inspired, living memory architecture for luo_os agents. Unlike traditional memory systems that store and retrieve data like a database, luo_memory is built from **autonomous cells** — each one always alive, always signaling, always evolving.

The design is grounded in neuroscience: each cell maps to a specific brain region and replicates its behavior in software. Together, they form a memory organism that is greater than the sum of its parts.

---

### Architecture — The Eight Luo-Cells

Each luo-cell is an `asyncio` coroutine running permanently in the background. Cells communicate through a signal bus — they fire spontaneously when their internal thresholds are crossed, not only when called.

| Cell | Brain Analog | Role |
|------|-------------|------|
| `EpisodicCell` | Hippocampus | Stores every event verbatim with timestamp and session context. Never summarizes. Never discards. |
| `SemanticCell` | Cerebral Cortex | Promotes repeated episodes into permanent facts when a concept appears 3+ times across sessions. |
| `SkillCell` | Cerebellum | Observes tool execution chains and crystallizes successful ones into reusable named skills. |
| `WorkingCell` | Prefrontal Cortex | In-session scratchpad (12-slot buffer). Auto-flushes to EpisodicCell at session end. |
| `DecayCell` | Ebbinghaus Curve | Always ticking. Weakens cold synaptic connections using the forgetting curve formula. |
| `DreamCell` | Hippocampal Replay | Activates on system idle. Replays recent episodes and promotes patterns to SemanticCell. |
| `ImportanceCell` | Amygdala | Scores incoming events for high importance (errors, decisions, breakthroughs) and boosts their decay resistance. |
| `AssociativeCell` | Spreading Activation | Maintains a concept graph. Activating one memory spreads activation to linked concepts. |

---

### What Makes a Luo-Cell Alive

A traditional software module waits to be called. A luo-cell lives independently:

```
LuoCell
  ├── internal state      — own memory, not shared dict (like cytoplasm)
  ├── spontaneous firing  — signals neighbors unprompted (like neurotransmitters)
  ├── lifespan + death    — born strong, weakened by disuse, retired at zero strength
  ├── Hebbian plasticity  — connections strengthen when two cells co-fire (fire together, wire together)
  ├── self-repair         — detects corruption and broadcasts repair request to neighbors
  └── division            — splits into child cell when load exceeds capacity
```

Connection weights between cells are stored in a persistent SQLite synapse table. Over thousands of sessions, the network develops its own association map — not one you programmed, but one that emerged from actual use patterns.

---

### Composite Retrieval Score

Every memory recall is ranked by a brain-inspired composite score:

```
score = (0.55 × semantic_similarity)
      + (0.20 × recency_decay)
      + (0.15 × importance_tag)
      + (0.10 × access_count)
```

This means frequently-accessed, recently-seen, emotionally-tagged memories surface first — exactly as they do in human recall.

---

### Quick Start

```python
from luo_agent.memory import LuoMemory
import asyncio

async def main():
    mem = LuoMemory()
    await mem.start()

    # store a memory verbatim
    await mem.store("user prefers Python over Bash for automation tasks")

    # load hot context at session start (inject into system prompt)
    context = await mem.wake_up()
    print(context)

    # recall by keyword
    results = await mem.recall("Python preference")

    # track tool use for skill crystallization
    await mem.tool_executed("bash", args={"cmd": "ls"}, success=True)
    await mem.task_completed(goal="list project files", success=True)

    # trigger dream consolidation manually
    await mem.dream()

    # inspect network
    print(mem.status())

    await mem.stop()

asyncio.run(main())
```

For non-async contexts:

```python
from luo_agent.memory import LuoMemorySync

mem = LuoMemorySync()
mem.start()
mem.store("the agent fixed a memory leak in session 14")
context = mem.wake_up()
mem.stop()
```

CLI interface:

```bash
cd luo_agent/memory
python3 luo_memory.py status    # network status
python3 luo_memory.py wake      # print hot context
python3 luo_memory.py store "text to remember"
python3 luo_memory.py recall "query"
python3 luo_memory.py facts     # all semantic facts
python3 luo_memory.py skills    # all crystallized skills
python3 luo_memory.py dream     # trigger consolidation
```

---

### File Structure

```
luo_agent/memory/
├── luo_cell.py          # LuoCell base class + LuoCellNetwork + SynapseTable
├── luo_cells.py         # All 8 specialized cell implementations
├── luo_memory.py        # Public API (LuoMemory + LuoMemorySync + CLI)
├── __init__.py          # Module exports
├── MEMORY.md            # L0 hot context (loaded at agent startup)
├── palace/              # Persistent palace storage
│   ├── luo_agent/       # Wing: agent task memory
│   ├── user/            # Wing: user goals and preferences
│   └── skills/          # Wing: crystallized skill storage
└── chroma_db/           # Reserved for vector embedding index (v1.1)
```

---

### Design Principles

1. **Verbatim storage** — nothing is summarized or extracted away. The human brain lossy-compresses; luo_memory does not. Every word is stored exactly as given.
2. **Zero API cost** — runs entirely on local SQLite. No Ollama calls during normal operation. DreamCell consolidation is the only optional LLM step.
3. **Always alive** — cells run as asyncio background tasks. There is no main loop that calls them. They exist, they observe, they fire.
4. **Emergent intelligence** — the Hebbian synapse table means the system develops its own association map through use. You do not program it; it learns.
5. **Drop-in compatible** — `LuoMemorySync` wraps the async API for use anywhere in luo_os without requiring the caller to manage an event loop.

---

### Integration with luo_agent

luo_memory integrates directly with the existing luo_agent reasoning loop:

```python
# in luo_agent/agents/agent.py — add at session start:
from luo_agent.memory import LuoMemory
mem = LuoMemory()
await mem.start()
system_context = await mem.wake_up()

# inject context into system prompt
system_prompt = base_system_prompt + "\n\n" + system_context

# after each tool call:
await mem.tool_executed(tool_name, args=tool_args, success=True)

# after each exchange:
await mem.store(f"User: {user_msg}\nAgent: {agent_response}")

# at session end:
await mem.task_completed(goal=session_goal, success=True)
await mem.stop()
```

