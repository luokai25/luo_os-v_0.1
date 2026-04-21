# LuoOS — The AI-Native Operating System

> **Built by Luo Kai.** An OS where the AI *is* the system — not a plugin, not a feature.

LUOKAI is the brain of LuoOS. It runs 100% locally — no Ollama, no OpenAI, no cloud. Just open it and it works.

---

## 🚀 Ways to Run LuoOS

### 1. 💻 On Your Device (Windows / Mac / Linux)

**Windows** — double-click `start.bat`

**Mac / Linux:**
```bash
git clone https://github.com/luokai25/luo_os-v_0.1.git
cd luo_os-v_0.1
./start.sh
```

**Any Python 3.6+:**
```bash
git clone https://github.com/luokai25/luo_os-v_0.1.git
cd luo_os-v_0.1
python3 start.py
```

Opens at `http://localhost:3000` automatically. No config needed.

On first run LUOKAI downloads its AI weights (~900MB) once to `~/.luo_os/models/`. After that it loads in ~3 seconds every time, fully offline.

---

### 2. ☁️ GitHub Codespaces (zero install — runs in browser)

Run LuoOS directly in your browser with no local setup at all.

1. Go to **https://github.com/luokai25/luo_os-v_0.1**
2. Click the green **`<> Code`** button → **Codespaces** tab
3. Click **"Create codespace on main"**
4. Wait ~1 minute for the environment to boot
5. In the Codespaces terminal:
```bash
python3 start.py
```
6. Codespaces will show a **"Open in Browser"** popup — click it
7. LuoOS opens in a new tab, fully working

> **Note:** In Codespaces the AI model weights download to the cloud container. The cell system (coding, debug, algorithms) works instantly while the model loads.

---

### 3. 🐳 Docker

```bash
# Pull and run
docker pull ghcr.io/luokai25/luo_os:latest
docker run -p 3000:3000 luokai25/luo_os

# Or build yourself
git clone https://github.com/luokai25/luo_os-v_0.1.git
cd luo_os-v_0.1
docker build -t luo_os .
docker run -p 3000:3000 -v ~/.luo_os:/root/.luo_os luo_os
```

Mount `~/.luo_os` as a volume so the AI weights persist between container runs.

Open `http://localhost:3000` in your browser.

---

### 4. 📦 pip install

```bash
pip install luo-os
luo-os start
```

Opens at `http://localhost:3000`.

---

### 5. ▶️ Replit

1. Go to **https://replit.com**
2. Click **"+ Create Repl"** → **"Import from GitHub"**
3. Paste: `https://github.com/luokai25/luo_os-v_0.1`
4. Set the run command to: `python3 start.py`
5. Click **Run**
6. Open the **Webview** tab — LuoOS is live

> Replit free tier works. The AI weights download to Replit's storage on first run.

---

### 6. 🌐 Gitpod

