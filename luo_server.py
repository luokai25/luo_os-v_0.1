#!/usr/bin/env python3
"""
LuoOS Server — Main backend
Serves the full browser-based OS + LUOKAI AI API
Port 3000 (sandbox OS) + 7070 (LUOKAI API)
"""
import sys, json, time, threading, subprocess
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

sys.path.insert(0, str(Path(__file__).parent))

app     = Flask(__name__, static_folder=".", static_url_path="")
CORS(app)

# ── Boot LUOKAI ──────────────────────────────────────────────────────
print("🚀 Booting LUOKAI Agent...")
try:
    from luokai.core.luokai_agent import LUOKAIAgent
    agent = LUOKAIAgent()
    AGENT_OK = True
    print("✅ LUOKAI Agent ready")
except Exception as e:
    print(f"⚠️  LUOKAI Agent error: {e}")
    AGENT_OK = False
    agent = None

# ── Routes ───────────────────────────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@app.route("/<path:path>")
def static_files(path):
    return send_from_directory(".", path)

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.json or {}
    msg  = data.get("message","").strip()
    if not msg:
        return jsonify({"error": "empty"}), 400
    if not agent:
        return jsonify({"response": "LUOKAI offline — check requirements"}), 200
    try:
        resp = agent.think(msg)
        return jsonify({"response": resp, "ok": True})
    except Exception as e:
        return jsonify({"response": f"Error: {e}", "ok": False})

@app.route("/api/status")
def status():
    if agent:
        return jsonify(agent.status())
    return jsonify({"ok": False, "error": "agent not loaded"})

@app.route("/api/execute", methods=["POST"])
def execute():
    data = request.json or {}
    code = data.get("code","")
    lang = data.get("language","python")
    if not agent:
        return jsonify({"output": "LUOKAI offline"}), 200
    if lang == "python":
        out = agent.run_python(code)
    else:
        out = agent.execute_command(code)
    return jsonify({"output": out, "ok": True})

@app.route("/api/search", methods=["POST"])
def search():
    q = (request.json or {}).get("query","")
    if agent:
        return jsonify({"results": agent.web_search(q)})
    return jsonify({"results": "Agent offline"})

@app.route("/api/voice/start", methods=["POST"])
def voice_start():
    if not agent: return jsonify({"ok": False})
    try:
        agent.start_voice()
        return jsonify({"ok": True, "msg": "👂 Voice started — say 'Luo' to wake"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

@app.route("/api/voice/stop", methods=["POST"])
def voice_stop():
    if agent: agent.stop_voice()
    return jsonify({"ok": True})

@app.route("/api/voice/status")
def voice_status():
    if agent and agent._voice:
        return jsonify(agent._voice.status())
    return jsonify({"running": False})

@app.route("/api/evolution/start", methods=["POST"])
def evo_start():
    if not agent: return jsonify({"ok": False})
    try:
        agent.start_evolution()
        return jsonify({"ok": True, "msg": "🔄 Co-evolution started"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

@app.route("/api/evolution/stats")
def evo_stats():
    if agent and agent._coevo:
        return jsonify(agent._coevo.stats())
    return jsonify({"running": False})

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
