# ⚡ Luo OS v0.1
### A Free Operating System for Humans and AI Agents
*Created by Luo Kai (luokai25)*

---

## Vision
Luo OS is a free, open-source operating system where AI is not an app —
it is part of the system itself. Built for both humans and AI agents.
No paywalls. No limits. Forever free.

---

## Architecture
| Layer | Technology |
|---|---|
| Kernel | Linux v7.0-rc6 base |
| AI Core | TinyLlama via Ollama (local, offline) |
| Desktop | Full GUI (Python/tkinter) |
| Agent API | Socket on port 7070 |
| REST API | HTTP on port 7071 |
| Dashboard | Web UI (browser-based) |
| Compat | Wine (Windows apps) |
| Shell | Bash + PowerShell + Luo Shell |
| Package Manager | luo_pkg.py |
| Multi-Agent | Spawn + manage AI sub-agents |

---

## Quick Start
```bash
# Clone
git clone https://github.com/luokai25/luo_os-v_0.1.git
cd luo_os-v_0.1

# Start everything
bash start_luo_os.sh
```

---

## File Structure
```
luo_os-v_0.1/
├── luo_os.py              ← Main launcher (boot screen)
├── start_luo_os.sh        ← Start all services
├── SOURCES.md             ← OS source credits + licenses
│
├── ai_core/
│   ├── daemon.py          ← Local AI (TinyLlama)
│   ├── agent_api.py       ← Socket API port 7070
│   ├── rest_api.py        ← HTTP REST API port 7071
│   ├── agent_client.py    ← Example agent client
│   ├── multi_agent.py     ← Multi-agent system
│   └── config.json        ← AI config
│
├── ui/
│   ├── window_manager.py  ← Full GUI desktop
│   ├── dashboard.html     ← Web dashboard
│   └── terminal_src/      ← Windows Terminal source
│
├── shell/
│   ├── luo_shell.sh       ← Luo Shell
│   ├── luo_pkg.py         ← Package manager
│   └── powershell_src/    ← PowerShell source
│
├── kernel/
│   ├── config.md          ← Kernel config
│   ├── bootloader.md      ← Boot sequence
│   ├── xnu_mach/          ← Apple XNU Mach kernel
│   ├── redox_src/         ← Redox OS source (Rust)
│   └── redox_*/           ← Redox build system
│
├── apps/
│   ├── text_editor.py     ← Built-in text editor
│   ├── browser.py         ← Built-in browser
│   └── file_manager.py    ← Built-in file manager
│
├── compat/
│   ├── wine_bridge.py     ← Windows app runner
│   └── android_bridge.md  ← Android compat plan
│
├── drivers/
│   └── drivers.md         ← Hardware drivers (Linux-based)
│
├── iso/
│   └── build_iso.sh       ← ISO builder
│
└── docs/
    ├── architecture.md    ← System architecture
    └── roadmap.md         ← Development roadmap
```

---

## AI Agent API
Any AI agent can connect and control Luo OS:

### Socket (port 7070)
```python
import socket, json
s = socket.socket()
s.connect(("127.0.0.1", 7070))
s.send(json.dumps({"action": "ping"}).encode())
```

### REST (port 7071)
```bash
curl http://127.0.0.1:7071/status
curl -X POST http://127.0.0.1:7071/ai -d '{"prompt":"Hello"}'
curl -X POST http://127.0.0.1:7071/run -d '{"command":"ls"}'
```

---

## Package Manager
```bash
python3 shell/luo_pkg.py available
python3 shell/luo_pkg.py install vim
python3 shell/luo_pkg.py install tinyllama
```

---

## Principles
1. Free forever — for humans and AI agents
2. AI is part of the OS, not an add-on
3. Open source forever
4. No paywalls, no limits
5. Built by Luo Kai

---

## Status: 🚧 v0.1 — In active development
