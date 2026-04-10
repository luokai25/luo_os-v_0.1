<div align="center">

# 𝗟𝗨𝗢 𝗢𝗦 𝘃𝟏.𝟎

**The AI-Native Operating System — Runs in Any Browser**

*Created by **Luo Kai** (luokai25 · luokai0)*

</div>

---

## What is LuoOS?

LuoOS is a **full computer that runs in your browser** — like Zed OS / JSLinux, but powered by a state-of-the-art local AI. No cloud. No API keys. Everything on YOUR machine.

**LUOKAI** is the AI core: always listening, always learning, always improving itself.

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/luokai25/luo_os-v_0.1
cd luo_os-v_0.1

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start Ollama (required for AI)
ollama serve &
ollama pull mistral

# 4. Run LuoOS
python3 luo_cli.py chat      # Interactive chat
python3 luo_cli.py server    # Web interface
python3 luo_cli.py evolution # Self-improvement mode

# Or use quick start:
./start_all.sh
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        LUO OS v1.0                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │  LUOKAI     │  │  Vector     │  │   Tools     │            │
│  │  Agent      │  │  Memory     │  │   System    │            │
│  │  (Core AI)  │  │  (RAG)      │  │  (30+ tools)│            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │  Voice      │  │  Co-Evo     │  │   CLI/TUI   │            │
│  │  Interface  │  │  Engine     │  │   Interface │            │
│  │  (24/7)     │  │  (Self-Improve)│  │             │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                      Ollama (Local LLM)                         │
│                    mistral / llama / qwen                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## Components

### 1. LUOKAI Agent (`luokai/core/luokai_agent.py`)

The main AI agent with:
- **Ollama integration** for local LLM inference
- **Vector memory** for semantic recall
- **Tool execution** for real actions
- **Voice interface** for hands-free interaction
- **Co-evolution** for self-improvement

```python
from luokai.core.luokai_agent import LUOKAIAgent

agent = LUOKAIAgent(model="mistral")
response = agent.think("What can you do?")
print(response)
```

### 2. Vector Memory (`luo_agent/memory/vector_memory.py`)

Semantic memory using ChromaDB:
- Store and retrieve memories by meaning
- RAG (Retrieval Augmented Generation)
- Persistent storage

```python
from luo_agent.memory.vector_memory import VectorMemory

memory = VectorMemory(agent_id="my_agent")
memory.add("User likes Python programming")
results = memory.search("coding preferences")
```

### 3. Tools System (`luo_agent/tools/tools.py`)

30+ tools for real actions:

| Category | Tools |
|----------|-------|
| Files | read_file, write_file, edit_file, list_dir, find_files, grep_file |
| Shell | bash, run_python, run_script |
| Web | web_search, web_fetch, http_request |
| System | system_info, process_list, kill_process |
| Docker | docker_ps, docker_exec, docker_logs |
| Code | analyze_code, hash_file |
| Utility | calculate, json_format, base64_encode/decode, uuid_gen |

```python
from luo_agent.tools.tools import ToolExecutor

tools = ToolExecutor()
result = tools.execute("web_search", {"query": "Python tutorials"})
```

### 4. Voice Interface (`luokai/voice/always_on.py`)

24/7 always-on voice:
- Wake word: "Luo" or "LUOKAI"
- Whisper for STT (offline)
- edge-tts / pyttsx3 for TTS
- No button press needed

```python
agent.start_voice()  # Starts background listener
agent.stop_voice()   # Stops
```

### 5. Co-Evolution Engine (`luokai/evolution/coevo.py`)

Self-improvement system:
1. **CHALLENGER** generates tests
2. **LUOKAI** solves them
3. **EVALUATOR** scores answers
4. Difficulty increases as AI improves

```python
agent.start_evolution(interval=300)  # Every 5 minutes
```

### 6. CLI Interface (`luo_cli.py`)

Unified command-line interface:

```bash
python3 luo_cli.py chat       # Interactive chat
python3 luo_cli.py voice      # Voice interface
python3 luo_cli.py evolution  # Self-improvement
python3 luo_cli.py tools      # List tools
python3 luo_cli.py status     # System status
python3 luo_cli.py server     # Web server
python3 luo_cli.py tui        # Rich TUI
python3 luo_cli.py install    # Install dependencies
```