[![Open in Gitpod](https://gitpod.io/button/open-in-gitpod.svg)](https://gitpod.io/#https://github.com/luokai25/luo_os-v_0.1)

Or manually:
1. Go to `https://gitpod.io/#https://github.com/luokai25/luo_os-v_0.1`
2. Gitpod boots the workspace automatically
3. In the terminal: `python3 start.py`
4. Open the port `3000` preview

---

### 7. 🧑‍💻 VS Code Dev Container

1. Install the **Dev Containers** extension in VS Code
2. Clone the repo:
```bash
git clone https://github.com/luokai25/luo_os-v_0.1.git
cd luo_os-v_0.1
code .
```
3. VS Code will ask: **"Reopen in Container"** — click it
4. In the container terminal: `python3 start.py`
5. Open `http://localhost:3000`

---

### 8. 🐧 Linux Server / VPS

```bash
# Clone and run headless
git clone https://github.com/luokai25/luo_os-v_0.1.git
cd luo_os-v_0.1
pip3 install flask flask-cors
python3 luo_server.py

# Access from anywhere
http://YOUR_SERVER_IP:3000
```

To keep it running after logout:
```bash
# With screen
screen -S luoos
python3 luo_server.py
# Ctrl+A then D to detach

# Or with systemd
sudo nano /etc/systemd/system/luoos.service
```

```ini
[Unit]
Description=LuoOS
After=network.target

[Service]
WorkingDirectory=/path/to/luo_os-v_0.1
ExecStart=python3 luo_server.py
Restart=always

[Install]
WantedBy=multi-user.target
```
```bash
sudo systemctl enable --now luoos
```

---

### 9. 🪟 Windows (detailed)

```cmd
:: Option A — batch file
start.bat

:: Option B — PowerShell
python start.py

:: Option C — no git, download ZIP
:: 1. Go to github.com/luokai25/luo_os-v_0.1
:: 2. Click Code > Download ZIP
:: 3. Extract the ZIP
:: 4. Double-click start.bat
```

Python 3.6+ required. Get it from **python.org** if not installed.

---

### 10. 🍎 macOS

```bash
# Install Python if needed
brew install python3

# Clone and run
git clone https://github.com/luokai25/luo_os-v_0.1.git
cd luo_os-v_0.1
./start.sh

# Or make executable and run
chmod +x start.sh && ./start.sh
```

---

## 🧠 LUOKAI Brain

Fully independent AI — no external dependencies:

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
│  └──────────────────────────────────────────────────┘   │
│                                                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │    Local AI Weights — Qwen2.5-1.5B (909MB)       │   │
│  │  Downloads once · runs offline · CPU only        │   │
│  └──────────────────────────────────────────────────┘   │
│                                                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │       Neural Interface — Cortical Labs CL1       │   │
│  │  64-channel MEA · real biological neurons        │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### How the AI works

| Step | What happens | Speed |
|---|---|---|
| 1 | Cell system handles coding/debug/algorithms | Instant |
| 2 | Knowledge DB answers from 78K entries | Instant |
| 3 | Local model (Qwen2.5-1.5B) answers everything else | ~1-3s |
| 4 | Skills library as fallback | Instant |

**First run:** model downloads ~900MB once to `~/.luo_os/models/`
**Every run after:** loads in ~3 seconds, works offline forever

---

## 🔌 API

All at `http://localhost:3000`:

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/chat` | Send message to LUOKAI |
| `GET`  | `/api/status` | System status |
| `GET`  | `/api/brain/status` | Cell system status |
| `POST` | `/api/brain/learn` | Teach LUOKAI a fact |
| `GET`  | `/api/model/status` | Local model ready/loading |
| `GET`  | `/api/model/list` | Available downloaded models |

```bash
curl -X POST http://localhost:3000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "write a binary search in Python"}'
```

---

## 📋 Requirements

| Requirement | Value |
|---|---|
| Python | 3.6+ |
| RAM (minimum) | 2GB (for AI model) |
| RAM (recommended) | 4GB |
| Disk | 1.5GB (model + OS) |
| GPU | Not required — CPU only |
| Internet | First run only (model download) |
| OS | Windows / Mac / Linux / any |

**Auto-installed on first run:** `flask`, `flask-cors`, `llama-cpp-python`

---

## 🗺 Roadmap

- [x] LUOKAI native AI — zero external dependencies
- [x] Cell system — reasoning, NLP, coding, neural
- [x] 78K knowledge entries in repo
- [x] Local AI weights — Qwen2.5-1.5B (auto-download)
- [x] Cortical Labs CL1 neural interface
- [x] One-click start — Windows / Mac / Linux
- [x] Python 3.6+ compatibility
- [ ] Conversation memory across sessions
- [ ] Neural activity dashboard
- [ ] Voice interface
- [ ] Multi-language support
- [ ] Plugin system for custom cells

---

## 🧬 Neural Interface (Cortical Labs CL1)

For real biological neuron experiments:

```bash
pip install cl
```

```python
from luokai.cells.neural import NeuralEngine

# Simulation mode (no hardware needed)
engine = NeuralEngine(sim_mode=True)
engine.start()

# Real CL1 hardware
engine = NeuralEngine(sim_mode=False, ticks_per_second=1000)
engine.start(try_hardware=True)
```

---

*Built by Luo Kai — an OS that thinks.*
