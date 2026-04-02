# ⚡ Luo OS v0.1
### An Open Source Operating System for Humans and AI Agents
*built by luokai [@luokai25](https://github.com/luokai25)*

> AI is not an app here. It is part of the OS itself.

---

## Quick Start
```bash
git clone https://github.com/luokai25/luo_os-v_0.1.git
cd luo_os-v_0.1
python3 luo_init.py          # boot full OS
bash shell/luo_shell.sh      # interactive shell
cd luo_agent && python3 luo_agent.py  # local AI
```

---

## Architecture

| Layer | Technology | Status |
|---|---|---|
| Kernel | Linux + Redox (Rust) + XNU Mach | 🚧 |
| AI Core | TinyLlama / Phi-3 / any Ollama model | ✅ |
| Luo Agent | Autonomous local AI agent | ✅ |
| Agent Identity | Auto-provisioning for AI agents | ✅ |
| Agent API | Socket port 7070 (token-auth) | ✅ |
| REST API | HTTP port 8080 | ✅ |
| Shell | Luo Shell + Bash | ✅ |
| Package Manager | luo_pkg.py (35+ packages) | ✅ |
| Desktop UI | Python/tkinter | 🚧 |
| Multi-Agent | Sub-agent coordinator | 🚧 |
| Compat | Wine (Windows apps) | 🚧 |

---

## File Structure
```
luo_os-v_0.1/
├── luo_init.py            boot all services
├── luo_os.py              main launcher
├── start_luo_os.sh        shell boot script
├── luo_agent/             autonomous local AI agent
│   ├── luo_agent.py       entry point
│   ├── core/              config, ollama client, daemon
│   ├── memory/            MEMORY.md + notes + autoDream
│   ├── tools/             14 tools: file, bash, web, python
│   ├── agents/            reasoning loop + tool calling
│   └── ui/                terminal UI with streaming
├── ai_core/               OS-level AI layer
│   ├── agent_identity.py  auto-provisioning system
│   ├── agent_api.py       socket API port 7070
│   ├── agent_client.py    zero-config client
│   ├── rest_api.py        HTTP REST API port 8080
│   ├── daemon.py          local AI daemon
│   └── multi_agent.py     multi-agent coordinator
├── ui/                    desktop GUI + dashboard
├── shell/                 luo shell + package manager
├── kernel/                kernel sources
├── apps/                  built-in apps
├── compat/                wine bridge
└── docs/                  architecture + roadmap
```

---

## Luo Agent — Local AI

No API keys. No credits. No internet. Free forever.
```bash
cd luo_agent && python3 luo_agent.py
```

| RAM | Model |
|---|---|
| 1-2 GB | `ollama pull tinyllama` |
| 2-3 GB | `ollama pull qwen2.5:1.5b` |
| 3-4 GB | `ollama pull gemma2:2b` |
| 4 GB+ | `ollama pull phi3:mini` |

---

## Agent Identity — Auto-Provisioning

Any AI agent that reads this repo gets an identity instantly:
```python
from ai_core.agent_client import connect_to_luo
luo = connect_to_luo(model="tinyllama", agent_name="my_agent")
print(luo.identity["agent_id"])
luo.run_command("ls /")
luo.memory_write("connected to Luo OS")
```

---

## Principles

1. Free forever — for humans and AI agents equally
2. AI is the OS — not an add-on
3. Open source — forever
4. Works on low-spec hardware
5. No paywalls, no limits, no accounts required

---

*Built by luokai*
