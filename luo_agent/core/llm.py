import json, urllib.request, urllib.error
from typing import Generator

class OllamaClient:
    def __init__(self, base_url, model):
        self.base_url = base_url.rstrip("/"); self.model = model

    def chat(self, messages, temperature=0.7, max_tokens=2048):
        payload = {"model":self.model,"messages":messages,"stream":True,
                   "options":{"temperature":temperature,"num_predict":max_tokens}}
        req = urllib.request.Request(f"{self.base_url}/api/chat",
              json.dumps(payload).encode(), {"Content-Type":"application/json"})
        full = ""
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                for line in r:
                    try:
                        c = json.loads(line.decode().strip())
                        full += c.get("message",{}).get("content","")
                        if c.get("done"): break
                    except: continue
        except urllib.error.URLError as e: return f"[ERROR] Ollama unreachable: {e}"
        return full.strip()

    def stream_chat(self, messages, temperature=0.7, max_tokens=2048):
        payload = {"model":self.model,"messages":messages,"stream":True,
                   "options":{"temperature":temperature,"num_predict":max_tokens}}
        req = urllib.request.Request(f"{self.base_url}/api/chat",
              json.dumps(payload).encode(), {"Content-Type":"application/json"})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                for line in r:
                    try:
                        c = json.loads(line.decode().strip())
                        tok = c.get("message",{}).get("content","")
                        if tok: yield tok
                        if c.get("done"): break
                    except: continue
        except urllib.error.URLError as e: yield f"[ERROR] {e}"

    def is_available(self):
        try:
            urllib.request.urlopen(f"{self.base_url}/api/tags", timeout=5); return True
        except: return False

    def list_models(self):
        try:
            with urllib.request.urlopen(f"{self.base_url}/api/tags", timeout=5) as r:
                return [m["name"] for m in json.loads(r.read()).get("models",[])]
        except: return []
