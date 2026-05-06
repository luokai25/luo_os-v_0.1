import json
#!/usr/bin/env python3
"""
LuoOS Server — Main backend
Serves the full browser-based OS + LUOKAI AI API
Port 3000 (sandbox OS) + 7070 (LUOKAI API)

Enhanced with:
- Streaming responses (SSE)
- ReAct agent with planning and reflection
- Multi-model support
- Real skills library
"""
import sys, json, time, threading, subprocess, os, signal
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory, Response, stream_with_context
from flask_cors import CORS

sys.path.insert(0, str(Path(__file__).parent))

# Load LuoOS config (set by start.py or setup_luoos.py)
_LUO_USER   = os.environ.get("LUO_USER_NAME", "User")
_LUO_MODEL  = os.environ.get("LUO_AI_MODEL",  "qwen2.5-1.5b")
_LUO_FEATS  = set(os.environ.get("LUO_FEATURES", "voice,coevo,neural,autolearn").split(","))

app     = Flask(__name__, static_folder=".", static_url_path="")
CORS(app)

# ── VS Code / code-server Configuration ─────────────────────────────
VSCODE_PORT      = 8080
VSCODE_PASSWORD  = os.environ.get("LUOOS_PASSWORD", "luoos2024")  # override: export LUOOS_PASSWORD=yourpass
VSCODE_WORKSPACE = Path.home() / "luo_workspace"
VSCODE_CONFIG    = Path.home() / ".config" / "code-server" / "config.yaml"
VSCODE_PID_FILE  = Path("/tmp/luo-code-server.pid")
VSCODE_LOG_FILE  = Path("/tmp/luo-code-server.log")
_vscode_proc     = None   # subprocess handle

# ── Configuration ───────────────────────────────────────────────────────
USE_REACT_AGENT = True  # Use enhanced ReAct agent
STREAMING_ENABLED = True  # Enable streaming responses

# ── Boot LUOKAI ──────────────────────────────────────────────────────
print("🚀 Booting LUOKAI Agent...")

agent = None
react_agent = None
AGENT_OK = False

# Try to load ReAct agent first (enhanced version)
if USE_REACT_AGENT:
    try:
        from luokai.core.react_agent import create_agent
        react_agent = create_agent(streaming=STREAMING_ENABLED)
        AGENT_OK = True
        print(f"✅ LUOKAI ReAct Agent ready (model: {react_agent.model})")
    except Exception as e:
        print(f"⚠️  ReAct agent error: {e}, falling back to basic agent")

# Fall back to basic agent if ReAct fails
if not AGENT_OK:
    try:
        from luokai.core.luokai_agent import LUOKAIAgent
        agent = LUOKAIAgent()
        AGENT_OK = True
        print("✅ LUOKAI Basic Agent ready")
    except Exception as e:
        print(f"⚠️  LUOKAI Agent error: {e}")
        AGENT_OK = False

# Use whichever agent is available
active_agent = react_agent or agent

# ── Routes ───────────────────────────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@app.route("/<path:path>")
def static_files(path):
    return send_from_directory(".", path)

@app.route("/api/chat", methods=["POST"])
def chat():
    """Standard chat endpoint (non-streaming)."""
    data = request.json or {}
    msg  = data.get("message","").strip()
    stream = data.get("stream", False)

    if not msg:
        return jsonify({"error": "empty"}), 400
    if not active_agent:
        return jsonify({"response": "LUOKAI offline — check requirements"}), 200

    # Handle streaming request
    if stream and STREAMING_ENABLED and react_agent:
        return Response(
            stream_with_context(generate_stream(msg)),
            mimetype='text/event-stream'
        )

    # Standard non-streaming response
    try:
        resp = active_agent.think(msg)
        return jsonify({"response": resp, "ok": True})
    except Exception as e:
        return jsonify({"response": f"Error: {e}", "ok": False})


@app.route("/api/chat/stream", methods=["POST"])
def chat_stream():
    """Streaming chat endpoint using Server-Sent Events."""
    data = request.json or {}
    msg = data.get("message", "").strip()

    if not msg:
        return jsonify({"error": "empty"}), 400
    if not active_agent:
        return jsonify({"response": "LUOKAI offline"}), 200

    def generate():
        try:
            # Check if ReAct agent with streaming is available
            if react_agent and hasattr(react_agent, 'think_stream'):
                for token in react_agent.think_stream(msg):
                    yield f"data: {json.dumps({'token': token})}\n\n"
            else:
                # Fall back to regular think
                resp = active_agent.think(msg)
                yield f"data: {json.dumps({'token': resp})}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive'
        }
    )


def generate_stream(msg):
    """Generator for streaming responses."""
    try:
        if react_agent and hasattr(react_agent, 'think_stream'):
            for token in react_agent.think_stream(msg):
                yield f"data: {json.dumps({'token': token})}\n\n"
        else:
            resp = active_agent.think(msg)
            yield f"data: {json.dumps({'token': resp})}\n\n"
        yield "data: [DONE]\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)})}\n\n"

@app.route("/api/status")
def status():
    """Get agent status."""
    if active_agent:
        return jsonify(active_agent.status())
    return jsonify({"ok": False, "error": "agent not loaded"})

@app.route("/api/models", methods=["GET"])
def list_models():
    """List available models."""
    if react_agent and hasattr(react_agent, '_available_models'):
        return jsonify({"models": react_agent._available_models, "current": react_agent.model})
    return jsonify({"models": [], "current": "unknown"})

@app.route("/api/models/switch", methods=["POST"])
def switch_model():
    """Switch to a different model."""
    data = request.json or {}
    model = data.get("model")
    if not model:
        return jsonify({"error": "model parameter required"}), 400
    if react_agent and hasattr(react_agent, 'model'):
        react_agent.model = model
        return jsonify({"ok": True, "model": model})
    return jsonify({"error": "cannot switch model"}), 400

@app.route("/api/execute", methods=["POST"])
def execute():
    data = request.json or {}
    code = data.get("code","")
    lang = data.get("language","python")
    if not active_agent:
        return jsonify({"output": "LUOKAI offline"}), 200
    if lang == "python":
        out = active_agent.run_python(code)
    else:
        out = active_agent.execute_command(code)
    return jsonify({"output": out, "ok": True})

@app.route("/api/search", methods=["POST"])
def search():
    q = (request.json or {}).get("query","")
    if active_agent:
        return jsonify({"results": active_agent.web_search(q)})
    return jsonify({"results": "Agent offline"})

