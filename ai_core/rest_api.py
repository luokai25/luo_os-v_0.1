#!/usr/bin/env python3
"""
Luo OS REST API — Port 7071
HTTP-based API for humans and AI agents
Created by Luo Kai (luokai25)
"""

import json
import os
import subprocess
import urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

VERSION = "0.1"

class LuoRESTHandler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        print(f"[Luo REST] {datetime.now().strftime('%H:%M:%S')} {args[0]} {args[1]}")

    def send_json(self, data, code=200):
        body = json.dumps(data, indent=2).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(body))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.rstrip("/")

        if path == "" or path == "/":
            self.send_json({
                "name": "Luo OS REST API",
                "version": VERSION,
                "creator": "Luo Kai (luokai25)",
                "free": True,
                "endpoints": {
                    "GET /": "This help",
                    "GET /status": "OS status",
                    "GET /info": "System info",
                    "GET /files?path=/": "List files",
                    "GET /read?path=/file": "Read file",
                    "GET /log": "Activity log",
                    "POST /run": "Run command",
                    "POST /write": "Write file",
                    "POST /ai": "Ask Luo AI"
                }
            })

        elif path == "/status":
            self.send_json({
                "status": "running",
                "os": "Luo OS",
                "version": VERSION,
                "time": datetime.now().isoformat(),
                "free": True
            })

        elif path == "/info":
            info = os.uname()
            self.send_json({
                "os": "Luo OS",
                "version": VERSION,
                "kernel": info.release,
                "arch": info.machine,
                "hostname": info.nodename,
                "creator": "Luo Kai (luokai25)"
            })

        elif path.startswith("/files"):
            from urllib.parse import urlparse, parse_qs
            params = parse_qs(urlparse(self.path).query)
            dir_path = params.get("path", ["/"])[0]
            try:
                items = []
                for item in sorted(os.listdir(dir_path)):
                    full = os.path.join(dir_path, item)
                    items.append({
                        "name": item,
                        "type": "dir" if os.path.isdir(full) else "file",
                        "size": os.path.getsize(full) if os.path.isfile(full) else 0
                    })
                self.send_json({"path": dir_path, "items": items})
            except Exception as e:
                self.send_json({"error": str(e)}, 400)

        elif path.startswith("/read"):
            from urllib.parse import urlparse, parse_qs
            params = parse_qs(urlparse(self.path).query)
            file_path = params.get("path", [""])[0]
            try:
                with open(file_path, "r") as f:
                    self.send_json({"path": file_path, "content": f.read()})
            except Exception as e:
                self.send_json({"error": str(e)}, 400)

        elif path == "/log":
            log_file = "/tmp/luo_os_log.json"
            try:
                with open(log_file, "r") as f:
                    log = json.load(f)
            except:
                log = []
            self.send_json({"log": log})

        else:
            self.send_json({"error": "Not found"}, 404)

    def do_POST(self):
        path = self.path.rstrip("/")
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}

        if path == "/run":
            command = body.get("command", "")
            if not command:
                self.send_json({"error": "No command"}, 400)
                return
            try:
                result = subprocess.run(
                    command, shell=True,
                    capture_output=True, text=True, timeout=10
                )
                self.send_json({
                    "command": command,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "returncode": result.returncode
                })
            except Exception as e:
                self.send_json({"error": str(e)}, 500)

        elif path == "/write":
            file_path = body.get("path", "")
            content = body.get("content", "")
            try:
                with open(file_path, "w") as f:
                    f.write(content)
                self.send_json({"status": "ok", "path": file_path})
            except Exception as e:
                self.send_json({"error": str(e)}, 500)

        elif path == "/ai":
            prompt = body.get("prompt", "")
            try:
                payload = json.dumps({
                    "model": "tinyllama",
                    "prompt": f"You are Luo AI, the core of Luo OS. {prompt}",
                    "stream": False,
                    "options": {"num_predict": 100}
                }).encode()
                req = urllib.request.Request(
                    "http://127.0.0.1:11434/api/generate",
                    data=payload,
                    headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req, timeout=120) as r:
                    result = json.loads(r.read())
                    self.send_json({"response": result.get("response", "").strip()})
            except Exception as e:
                self.send_json({"error": str(e)}, 500)

        else:
            self.send_json({"error": "Not found"}, 404)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 7071), LuoRESTHandler)
    print(f"╔══════════════════════════════════════╗")
    print(f"║   Luo OS REST API v{VERSION}               ║")
    print(f"║   Running on http://0.0.0.0:7071     ║")
    print(f"║   Free for Humans & AI Agents        ║")
    print(f"╚══════════════════════════════════════╝")
    server.serve_forever()
