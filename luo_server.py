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
import sys, json, time, threading, subprocess
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory, Response, stream_with_context
from flask_cors import CORS

sys.path.insert(0, str(Path(__file__).parent))

app     = Flask(__name__, static_folder=".", static_url_path="")
CORS(app)

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
    """List available skills."""
    try:
        from luokai.skills import list_all_skills, SKILL_COUNT
        return jsonify({"skills": list_all_skills(), "count": SKILL_COUNT})
    except Exception as e:
        return jsonify({"skills": {}, "count": 0, "error": str(e)})

@app.route("/api/skills/<skill_name>", methods=["POST"])
def execute_skill(skill_name):
    """Execute a skill."""
    data = request.json or {}
    try:
        from luokai.skills import registry
        result = registry.execute(skill_name, **data)
        return jsonify({"result": result, "ok": True})
    except Exception as e:
        return jsonify({"error": str(e), "ok": False}, 400)

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

@app.after_request
def cors(r):
    r.headers["Access-Control-Allow-Origin"]  = "*"
    r.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    r.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return r

if __name__ == "__main__":
    import webbrowser
    print("\n" + "="*60)
    print("  LuoOS Server")
    print("  http://localhost:3000")
    print("="*60 + "\n")
    threading.Thread(target=lambda: (time.sleep(2), webbrowser.open("http://localhost:3000")), daemon=True).start()
    app.run(host="0.0.0.0", port=3000, debug=False, threaded=True)