@app.route("/api/voice/start", methods=["POST"])
def voice_start():
    if not active_agent: return jsonify({"ok": False})
    try:
        active_agent.start_voice()
        return jsonify({"ok": True, "msg": "Voice started - say 'Luo' to wake"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

@app.route("/api/voice/stop", methods=["POST"])
def voice_stop():
    if active_agent: active_agent.stop_voice()
    return jsonify({"ok": True})

@app.route("/api/voice/status")
def voice_status():
    if active_agent and hasattr(active_agent, '_voice') and active_agent._voice:
        return jsonify(active_agent._voice.status())
    return jsonify({"running": False})

@app.route("/api/evolution/start", methods=["POST"])
def evo_start():
    if not active_agent: return jsonify({"ok": False})
    try:
        active_agent.start_evolution()
        return jsonify({"ok": True, "msg": "Co-evolution started"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

@app.route("/api/evolution/stats")
def evo_stats():
    if active_agent and hasattr(active_agent, '_coevo') and active_agent._coevo:
        return jsonify(active_agent._coevo.stats())
    return jsonify({"running": False})

@app.route("/api/memory", methods=["GET"])
def get_memory():
    """Get agent memory."""
    if active_agent and hasattr(active_agent, '_memory'):
        return jsonify({"memory": active_agent._memory, "count": len(active_agent._memory)})
    return jsonify({"memory": {}, "count": 0})

@app.route("/api/memory/recall", methods=["POST"])
def recall_memory():
    """Semantic search through agent memory."""
    data = request.json or {}
    query = data.get("query", "")
    n = data.get("n", 5)
    if active_agent and hasattr(active_agent, 'semantic_recall'):
        results = active_agent.semantic_recall(query, n)
        return jsonify({"results": results})
    return jsonify({"results": []})

@app.route("/api/skills", methods=["GET"])
def list_skills():
    """All categories with skill counts + overall stats."""
    try:
        from luokai.skills import get_library
        lib  = get_library()
        stat = lib.stats()
        return jsonify({"ok": True, **stat})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

@app.route("/api/skills/search", methods=["GET", "POST"])
def skills_search():
    """Search skills. GET ?q=query&limit=20&category=  or  POST {query, limit, category}"""
    try:
        from luokai.skills import get_library
        lib = get_library()
        if request.method == "POST":
            body     = request.json or {}
            q        = body.get("query", body.get("q", ""))
            limit    = int(body.get("limit", 20))
            category = body.get("category", "")
        else:
            q        = request.args.get("q", "")
            limit    = int(request.args.get("limit", 20))
            category = request.args.get("category", "")
        results = lib.search(q, limit=limit, category=category)
        return jsonify({"results": results, "count": len(results), "query": q, "ok": True})
    except Exception as e:
        return jsonify({"results": [], "ok": False, "error": str(e)})

@app.route("/api/skills/categories", methods=["GET"])
def skills_categories():
    """List all skill categories."""
    try:
        from luokai.skills import get_library
        lib  = get_library()
        cats = lib.categories()
        return jsonify({"categories": cats, "count": len(cats), "ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

@app.route("/api/skills/category/<path:cat>", methods=["GET"])
def skills_by_category(cat):
    """Skills in a category. GET /api/skills/category/devops-and-cloud?limit=50"""
    try:
        from luokai.skills import get_library
        lib   = get_library()
        limit = int(request.args.get("limit", 50))
        skills = lib.list_category(cat, limit=limit)
        return jsonify({"skills": skills, "count": len(skills), "category": cat, "ok": True})
    except Exception as e:
        return jsonify({"skills": [], "ok": False, "error": str(e)})

@app.route("/api/skills/get/<path:slug>", methods=["GET"])
def skill_detail(slug):
    """Full skill detail by ID/slug."""
    try:
        from luokai.skills import get_library
        lib   = get_library()
        skill = lib.get(slug)
        if not skill:
            return jsonify({"ok": False, "error": f"Skill '{slug}' not found"}), 404
        return jsonify({"skill": skill, "ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

@app.route("/api/skills/stats", methods=["GET"])
def skills_stats_route():
    """Skills engine statistics."""
    try:
        from luokai.skills import get_library
        lib = get_library()
        return jsonify({"ok": True, **lib.stats()})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

@app.route("/api/skills/random", methods=["GET"])
def skills_random():
    """Get random skills. GET ?n=5&category="""
    try:
        from luokai.skills import get_library
        lib      = get_library()
        n        = int(request.args.get("n", 5))
        category = request.args.get("category", "")
        skills   = lib.random_skills(n=n, category=category)
        return jsonify({"skills": skills, "ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

@app.route("/api/skills/<path:skill_name>", methods=["POST"])
def invoke_skill(skill_name):
    """Invoke a skill by name/ID — returns skill instructions for the agent."""
    try:
        from luokai.skills import get_library
        lib    = get_library()
        body   = request.json or {}
        ctx    = body.get("context", "")
        result = lib.invoke(skill_name, context=ctx)
        return jsonify({**result})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

@app.route("/api/fs/read", methods=["POST"])
def fs_read():
    path = (request.json or {}).get("path","")
    try:
        content = Path(path).expanduser().read_text(errors="replace")[:50000]
        return jsonify({"ok": True, "content": content})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

@app.route("/api/fs/write", methods=["POST"])
def fs_write():
    data    = request.json or {}
    path    = data.get("path","")
    content = data.get("content","")
    try:
        p = Path(path).expanduser()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

@app.route("/api/fs/ls", methods=["POST"])
def fs_ls():
    path = (request.json or {}).get("path","~")
    try:
        p     = Path(path).expanduser()
        items = sorted(p.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
        result = [{"name":i.name,"type":"dir" if i.is_dir() else "file","size":i.stat().st_size if i.is_file() else 0} for i in items[:200]]
        return jsonify({"ok": True, "items": result, "path": str(p)})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

# ── VS Code / code-server API ────────────────────────────────────────

def _vscode_is_running():
    """Check if code-server is listening on its port."""
    import socket
    try:
        with socket.create_connection(("127.0.0.1", VSCODE_PORT), timeout=1):
            return True
    except OSError:
        return False

def _ensure_vscode_config():
    """Write config.yaml if missing."""
    VSCODE_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    VSCODE_WORKSPACE.mkdir(parents=True, exist_ok=True)
    if not VSCODE_CONFIG.exists():
        VSCODE_CONFIG.write_text(
            f"bind-addr: 127.0.0.1:{VSCODE_PORT}\n"
            f"auth: password\n"
            f"password: {VSCODE_PASSWORD}\n"
            f"cert: false\n"
        )

def _vscode_autostart():
    """Try to auto-start code-server if installed."""
    global _vscode_proc
    if _vscode_is_running():
        print("✅ code-server already running")
        return
    if not _find_code_server():
        print("⚠️  code-server not installed — VS Code app will show install prompt")
        return
    _ensure_vscode_config()
    try:
        global _vscode_log
        _vscode_log = open(VSCODE_LOG_FILE, "a")  # kept open for subprocess lifetime
        _vscode_proc = subprocess.Popen(
            ["code-server", "--config", str(VSCODE_CONFIG), str(VSCODE_WORKSPACE)],
            stdout=_vscode_log, stderr=_vscode_log, start_new_session=True
        )
        VSCODE_PID_FILE.write_text(str(_vscode_proc.pid))
        print(f"🖥️  code-server started (PID {_vscode_proc.pid}) on port {VSCODE_PORT}")
    except Exception as e:
        print(f"⚠️  code-server auto-start failed: {e}")

def _find_code_server():
    """Return path to code-server binary, or None."""
    import shutil
    return shutil.which("code-server")

@app.route("/api/vscode/status")
def vscode_status():
    running  = _vscode_is_running()
    installed = _find_code_server() is not None
    return jsonify({
        "ok":        True,
        "running":   running,
        "installed": installed,
        "port":      VSCODE_PORT,
        "url":       f"http://localhost:{VSCODE_PORT}",
        "workspace": str(VSCODE_WORKSPACE),
        "password":  VSCODE_PASSWORD,
    })

@app.route("/api/vscode/start", methods=["POST"])
def vscode_start():
    global _vscode_proc
    if _vscode_is_running():
        return jsonify({"ok": True, "running": True, "msg": "Already running",
                        "url": f"http://localhost:{VSCODE_PORT}"})
    if not _find_code_server():
        return jsonify({"ok": False, "running": False,
                        "msg": "code-server not installed. Run: bash vscode/install_code_server.sh"})
    _ensure_vscode_config()
    try:
        global _vscode_log
        _vscode_log = open(VSCODE_LOG_FILE, "a")  # kept open for subprocess lifetime
        _vscode_proc = subprocess.Popen(
            ["code-server", "--config", str(VSCODE_CONFIG), str(VSCODE_WORKSPACE)],
            stdout=_vscode_log, stderr=_vscode_log, start_new_session=True
        )
        VSCODE_PID_FILE.write_text(str(_vscode_proc.pid))
        # Wait up to 8 seconds for it to bind
        for _ in range(16):
            time.sleep(0.5)
            if _vscode_is_running():
                return jsonify({"ok": True, "running": True,
                                "msg": "code-server started",
                                "url": f"http://localhost:{VSCODE_PORT}",
                                "pid": _vscode_proc.pid})
        return jsonify({"ok": True, "running": False,
                        "msg": "Started but still initializing — try again in a moment",
                        "url": f"http://localhost:{VSCODE_PORT}"})
    except Exception as e:
        return jsonify({"ok": False, "running": False, "msg": str(e)})

@app.route("/api/vscode/stop", methods=["POST"])
def vscode_stop():
    global _vscode_proc
    stopped = False
    # Kill our tracked process
    if _vscode_proc:
        try:
            _vscode_proc.terminate()
            _vscode_proc.wait(timeout=5)
            stopped = True
        except Exception:
            try: _vscode_proc.kill()
            except Exception: pass
        _vscode_proc = None
    # Also kill by PID file
    if VSCODE_PID_FILE.exists():
        try:
            pid = int(VSCODE_PID_FILE.read_text().strip())
            os.kill(pid, signal.SIGTERM)
            stopped = True
        except Exception: pass
        VSCODE_PID_FILE.unlink(missing_ok=True)
    return jsonify({"ok": True, "stopped": stopped,
                    "msg": "code-server stopped" if stopped else "Was not running"})

@app.route("/api/vscode/install", methods=["POST"])
def vscode_install():
    """Trigger install script in background."""
    script = Path(__file__).parent / "vscode" / "install_code_server.sh"
    if not script.exists():
        return jsonify({"ok": False, "msg": "Install script not found"})
    try:
        proc = subprocess.Popen(
            ["bash", str(script)],
            stdout=open("/tmp/code-server-install.log","w"),  # subprocess handles close
            stderr=subprocess.STDOUT,
            start_new_session=True
        )
        return jsonify({"ok": True, "msg": "Install started in background",
                        "pid": proc.pid,
                        "log": "/tmp/code-server-install.log"})
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)})

# ── Brain API ─────────────────────────────────────────────────────────

def _get_brain():
    a = active_agent
    if a and hasattr(a, "_brain") and a._brain:
        return a._brain
    return None

@app.route("/api/brain/status", methods=["GET"])
def brain_status():
    brain = _get_brain()
    if not brain:
        return jsonify({"ok": False, "error": "Brain not initialized"})
    return jsonify({"ok": True, **brain.status()})

@app.route("/api/brain/memory/store", methods=["POST"])
def brain_memory_store():
    body = request.json or {}
    content = body.get("content", "")
    if not content:
        return jsonify({"ok": False, "error": "content required"})
    brain = _get_brain()
    if not brain:
        return jsonify({"ok": False, "error": "brain offline"})
    brain.store(content, role=body.get("role","observation"),
                importance=float(body.get("importance",0.5)))
    return jsonify({"ok": True, "stored": content[:80]})

@app.route("/api/brain/memory/recall", methods=["GET", "POST"])
def brain_memory_recall():
    if request.method == "POST":
        body = request.json or {}
        query = body.get("query", "")
        limit = int(body.get("limit", 8))
    else:
        query = request.args.get("q", "")
        limit = int(request.args.get("limit", 8))
    brain = _get_brain()
    if not brain:
        return jsonify({"ok": False, "results": [], "error": "brain offline"})
    results = brain.recall(query=query, limit=limit)
    return jsonify({"ok": True, "results": results, "count": len(results), "query": query})

@app.route("/api/brain/memory/wake", methods=["GET"])
def brain_wake():
    brain = _get_brain()
    if not brain or not brain.memory:
        return jsonify({"ok": False, "context": "", "error": "brain/memory offline"})
    try:
        ctx = brain.memory.wake_up(max_tokens=1000)
        return jsonify({"ok": True, "context": ctx})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

@app.route("/api/brain/memory/dream", methods=["POST"])
def brain_dream():
    brain = _get_brain()
    if not brain or not brain.memory:
        return jsonify({"ok": False, "error": "brain/memory offline"})
    try:
        brain.memory.dream()
        return jsonify({"ok": True, "msg": "Dream consolidation triggered"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

@app.route("/api/brain/goals", methods=["GET"])
def brain_goals():
    brain = _get_brain()
    if not brain:
        return jsonify({"ok": False, "goals": [], "error": "brain offline"})
    return jsonify({"ok": True, "goals": brain.get_goals()})

@app.route("/api/brain/goals", methods=["POST"])
def brain_set_goal():
    body = request.json or {}
    desc = body.get("description", "")
    if not desc:
        return jsonify({"ok": False, "error": "description required"})
    brain = _get_brain()
    if not brain:
        return jsonify({"ok": False, "error": "brain offline"})
    brain.set_goal(desc, priority=int(body.get("priority", 5)))
    return jsonify({"ok": True, "set": desc})

@app.route("/api/brain/skills/learned", methods=["GET"])
def brain_learned_skills():
    brain = _get_brain()
    if not brain:
        return jsonify({"ok": False, "skills": [], "error": "brain offline"})
    return jsonify({"ok": True, "skills": brain.get_learned_skills()})

@app.route("/api/brain/fact", methods=["POST"])
def brain_learn_fact():
    body = request.json or {}
    key, value = body.get("key",""), body.get("value","")
    if not key or not value:
        return jsonify({"ok": False, "error": "key and value required"})
    brain = _get_brain()
    if not brain:
        return jsonify({"ok": False, "error": "brain offline"})
    brain.learn_fact(key, value, float(body.get("confidence", 0.9)))
    return jsonify({"ok": True, "learned": {key: value}})

@app.route("/api/brain/coevo/stats", methods=["GET"])
def brain_coevo_stats():
    brain = _get_brain()
    if not brain or not brain.coevo:
        return jsonify({"ok": False, "error": "coevo offline"})
    try:
        return jsonify({"ok": True, **brain.coevo.stats()})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

@app.route("/api/config/key", methods=["POST"])
def config_save_key():
    """Save an API key to ~/.luo_os/config.json."""
    body = request.json or {}
    key, value = body.get("key",""), body.get("value","")
    if not key or not value:
        return jsonify({"ok": False, "error": "key and value required"})
    try:
        from setup_luoos import CONFIG_PATH, load_config
        import json as _json
        cfg = load_config()
        if "api_keys" not in cfg:
            cfg["api_keys"] = {}
        cfg["api_keys"][key] = value
        CONFIG_PATH.write_text(_json.dumps(cfg, indent=2))
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

@app.route("/api/model/status", methods=["GET"])
def model_status():
    """Get local model engine status."""
    try:
        from luokai.core.model_engine import get_engine
        return jsonify({"ok": True, **get_engine().status()})
    except Exception as e:
        return jsonify({"ok": False, "ready": False, "loading": False, "error": str(e)})

@app.route("/api/model/list", methods=["GET"])
def model_list():
    """List available models."""
    try:
        from luokai.core.model_engine import get_engine
        return jsonify({"ok": True, "models": get_engine().list_available_models()})
    except Exception as e:
        return jsonify({"ok": False, "models": [], "error": str(e)})



# ════════════════════════════════════════════════════════════════
# LUO BROWSER ENGINE — Headless Chromium via Playwright
# Full JS execution, cookies, sessions — every site works
# ════════════════════════════════════════════════════════════════

_pw_browser   = None   # persistent browser instance
_pw_context   = None   # persistent browser context (cookies/session)
_pw_lock      = threading.Lock()
_pw_ready     = False
_pw_error     = None

def _ensure_playwright():
    """Boot Playwright + Chromium once, reuse across all requests."""
    global _pw_browser, _pw_context, _pw_ready, _pw_error
    if _pw_ready:
        return True
    with _pw_lock:
        if _pw_ready:
            return True
        try:
            from playwright.sync_api import sync_playwright
            import subprocess, sys as _sys

            # Auto-install Chromium if not present
            try:
                _pw_instance = sync_playwright().start()
                _pw_browser  = _pw_instance.chromium.launch(
                    headless=True,
                    args=[
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-gpu",
                        "--disable-web-security",
                        "--disable-features=IsolateOrigins,site-per-process",
                        "--window-size=1280,800",
                    ]
                )
            except Exception:
                # Chromium not installed — install it now
                subprocess.run(
                    [_sys.executable, "-m", "playwright", "install", "chromium"],
                    capture_output=True, timeout=300
                )
                _pw_instance = sync_playwright().start()
                _pw_browser  = _pw_instance.chromium.launch(
                    headless=True,
                    args=["--no-sandbox","--disable-setuid-sandbox",
                          "--disable-dev-shm-usage","--disable-gpu"]
                )

            _pw_context = _pw_browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1280, "height": 800},
                locale="en-US",
                timezone_id="America/New_York",
            )
            _pw_ready = True
            print("[LuoBrowser] ✅ Headless Chromium ready")
            return True
        except Exception as e:
            _pw_error = str(e)
            print(f"[LuoBrowser] ❌ Chromium unavailable: {e}")
            return False

def _fallback_fetch(url):
    """urllib fallback for environments without Chromium."""
    import urllib.request as ur, re as _re
    from urllib.parse import urljoin
    req = ur.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0",
        "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    })
    with ur.urlopen(req, timeout=15) as resp:
        raw        = resp.read(3 * 1024 * 1024)
        ctype      = resp.headers.get("Content-Type", "text/html")
        final_url  = resp.url
    charset = "utf-8"
    for p in ctype.split(";"):
        p = p.strip()
        if p.lower().startswith("charset="):
            charset = p.split("=", 1)[1].strip()
    html = raw.decode(charset, errors="replace")
    def abs_url(v):
        if not v or v.startswith(("http","data:","mailto:","javascript:","#","blob:")):
            return v
        return urljoin(final_url, v)
    html = _re.sub(r'(src|href|action)=(\x22)([^\x22]*)(\x22)',
        lambda m: m.group(1)+"="+m.group(2)+abs_url(m.group(3))+m.group(4),
        html, flags=_re.I)
    html = _re.sub(r"(src|href|action)=(\x27)([^\x27]*)(\x27)",
        lambda m: m.group(1)+"="+m.group(2)+abs_url(m.group(3))+m.group(4),
        html, flags=_re.I)
    html = _re.sub(r"(<head[^>]*>)",
        '<base href="' + final_url + '">\\1', html, count=1, flags=_re.I)
    tm    = _re.search(r"<title[^>]*>(.*?)</title>", html, _re.I|_re.S)
    title = tm.group(1).strip() if tm else final_url
    return {"ok": True, "html": html, "url": final_url,
            "title": title, "engine": "urllib"}


@app.route("/api/browser/fetch", methods=["POST"])
def browser_fetch():
    """
    Fetch any URL using headless Chromium (full JS, no iframe limits).
    Falls back to urllib proxy if Chromium is unavailable.
    """
    body = request.json or {}
    url  = body.get("url", "").strip()
    if not url:
        return jsonify({"ok": False, "error": "No URL"})
    if not url.startswith("http"):
        url = "https://" + url

    # ── Try Playwright / Chromium first ──────────────────────────
    if _ensure_playwright():
        try:
            with _pw_lock:
                page = _pw_context.new_page()
                try:
                    # Block heavy media to speed up loading
                    page.route("**/*.{mp4,webm,ogg,mp3,wav,flac,aac,woff,woff2,ttf,eot}",
                               lambda r: r.abort())

                    page.goto(url, timeout=25000, wait_until="domcontentloaded")
                    # Give JS a moment to render
                    page.wait_for_timeout(1800)

                    final_url = page.url
                    title     = page.title()
                    html      = page.content()

                    # Take screenshot for thumbnail (base64 PNG, max 400px wide)
                    screenshot = page.screenshot(
                        type="png", full_page=False,
                        clip={"x":0,"y":0,"width":1280,"height":800}
                    )
                    import base64
                    thumb_b64 = base64.b64encode(screenshot).decode()

                    return jsonify({
                        "ok":        True,
                        "html":      html,
                        "url":       final_url,
                        "title":     title,
                        "thumb":     thumb_b64,   # PNG screenshot
                        "engine":    "chromium",
                    })
                finally:
                    page.close()
        except Exception as e:
            print(f"[LuoBrowser] Chromium page error: {e}")
            # fall through to urllib

    # ── urllib fallback ───────────────────────────────────────────
    try:
        result = _fallback_fetch(url)
        return jsonify(result)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "url": url})


@app.route("/api/browser/screenshot", methods=["POST"])
def browser_screenshot():
    """Return a PNG screenshot of a URL (base64 encoded)."""
    body = request.json or {}
    url  = body.get("url", "").strip()
    if not url or not url.startswith("http"):
        url = "https://" + url
    if not _ensure_playwright():
        return jsonify({"ok": False, "error": "Chromium not available"})
    try:
        with _pw_lock:
            page = _pw_context.new_page()
            try:
                page.goto(url, timeout=20000, wait_until="domcontentloaded")
                page.wait_for_timeout(2000)
                import base64
                png   = page.screenshot(full_page=False)
                b64   = base64.b64encode(png).decode()
                title = page.title()
                url_f = page.url
                return jsonify({"ok": True, "screenshot": b64,
                                "title": title, "url": url_f})
            finally:
                page.close()
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.route("/api/browser/search", methods=["POST"])
def browser_search():
    """Search DuckDuckGo via headless Chromium, return full results HTML."""
    body  = request.json or {}
    query = body.get("query", "").strip()
    if not query:
        return jsonify({"ok": False, "error": "No query"})
    import urllib.parse
    search_url = "https://duckduckgo.com/?q=" + urllib.parse.quote(query) + "&ia=web"
    body["url"] = search_url
    return browser_fetch()


@app.route("/api/browser/status", methods=["GET"])
def browser_status():
    """Check if headless Chromium is ready."""
    return jsonify({
        "ok":     True,
        "ready":  _pw_ready,
        "engine": "chromium" if _pw_ready else "urllib",
        "error":  _pw_error,
    })




# ════════════════════════════════════════════════════════════════
# LUO-WORLDMONITOR — Global intelligence dashboard integration
# Proxies live RSS feeds, serves worldmonitor data inside LuoOS
# Source: https://github.com/koala73/worldmonitor (in apps/luo-worldmonitor)
# ════════════════════════════════════════════════════════════════

import xml.etree.ElementTree as _ET

# Curated RSS feeds from worldmonitor source config — no API key needed
_WM_FEEDS = {
    "top":      "https://feeds.bbci.co.uk/news/world/rss.xml",
    "us":       "https://www.cbsnews.com/latest/rss/main",
    "tech":     "https://feeds.feedburner.com/TechCrunch",
    "defense":  "https://www.defensenews.com/arc/outboundfeeds/rss/?outputType=xml",
    "finance":  "https://news.google.com/rss/search?q=markets+stocks+economy&hl=en-US&gl=US&ceid=US:en",
    "science":  "https://export.arxiv.org/rss/cs.LG",
    "middle_east": "https://www.theguardian.com/world/middleeast/rss",
    "climate":  "https://news.google.com/rss/search?q=climate+disaster+extreme+weather&hl=en-US&gl=US&ceid=US:en",
    "health":   "https://news.google.com/rss/search?q=health+disease+pandemic&hl=en-US&gl=US&ceid=US:en",
    "space":    "https://www.nasa.gov/rss/dyn/breaking_news.rss",
}

def _fetch_rss(url, max_items=12):
    """Fetch and parse RSS feed, return list of items."""
    import urllib.request as _ur
    req = _ur.Request(url, headers={
        "User-Agent": "LuoOS-WorldMonitor/1.0",
        "Accept": "application/rss+xml, application/xml, text/xml",
    })
    try:
        with _ur.urlopen(req, timeout=8) as r:
            raw = r.read(1024 * 512)
    except Exception as e:
        return []
    try:
        root = _ET.fromstring(raw.decode("utf-8", errors="replace"))
    except Exception:
        return []
    ns   = {"media": "http://search.yahoo.com/mrss/"}
    chan = root.find("channel") or root
    items = []
    for item in chan.findall("item")[:max_items]:
        def t(tag):
            el = item.find(tag)
            return (el.text or "").strip() if el is not None else ""
        # Extract image from media:thumbnail or enclosure
        img = ""
        mt = item.find("media:thumbnail", ns)
        if mt is not None:
            img = mt.get("url", "")
        enc = item.find("enclosure")
        if not img and enc is not None:
            img = enc.get("url", "")
        items.append({
            "title":       t("title"),
            "link":        t("link"),
            "description": t("description")[:200],
            "pubDate":     t("pubDate"),
            "source":      t("source") or t("author"),
            "image":       img,
        })
    return items


@app.route("/api/worldmonitor/feed", methods=["GET", "POST"])
def worldmonitor_feed():
    """Fetch live news feed by category."""
    body     = request.json or {}
    category = (request.args.get("category") or body.get("category", "top")).lower()
    max_items= int(request.args.get("max") or body.get("max", 12))
    url      = _WM_FEEDS.get(category, _WM_FEEDS["top"])
    items    = _fetch_rss(url, max_items)
    return jsonify({"ok": True, "category": category, "items": items,
                    "source_url": url, "count": len(items)})


@app.route("/api/worldmonitor/multi", methods=["POST"])
def worldmonitor_multi():
    """Fetch multiple categories at once (parallel)."""
    from concurrent.futures import ThreadPoolExecutor, as_completed
    body       = request.json or {}
    categories = body.get("categories", ["top", "tech", "finance", "defense"])[:6]
    max_each   = body.get("max", 6)

    results = {}
    with ThreadPoolExecutor(max_workers=4) as ex:
        futures = {
            ex.submit(_fetch_rss, _WM_FEEDS.get(c, _WM_FEEDS["top"]), max_each): c
            for c in categories if c in _WM_FEEDS
        }
        for future in as_completed(futures, timeout=10):
            cat = futures[future]
            try:
                results[cat] = future.result()
            except Exception:
                results[cat] = []

    return jsonify({"ok": True, "results": results,
                    "categories": list(results.keys())})


@app.route("/api/worldmonitor/categories", methods=["GET"])
def worldmonitor_categories():
    """List available feed categories."""
    return jsonify({
        "ok":         True,
        "categories": list(_WM_FEEDS.keys()),
        "feeds":      {k: v for k, v in _WM_FEEDS.items()}
    })


@app.route("/api/worldmonitor/status", methods=["GET"])
def worldmonitor_status():
    """Health check for worldmonitor integration."""
    return jsonify({
        "ok":         True,
        "integrated": True,
        "feeds":      len(_WM_FEEDS),
        "source":     "https://github.com/koala73/worldmonitor",
        "local_path": "apps/luo-worldmonitor",
    })



# ════════════════════════════════════════════════════════════════
# CONVERSATION MEMORY — persists across sessions
# Saves to ~/.luo_os/memory.json, injects context into every chat
# ════════════════════════════════════════════════════════════════
import json as _json_mem

_MEMORY_FILE = Path.home() / ".luo_os" / "memory.json"
_chat_history = []   # in-memory list of {role, content, ts}

def _load_memory():
    global _chat_history
    try:
        if _MEMORY_FILE.exists():
            data = _json_mem.loads(_MEMORY_FILE.read_text())
            _chat_history = data.get("history", [])[-200:]  # keep last 200
    except Exception:
        _chat_history = []

def _save_memory():
    try:
        _MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        _MEMORY_FILE.write_text(_json_mem.dumps({
            "history": _chat_history[-200:],
            "saved_at": time.strftime("%Y-%m-%dT%H:%M:%S")
        }, indent=2))
    except Exception:
        pass

def _get_context_messages(new_msg: str, n: int = 12) -> list:
    """Return last n turns as context for the inference engine."""
    recent = _chat_history[-n*2:]
    msgs = [{"role": m["role"], "content": m["content"]} for m in recent]
    msgs.append({"role": "user", "content": new_msg})
    return msgs

# Load memory on startup
_load_memory()

@app.route("/api/memory/history", methods=["GET"])
def memory_history():
    n = int(request.args.get("n", 50))
    return jsonify({"ok": True, "history": _chat_history[-n:],
                    "total": len(_chat_history)})

@app.route("/api/memory/clear", methods=["POST"])
def memory_clear():
    global _chat_history
    _chat_history = []
    _save_memory()
    return jsonify({"ok": True, "message": "Memory cleared"})

@app.route("/api/memory/save", methods=["POST"])
def memory_save_endpoint():
    _save_memory()
    return jsonify({"ok": True})



# ════════════════════════════════════════════════════════════════
# FILE SYSTEM API
# ════════════════════════════════════════════════════════════════
import glob as _glob

def _resolve_path(path: str) -> str:
    """Resolve ~ and make safe."""
    if not path or path == '~':
        return str(Path.home())
    path = path.replace('~', str(Path.home()))
    return str(Path(path).resolve())

@app.route("/api/fs/ls", methods=["POST"])
def fs_ls():
    body = request.json or {}
    try:
        p = Path(_resolve_path(body.get("path", "~")))
        if not p.exists():
            return jsonify({"ok": False, "error": "Path not found"})
        items = []
        for child in sorted(p.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
            try:
                stat = child.stat()
                items.append({
                    "name":   child.name,
                    "type":   "dir" if child.is_dir() else "file",
                    "size":   stat.st_size if child.is_file() else 0,
                    "is_dir": child.is_dir(),
                    "mtime":  stat.st_mtime,
                })
            except PermissionError:
                pass
        return jsonify({"ok": True, "items": items, "path": str(p)})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

@app.route("/api/fs/read", methods=["POST"])
def fs_read():
    body = request.json or {}
    try:
        p = Path(_resolve_path(body.get("path", "")))
        if not p.exists() or not p.is_file():
            return jsonify({"ok": False, "error": "File not found"})
        if p.stat().st_size > 2 * 1024 * 1024:
            return jsonify({"ok": False, "error": "File too large (>2MB)"})
        content_text = p.read_text(errors="replace")
        return jsonify({"ok": True, "content": content_text, "path": str(p)})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

@app.route("/api/fs/write", methods=["POST"])
def fs_write():
    body = request.json or {}
    try:
        p = Path(_resolve_path(body.get("path", "")))
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body.get("content", ""))
        return jsonify({"ok": True, "path": str(p)})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

@app.route("/api/fs/delete", methods=["POST"])
def fs_delete():
    body = request.json or {}
    try:
        p = Path(_resolve_path(body.get("path", "")))
        if not p.exists():
            return jsonify({"ok": False, "error": "Not found"})
        if p.is_dir():
            import shutil
            shutil.rmtree(p)
        else:
            p.unlink()
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

@app.route("/api/fs/mkdir", methods=["POST"])
def fs_mkdir():
    body = request.json or {}
    try:
        p = Path(_resolve_path(body.get("path", "")))
        p.mkdir(parents=True, exist_ok=True)
        return jsonify({"ok": True, "path": str(p)})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

# ════════════════════════════════════════════════════════════════
# TERMINAL EXECUTE API — real shell commands
# ════════════════════════════════════════════════════════════════
import subprocess as _subp

_term_cwd = str(Path.home())

@app.route("/api/execute", methods=["POST"])
def execute_command():
    global _term_cwd
    body    = request.json or {}
    command = body.get("command", "").strip()
    cwd     = body.get("cwd", _term_cwd)
    if not command:
        return jsonify({"ok": False, "error": "No command"})

    # Safety: block obviously dangerous commands
    blocked = ["rm -rf /", "mkfs", "dd if=/dev/", ":(){:|:&}", "chmod 777 /"]
    if any(b in command for b in blocked):
        return jsonify({"ok": False, "output": "⛔ Command blocked for safety"})

    # Handle cd specially
    if command.startswith("cd "):
        new_path = command[3:].strip().replace("~", str(Path.home()))
        try:
            resolved = str(Path(cwd).joinpath(new_path).resolve())
            if Path(resolved).is_dir():
                _term_cwd = resolved
                return jsonify({"ok": True, "output": "", "cwd": _term_cwd})
            return jsonify({"ok": True, "output": f"cd: {new_path}: No such directory", "cwd": _term_cwd})
        except Exception as e:
            return jsonify({"ok": True, "output": str(e), "cwd": _term_cwd})

    if command == "cd":
        _term_cwd = str(Path.home())
        return jsonify({"ok": True, "output": "", "cwd": _term_cwd})

    try:
        # Resolve cwd
        cwd_path = Path(cwd.replace("~", str(Path.home())))
        if not cwd_path.exists():
            cwd_path = Path.home()

        result = _subp.run(
            command, shell=True, cwd=str(cwd_path),
            capture_output=True, text=True, timeout=15,
            env={**os.environ, "TERM": "xterm-256color"}
        )
        output = (result.stdout + result.stderr).strip()
        return jsonify({"ok": True, "output": output, "cwd": str(cwd_path),
                        "returncode": result.returncode})
    except _subp.TimeoutExpired:
        return jsonify({"ok": False, "output": "Command timed out (15s limit)"})
    except Exception as e:
        return jsonify({"ok": False, "output": str(e)})



# ════════════════════════════════════════════════════════════════
# LUO-BLENDER — Three.js 3D Editor (self-hosted, no install)
# ════════════════════════════════════════════════════════════════
@app.route("/luo-blender/")
@app.route("/luo-blender")
def luo_blender_index():
    """Serve the Three.js 3D editor."""
    editor_path = Path(__file__).parent / "apps" / "luo-3d-editor"
    return send_from_directory(str(editor_path), "index.html")

@app.route("/luo-blender/<path:filename>")
def luo_blender_static(filename):
    """Serve Three.js editor assets."""
    # Check editor folder first
    base_path = Path(__file__).parent / "apps" / "luo-3d-editor"
    return send_from_directory(str(base_path), filename)

@app.route("/luo-3d-editor-assets/<path:filename>")
def luo_blender_assets(filename):
    """Serve Three.js build and examples from parent directory."""
    base_path = Path(__file__).parent / "apps" / "luo-3d-editor"
    return send_from_directory(str(base_path), filename)


# ════════════════════════════════════════════════════════════════
# HEALTH, FILE SERVE, SEARCH, STREAMING, TEMP
# ════════════════════════════════════════════════════════════════
import datetime as _dt

_server_start = time.time()

@app.route("/api/health", methods=["GET"])
def health():
    uptime_s = int(time.time() - _server_start)
    h, m, s  = uptime_s//3600, (uptime_s%3600)//60, uptime_s%60
    try:
        from luokai.core.model_engine import get_engine
        model_ready = get_engine().is_ready
    except Exception:
        model_ready = False
    try:
        from setup_luoos import load_config
        cfg = load_config()
        memory_count = len(_chat_history)
    except Exception:
        cfg = {}; memory_count = 0
    return jsonify({
        "ok":           True,
        "status":       "running",
        "version":      "1.0.0",
        "uptime":       f"{h:02d}:{m:02d}:{s:02d}",
        "uptime_s":     uptime_s,
        "model_ready":  model_ready,
        "memory_count": memory_count,
        "chromium":     _pw_ready,
        "port":         int(os.environ.get("LUO_PORT", 3000)),
    })

@app.route("/api/serve-file", methods=["GET"])
def serve_file():
    """Serve a local file for the image viewer."""
    path = request.args.get("path", "")
    if not path:
        return "No path", 400
    try:
        p = Path(_resolve_path(path))
        if not p.exists() or not p.is_file():
            return "Not found", 404
        import mimetypes
        mime, _ = mimetypes.guess_type(str(p))
        return send_from_directory(str(p.parent), p.name, mimetype=mime or "application/octet-stream")
    except Exception as e:
        return str(e), 500

@app.route("/api/fs/search", methods=["POST"])
def fs_search():
    """Search for files by name recursively."""
    body  = request.json or {}
    query = body.get("query", "").strip().lower()
    path  = body.get("path", "~")
    if not query:
        return jsonify({"ok": False, "error": "No query"})
    try:
        base    = Path(_resolve_path(path))
        results = []
        for p in base.rglob("*"):
            if query in p.name.lower():
                results.append({
                    "name":   p.name,
                    "path":   str(p),
                    "is_dir": p.is_dir(),
                    "size":   p.stat().st_size if p.is_file() else 0,
                })
            if len(results) >= 50:
                break
        return jsonify({"ok": True, "results": results, "count": len(results)})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

@app.route("/api/chat/stream", methods=["POST"])
def chat_stream():
    """SSE streaming response from LUOKAI."""
    body = request.json or {}
    msg  = body.get("message", "").strip()
    if not msg:
        return jsonify({"ok": False, "error": "Empty"})

    def generate():
        try:
            context  = _get_context_messages(msg, n=10)
            eng      = _get_inference()
            response = eng.generate(context)
            if not response:
                response = "I could not generate a response."
            # Stream word by word
            words = response.split(" ")
            for i, word in enumerate(words):
                chunk = word + (" " if i < len(words)-1 else "")
                yield "data: " + chunk + "\n\n"
                time.sleep(0.02)  # ~50 words/sec
            yield "data: [DONE]\n\n"
            # Save to memory
            _chat_history.append({"role":"user","content":msg,"ts":time.strftime("%H:%M")})
            _chat_history.append({"role":"assistant","content":response,"ts":time.strftime("%H:%M")})
            _save_memory()
        except Exception as e:
            yield "data: Error: " + str(e) + "\n\n"

            yield "data: [DONE]\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={"Cache-Control":"no-cache","X-Accel-Buffering":"no"}
    )

@app.route("/api/config/temperature", methods=["POST"])
def set_temperature():
    """Set LUOKAI inference temperature."""
    body = request.json or {}
    temp = float(body.get("temperature", 0.7))
    os.environ["LUOKAI_TEMPERATURE"] = str(temp)
    return jsonify({"ok": True, "temperature": temp})



# ════════════════════════════════════════════════════════════════
# HAND TRACKER — serves the MediaPipe gesture recognition page
# ════════════════════════════════════════════════════════════════
@app.route("/hand-tracker")
@app.route("/hand-tracker/")
def hand_tracker():
    """Serve the hand tracking page."""
    tracker_path = Path(__file__).parent / "luokai" / "vision"
    return send_from_directory(str(tracker_path), "hand_tracker.html")

@app.route("/hand-tracker/<path:filename>")
def hand_tracker_assets(filename):
    tracker_path = Path(__file__).parent / "luokai" / "vision"
    return send_from_directory(str(tracker_path), filename)


# ════════════════════════════════════════════════════════════════
# LUO ULTRA — Pillars 1, 3, 4, 6 server endpoints
# ════════════════════════════════════════════════════════════════

# ── Pillar 1: Perception ─────────────────────────────────────────
@app.route("/perception")
@app.route("/perception/")
def perception_page():
    return send_from_directory(
        str(Path(__file__).parent / "luokai" / "vision"),
        "perception.html"
    )

# ── Pillar 3: Agentic LUOKAI ─────────────────────────────────────
@app.route("/api/agent/chat", methods=["POST"])
def agent_chat():
    """Run LUOKAI in agent mode — executes tools, multi-step plans."""
    try:
        from luokai.agent import run_agent
        body = request.json or {}
        msg  = body.get("message", "").strip()
        if not msg:
            return jsonify({"ok": False, "error": "Empty"})

        eng = _get_inference()
        def infer_fn(history):
            return eng.generate(history)

        result = run_agent(msg, infer_fn, max_steps=5)
        return jsonify({"ok": True, **result})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.route("/api/agent/pending", methods=["GET"])
def agent_pending():
    """UI polls this to get pending tool actions."""
    try:
        from luokai.agent import get_pending_actions
        return jsonify({"ok": True, "actions": get_pending_actions()})
    except Exception:
        return jsonify({"ok": True, "actions": []})


@app.route("/api/agent/report", methods=["POST"])
def agent_report():
    """UI reports back the result of a tool execution."""
    try:
        from luokai.agent import report_result
        body = request.json or {}
        report_result(body.get("id", ""), body.get("result"))
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.route("/api/agent/tools", methods=["GET"])
def agent_tools():
    """List all available tools."""
    try:
        from luokai.agent.tools import TOOLS
        return jsonify({"ok": True, "tools": TOOLS})
    except Exception:
        return jsonify({"ok": False, "tools": {}})


# ── Pillar 4: Mind Canvas (state persistence) ────────────────────
_CANVAS_PATH = Path.home() / ".luo_os" / "mind_canvas.json"

@app.route("/api/canvas/save", methods=["POST"])
def canvas_save():
    body = request.json or {}
    try:
        _CANVAS_PATH.parent.mkdir(parents=True, exist_ok=True)
        _CANVAS_PATH.write_text(json.dumps(body, indent=2))
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.route("/api/canvas/load", methods=["GET"])
def canvas_load():
    try:
        if _CANVAS_PATH.exists():
            return jsonify({"ok": True, "data": json.loads(_CANVAS_PATH.read_text())})
        return jsonify({"ok": True, "data": {"nodes": [], "edges": []}})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


# ── Pillar 6: Dream Engine (background cognition) ────────────────
_DREAMS_PATH = Path.home() / ".luo_os" / "dreams.json"
_dream_state = {"running": False, "thread": None, "last_run": 0, "dreams": []}


def _load_dreams():
    if _DREAMS_PATH.exists():
        try:
            _dream_state["dreams"] = json.loads(_DREAMS_PATH.read_text())
        except Exception:
            _dream_state["dreams"] = []
    else:
        _dream_state["dreams"] = []


def _save_dreams():
    try:
        _DREAMS_PATH.parent.mkdir(parents=True, exist_ok=True)
        _DREAMS_PATH.write_text(json.dumps(_dream_state["dreams"][-50:], indent=2))
    except Exception:
        pass


def _dream_loop():
    """Run idle cognition: replay conversations, find patterns."""
    import time as _t
    while _dream_state["running"]:
        _t.sleep(60)  # check every minute
        # Only dream if user has been idle for 5 minutes
        if _t.time() - _dream_state.get("last_activity", _t.time()) < 300:
            continue
        if _t.time() - _dream_state["last_run"] < 600:
            continue  # don't dream more often than every 10 min

        try:
            # Get recent conversation
            if not _chat_history:
                continue
            recent = _chat_history[-20:]
            recent_text = "\n".join(f"{m['role']}: {m['content']}" for m in recent)

            # Ask LUOKAI to extract patterns/insights
            prompt = (
                "You are LUOKAI in dream-state. Review the user's recent conversation and "
                "extract: 1) 3 key topics, 2) 1 pattern you notice, 3) 1 question you'd "
                "ask the user tomorrow, 4) 1 connection between ideas they may have missed.\n\n"
                "Conversation:\n" + recent_text[:2000]
            )
            try:
                eng = _get_inference()
                response = eng.generate([{"role": "user", "content": prompt}])
            except Exception:
                response = "Cannot dream without inference engine."

            dream = {
                "ts":      _t.strftime("%Y-%m-%d %H:%M"),
                "content": response[:600] if response else "",
                "msgs_processed": len(recent),
            }
            _dream_state["dreams"].append(dream)
            _save_dreams()
            _dream_state["last_run"] = _t.time()
            print(f"[LuoDream] Dream generated: {dream['ts']}")
        except Exception as e:
            print(f"[LuoDream] Error: {e}")


@app.route("/api/dreams/list", methods=["GET"])
def dreams_list():
    _load_dreams()
    return jsonify({
        "ok":      True,
        "dreams":  _dream_state["dreams"][-20:],
        "running": _dream_state["running"],
    })


@app.route("/api/dreams/start", methods=["POST"])
def dreams_start():
    if _dream_state["running"]:
        return jsonify({"ok": True, "status": "already running"})
    _dream_state["running"] = True
    _dream_state["last_run"] = time.time()
    _dream_state["last_activity"] = time.time()
    t = threading.Thread(target=_dream_loop, daemon=True, name="LuoDreamEngine")
    t.start()
    _dream_state["thread"] = t
    return jsonify({"ok": True, "status": "started"})


@app.route("/api/dreams/stop", methods=["POST"])
def dreams_stop():
    _dream_state["running"] = False
    return jsonify({"ok": True, "status": "stopped"})


@app.route("/api/dreams/poke", methods=["POST"])
def dreams_poke():
    """Update last activity timestamp — UI calls this on user interaction."""
    _dream_state["last_activity"] = time.time()
    return jsonify({"ok": True})


# Auto-start dream engine
threading.Thread(target=lambda: (time.sleep(30), dreams_start()),
                 daemon=True, name="LuoDreamBoot").start()


@app.after_request
def cors(r):
    r.headers["Access-Control-Allow-Origin"]  = "*"
    r.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    r.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return r

def _run_server():
    """Start the LuoOS server. Called by start.py or directly."""
    import atexit
    port = int(os.environ.get("LUO_PORT", 3000))

    def _shutdown():
        brain = _get_brain()
        if brain:
            brain.shutdown()
    atexit.register(_shutdown)

    # Boot LUOKAI model engine in background (uses model chosen during setup)
    try:
        from luokai.core.model_engine import boot_engine, set_active_model
        if _LUO_MODEL != "none":
            set_active_model(_LUO_MODEL)
        boot_engine()
    except Exception:
        pass

    # Pre-warm headless Chromium so first browser request is fast
    threading.Thread(
        target=_ensure_playwright, daemon=True, name="LuoBrowserInit"
    ).start()

    threading.Thread(target=_vscode_autostart, daemon=True).start()
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True, use_reloader=False)

if __name__ == "__main__":
    _run_server()