---

## Installation

### Option 1: Quick Install

```bash
pip install -r requirements.txt
```

### Option 2: Minimal Install

```bash
pip install flask flask-cors requests
```

### Option 3: Full Install

```bash
pip install -r requirements.txt
pip install chromadb sentence-transformers  # Vector memory
pip install textual rich                     # Rich TUI
pip install pyaudio SpeechRecognition edge-tts  # Voice
```

### Systemd Services (Linux)

```bash
sudo ./install_services.sh

# Manage services
sudo systemctl start luo-agent
sudo systemctl start luo-server
sudo systemctl status luo-*
```

---

## Configuration

Environment variables:

```bash
export LUO_MODEL=mistral
export OLLAMA_URL=http://localhost:11434
```

Or use config file:

```python
from luo_agent.core.config import LuoConfig

config = LuoConfig()
config.set("model", "llama2")
```

---

## Keyboard Shortcuts (TUI)

| Key | Action |
|-----|--------|
| Ctrl+C | Quit |
| Ctrl+L | Clear chat |
| Ctrl+S | Save session |
| F1 | Show memory |
| F2 | Show agents |

---

## Chat Commands

| Command | Description |
|---------|-------------|
| /help | Show available commands |
| /status | Show agent status |
| /memory | Show memory contents |
| /tools | List available tools |
| /model \<name\> | Switch model |
| /clear | Clear conversation |
| /quit | Exit |

---

## API Endpoints

When running `luo_server.py`:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/chat` | POST | Chat with LUOKAI |
| `/api/status` | GET | Get agent status |
| `/api/execute` | POST | Execute code |
| `/api/search` | POST | Web search |
| `/api/voice/start` | POST | Start voice |
| `/api/voice/stop` | POST | Stop voice |
| `/api/evolution/start` | POST | Start evolution |
| `/api/fs/read` | POST | Read file |
| `/api/fs/write` | POST | Write file |
| `/api/fs/ls` | POST | List directory |

---

## Browser OS

Open `index.html` for the browser-based OS sandbox:
- Desktop environment
- Window manager
- 11 built-in apps
- File manager
- Terminal emulator

---

## The Co-Evolution Algorithm

```
LUOKAI improves → generates harder tests → passes them → even harder tests → ∞
```

1. **CHALLENGER** generates increasingly hard tests
2. **LUOKAI** solves them using Tree-of-Thought reasoning
3. **EVALUATOR** scores answers 0-10
4. Failures become training data
5. Difficulty increases as scores improve

---

## Project Structure

```
luo_os/
├── luo_cli.py              # Unified CLI entry point
├── luo_server.py           # Flask web server
├── luo_os.py              # Tkinter launcher
├── requirements.txt        # Dependencies
├── index.html             # Browser OS
│
├── luokai/                # LUOKAI AI core
│   ├── core/
│   │   └── luokai_agent.py
│   ├── voice/
│   │   └── always_on.py
│   ├── evolution/
│   │   └── coevo.py
│   └── skills/
│
├── luo_agent/             # Agent framework
│   ├── core/
│   │   ├── config.py
│   │   └── llm.py
│   ├── memory/
│   │   ├── memory.py
│   │   └── vector_memory.py
│   ├── tools/
│   │   └── tools.py
│   ├── agents/
│   │   └── agent.py
│   └── ui/
│       ├── tui.py
│       └── terminal.py
│
├── ai_core/               # Additional AI modules
├── kernel/                # OS kernel (experimental)
├── ui/                    # Desktop UI (Tkinter)
├── apps/                  # Built-in apps
├── shell/                 # Shell environment
├── docker/                # Docker configs
├── systemd/               # Systemd services
└── docs/                  # Documentation
```

---

## Legal

**© 2025 Luo Kai (luokai25). All rights reserved.**

LuoOS, LUOKAI, Luo AI, Luo Browser, Luo Terminal, Luo Files, Luo Studio, Luo Vision, Luo Music, Luo Notes, Luo Code, Luo Settings — all names, concepts, and implementations are intellectual property of Luo Kai.

Built with ❤️ from 60+ open-source projects. See [SOURCES.md](SOURCES.md).