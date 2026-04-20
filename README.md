# LuoOS — The AI-Native Operating System

> **Built by Luo Kai.** An OS where the AI *is* the system — not a plugin, not a feature.

LUOKAI runs completely independently — no Ollama, no OpenAI, no external APIs. Double-click and it works.

---

## 🚀 Quick Start

**Windows** — double-click `start.bat`

**Mac / Linux:**
```bash
./start.sh
```

**Any Python 3.6+:**
```bash
python3 start.py
```

Opens automatically at `http://localhost:3000`. No config. No downloads. No external services.

---

## 🧠 LUOKAI Brain

Fully independent AI — built from scratch:

```
┌─────────────────────────────────────────────────────────┐
│                      LUOKAI BRAIN                       │
│                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │  Reasoning  │  │     NLP     │  │   Coding    │     │
│  │  14 cells   │  │   5 cells   │  │   6 cells   │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
│                                                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │        Knowledge Base  —  78,063 entries         │   │
│  │  algorithms · debugging · security · APIs        │   │
│  │  architecture · testing · devops · docs          │   │
│  └──────────────────────────────────────────────────┘   │
│                                                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │       Neural Interface  —  Cortical Labs CL1     │   │
│  │  64-channel MEA · spike detection · stimulation  │   │
│  │  biological neuron ↔ AI closed loop              │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### Cell System

| Family | Cells | Purpose |
|---|---|---|
| **Reasoning** | ModusPonens, Syllogism, Analogy, CauseEffect, Abduction... | 14 cells — logical inference |
| **NLP** | Tokenizer, NER, IntentClassifier, Sentiment, ContextTracker | 5 cells — language understanding |
| **Coding** | Debug, Syntax, Logic, Algorithm, Security, Refactor | 6 cells — code intelligence |
| **Neural** | NeuralBridge, SpikeInterpreter, StimulusDesigner | 3 cells — biological neuron interface |

### Knowledge Base (ships in repo, zero download)

78,063 curated entries in `luokai/data/knowledge.db`:

- Code conversations — 15,000 real Q&A pairs
- Algorithms — 10,000 (complexity, implementation)
- Debugging scenarios — 10,000 (error → solution)
- Security vulnerabilities — 8,000 (vuln + fix)
- Architecture patterns — 8,000
- API patterns, test cases, CI/CD, devops, documentation — 5,000 each

---

## 🧬 Neural Interface — Cortical Labs CL1

LuoOS bridges real biological neurons via the [Cortical Labs CL1](https://corticallabs.com) platform.

**Simulation mode (no hardware needed — runs by default):**
```python
from luokai.cells.neural import NeuralEngine
engine = NeuralEngine(sim_mode=True)
engine.start()
```

**Real CL1 hardware:**
```python
engine = NeuralEngine(sim_mode=False, ticks_per_second=1000)
engine.start(try_hardware=True)
```

**What it does:**
- Reads spikes from 64 MEA channels at 25kHz
- Classifies patterns: burst / synchronous / sparse / focal
- Maps neural activity to cognitive states: FOCUSED, ENGAGED, ANALYTICAL, CREATIVE
- Sends stimulation back: reward, reinforce, explore, entrain rhythms
- Detects theta / alpha / beta / gamma rhythms

**Stimulation presets:**
```python
engine.stimulate_response("reward")      # 5-pulse 50Hz burst
engine.stimulate_response("reinforce")   # 10-pulse 100Hz strong
engine.stimulate_response("explore")     # 2-pulse 10Hz distributed
engine.stimulate_response("entrain_gamma")  # 40-pulse 40Hz attention
```

**Closed-loop experiment (CL1 hardware):**
```python
import cl
from luokai.cells.neural import NeuralEngine

engine = NeuralEngine(sim_mode=False)
with cl.open() as neurons:
    for tick in neurons.loop(ticks_per_second=1000):
        for spike in tick.analysis.spikes:
            neurons.stim(spike.channel, 1)
        if len(tick.analysis.spikes) > 50:
            engine.stimulate_response("reward")
```

---

## 🏗 Architecture

```
LuoOS/
├── start.py               # One-click launcher (Python 3.6+)
├── start.bat              # Windows
├── start.sh               # Mac/Linux
├── luo_server.py          # Flask backend (port 3000)
├── index.html             # Main OS UI
│
├── luokai/
│   ├── core/
│   │   ├── inference.py   # Inference engine (4,146 skills + knowledge)
│   │   ├── brain.py       # Brain: CoEvo, KAIROS, TreeOfThought
│   │   └── react_agent.py # ReAct reasoning agent
│   │
│   ├── cells/
│   │   ├── base.py            # BaseCell
│   │   ├── reasoning.py       # 14 reasoning cells
│   │   ├── nlp.py             # 5 NLP cells
│   │   ├── coding.py          # 6 coding cells
│   │   ├── data_index.py      # Knowledge search
│   │   └── neural/
│   │       ├── bridge.py      # CL1 MEA interface
│   │       ├── interpreter.py # Spike → cognitive state
│   │       └── stimulator.py  # Decision → stimulation
│   │
│   ├── data/
│   │   ├── knowledge.db       # 78,063 entries (12MB)
│   │   ├── knowledge/k000.jsonl
│   │   ├── knowledge/k001.jsonl
│   │   └── build_knowledge.py
│   │
│   └── skills/            # 4,146 skills — 20 domains
│
├── ai_core/               # Background agents
├── ui/                    # Dashboard panels
└── docs/                  # Architecture & roadmap
```

---

## 💬 Knowledge Coverage

LUOKAI answers instantly from built-in knowledge:

```
CSS        — centering, flexbox, grid, box model, responsive
APIs       — REST, GraphQL, WebSocket, OAuth 2.0, JWT
DevOps     — Docker, Kubernetes, CI/CD, nginx, git
Algorithms — binary search, BFS/DFS, dynamic programming, Big O
Security   — SQL injection, XSS, CSRF, password hashing
Databases  — SQL vs NoSQL, indexes, normalization, window functions
Languages  — Python, JavaScript, TypeScript, Rust, React, Node.js
ML/AI      — neural networks, PyTorch, training loops
Networking — TCP/IP, HTTPS/TLS, DNS resolution
```

---

## 🔌 API

All at `http://localhost:3000`:

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/chat` | Send message to LUOKAI |
| `GET`  | `/api/status` | System status |
| `GET`  | `/api/brain/status` | Cell system status |
| `POST` | `/api/brain/learn` | Teach LUOKAI a fact |
| `GET`  | `/api/brain/skills` | List skills |

```bash
curl -X POST http://localhost:3000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "what is binary search?"}'
```

---

## 📋 Requirements

- **Python 3.6+** — any version works
- **flask + flask-cors** — auto-installed on first run

**Optional for neural experiments:**
- Cortical Labs CL1 hardware
- `pip install cl`

---

## 🗺 Roadmap

- [x] LUOKAI native AI — zero external dependencies
- [x] Cell system — reasoning, NLP, coding, neural
- [x] 78K knowledge entries in repo
- [x] Cortical Labs CL1 neural interface
- [x] One-click start — Windows / Mac / Linux
- [x] Python 3.6+ compatibility
- [ ] Conversation memory across sessions
- [ ] Neural activity dashboard
- [ ] Voice interface
- [ ] Multi-language support

---

*Built by Luo Kai — an OS that thinks.*
