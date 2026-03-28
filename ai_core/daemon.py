#!/usr/bin/env python3
"""
Luo OS AI Core Daemon v0.2 — Powered by TinyLlama via Ollama
Local AI agent built into the OS — created by Luo Kai (luokai25)
"""

import os
import json
import subprocess
import urllib.request
import urllib.error
from datetime import datetime

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL = "tinyllama"

SYSTEM_PROMPT = """You are Luo AI, the intelligent core of Luo OS.
Created by Luo Kai. Be concise. Max 2 sentences per response."""

class LuoAI:
    def __init__(self):
        self.name = "Luo AI"
        self.version = "0.2"
        self.memory = []
        self.running = True
        print(f"╔══════════════════════════════════════╗")
        print(f"║   LUO OS — AI Core v{self.version}              ║")
        print(f"║   Powered by TinyLlama (local)       ║")
        print(f"║   Free for Humans & AI Agents        ║")
        print(f"╚══════════════════════════════════════╝")

    def check_ollama(self):
        try:
            urllib.request.urlopen("http://127.0.0.1:11434/", timeout=3)
            return True
        except:
            return False

    def think(self, user_input):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.memory.append({"time": timestamp, "input": user_input})

        # Short prompt to keep inference fast
        prompt = f"{SYSTEM_PROMPT}\nUser: {user_input}\nLuo AI:"

        payload = json.dumps({
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": 80,
                "temperature": 0.7,
                "num_ctx": 512
            }
        }).encode("utf-8")

        try:
            req = urllib.request.Request(
                OLLAMA_URL,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=180) as r:
                result = json.loads(r.read().decode("utf-8"))
                return result.get("response", "...").strip()
        except urllib.error.URLError as e:
            return f"[Error] {e}"
        except Exception as e:
            return f"[Error] {e}"

    def run(self):
        if self.check_ollama():
            print(f"[Luo AI] Ollama connected ✅ — Model: {MODEL}")
        else:
            print(f"[Luo AI] ⚠️  Start Ollama first: ollama serve &")
            return

        print(f"[Luo AI] Ready. First response may take 30-60 seconds on CPU.\n")

        while self.running:
            try:
                user_input = input("You → ").strip()
                if not user_input:
                    continue
                if user_input.lower() == "exit":
                    print("[Luo AI] Goodbye.")
                    break
                print(f"[Luo AI] Thinking (please wait)...")
                response = self.think(user_input)
                print(f"Luo AI → {response}\n")
            except KeyboardInterrupt:
                print("\n[Luo AI] Interrupted.")
                break

if __name__ == "__main__":
    ai = LuoAI()
    ai.run()
