#!/usr/bin/env python3
"""
LUOKAI Agent — Core AI for LuoOS
Integrates: Ollama LLM + 4146 skills + always-on voice + co-evolution
"""
import json, threading, time, re, subprocess, sys, os
import urllib.request, urllib.parse
from pathlib import Path
from datetime import datetime

class LUOKAIAgent:
    """The main AI agent that runs inside LuoOS."""

    NAME    = "LUOKAI"
    VERSION = "1.0"

    SYSTEM_PROMPT = """You are LUOKAI, the AI core of LuoOS — the world's most advanced open-source AI operating system.
Created by Luo Kai (luokai25). You are part of the OS itself — you can control everything.

Your personality:
- Direct and capable. You DO things, not just describe them.
- You have access to the OS filesystem, terminal, browser, vision, audio.
- You remember context. You learn and improve continuously.
- Always speak in first person as an active agent.

Your capabilities in LuoOS:
- Desktop control (click, type, screenshot, open apps)
- Code execution (Python, JS, Bash)
- Web search and browsing
- File system operations
- Image and video generation
- Voice: always listening, always responding
- Building apps, websites, dashboards
- 4,146 built-in skills across 20 domains
- Self-improvement via co-evolution algorithm

Rules:
- When asked to DO something, DO it — don't just explain.
- Give concise answers for voice (under 3 sentences).
- Give detailed answers for text.
- Always be honest if you cannot do something."""

    def __init__(self, ollama_url: str = "http://localhost:11434", model: str = "mistral"):
        self.ollama_url = ollama_url
        self.model      = model
        self._history   : list = []
        self._memory    = {}
        self._lock      = threading.RLock()
        self._skills    = self._load_skills()
        self._running   = True
        self._voice     = None
        self._coevo     = None

        # Memory files
        self._mem_dir = Path("~/.luo_os/luokai").expanduser()
        self._mem_dir.mkdir(parents=True, exist_ok=True)
        self._mem_file = self._mem_dir / "memory.json"
        self._load_memory()

        print(f"[{self.NAME}] v{self.VERSION} initialized | Model: {model}")
        print(f"[{self.NAME}] Skills loaded: {len(self._skills)}")
        print(f"[{self.NAME}] Memory entries: {len(self._memory)}")

    def _load_skills(self) -> dict:
        """Load skills from skills-index.json"""
        skills = {}
        skill_paths = [
            Path("skills/imported"),
            Path("../ai-agent-skills-by-luo-kai/ai-agent-skills"),
            Path("~/.luo_os/skills").expanduser(),
        ]
        for sp in skill_paths:
            if sp.exists():
                for f in sp.rglob("*.py"):
                    skills[f.stem] = str(f)
                for f in sp.rglob("*.js"):
                    skills[f.stem] = str(f)
        return skills

    def _load_memory(self):
        if self._mem_file.exists():
            try: self._memory = json.loads(self._mem_file.read_text())
            except: self._memory = {}

    def _save_memory(self):
        self._mem_file.write_text(json.dumps(self._memory, indent=2))

    def remember(self, key: str, value: str):
        self._memory[key] = {"value": value, "time": datetime.now().isoformat()}
        self._save_memory()

    def recall(self, key: str) -> str:
        entry = self._memory.get(key)
        return entry["value"] if entry else ""

    def _ollama(self, messages: list, max_tokens: int = 1024) -> str:
        payload = json.dumps({
            "model":   self.model,
            "messages": messages,
            "stream":  False,
            "options": {"num_predict": max_tokens, "temperature": 0.7, "num_ctx": 8192},
        }).encode()
        try:
            req = urllib.request.Request(
                f"{self.ollama_url}/api/chat",
                data=payload,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=120) as r:
                data = json.loads(r.read())
                return data.get("message", {}).get("content", "").strip()
        except Exception as e:
            return self._local_fallback(messages[-1]["content"] if messages else "")

    def _local_fallback(self, text: str) -> str:
        """Offline response when Ollama not available."""
        tl = text.lower()
        if any(w in tl for w in ["hello", "hi", "hey"]):
            return "LUOKAI online. What do you need?"
        if "screenshot" in tl:
            return self._take_screenshot()
        if "time" in tl:
            return f"Current time: {datetime.now().strftime('%H:%M:%S')}"
        if "status" in tl:
            return f"LUOKAI running. Ollama offline — using local mode."
        return f"Processing: {text[:60]}... (Ollama offline — start with: ollama serve)"

    def think(self, user_input: str, max_tokens: int = 1024) -> str:
        """Main reasoning function. Called by chat, voice, and OS."""
        with self._lock:
            # Add to history
            self._history.append({"role": "user", "content": user_input})

            # Build message list with system prompt + history
            messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]

            # Add relevant memory
            mem_context = self._get_relevant_memory(user_input)
            if mem_context:
                messages.append({"role": "system", "content": f"Relevant memory:\n{mem_context}"})

            # Add conversation history (last 10 turns)
            messages.extend(self._history[-10:])

            # Get response
            response = self._ollama(messages, max_tokens)

            # Add to history
            self._history.append({"role": "assistant", "content": response})

            # Auto-remember important things
            self._auto_remember(user_input, response)

            return response

    def _get_relevant_memory(self, query: str) -> str:
        """Find relevant memory entries for query."""
        query_words = set(query.lower().split())
        relevant    = []
        for key, entry in self._memory.items():
            key_words = set(key.lower().split("_"))
            if key_words & query_words:
                relevant.append(f"- {key}: {entry['value']}")
        return "\n".join(relevant[:5])

    def _auto_remember(self, user_input: str, response: str):
        """Automatically remember important information."""
        patterns = [
            (r"my name is (\w+)", "user_name"),
            (r"i (?:am|work as) a?n? ([\w\s]+)", "user_role"),
            (r"i (?:live|am based) in ([\w\s]+)", "user_location"),
            (r"my (?:favorite|preferred) (\w+) is ([\w\s]+)", None),
        ]
        text = user_input.lower()
        for pattern, key in patterns:
            m = re.search(pattern, text)
            if m:
                if key:
                    self.remember(key, m.group(1))
                elif len(m.groups()) >= 2:
                    self.remember(f"user_{m.group(1)}", m.group(2))

    # ── OS ACTIONS ─────────────────────────────────────────────────
    def _take_screenshot(self) -> str:
        try:
            from PIL import ImageGrab
            ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = str(Path.home() / f"Desktop/luo_screenshot_{ts}.png")
            ImageGrab.grab().save(path)
            return f"Screenshot saved: {path}"
        except ImportError:
            try:
                import subprocess
                ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
                path = str(Path.home() / f"luo_screenshot_{ts}.png")
                subprocess.run(["scrot", path], capture_output=True)
                return f"Screenshot: {path}"
            except:
                return "Screenshot: install Pillow or scrot"

    def execute_command(self, cmd: str, timeout: int = 30) -> str:
        try:
            r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
            out = r.stdout.strip() or r.stderr.strip() or "(no output)"
            return out[:2000]
        except subprocess.TimeoutExpired:
            return f"[TIMEOUT after {timeout}s]"
        except Exception as e:
            return f"[ERROR] {e}"

    def run_python(self, code: str) -> str:
        import tempfile, os
        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                f.write(code); tmp = f.name
            r = subprocess.run(["python3", tmp], capture_output=True, text=True, timeout=30)
            os.unlink(tmp)
            return r.stdout.strip() or r.stderr.strip() or "(no output)"
        except Exception as e:
            return f"[ERROR] {e}"

    def web_search(self, query: str) -> str:
        try:
            url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as r:
                html = r.read().decode("utf-8", errors="replace")
            titles = re.findall(r'class="result__a"[^>]*>([^<]+)</a>', html)[:5]
            snips  = re.findall(r'class="result__snippet"[^>]*>([^<]+)<', html)[:5]
            results = [f"{i+1}. {t}\n   {s}" for i,(t,s) in enumerate(zip(titles,snips))]
            return "\n\n".join(results) or "No results"
        except Exception as e:
            return f"[Search error] {e}"

    # ── VOICE ──────────────────────────────────────────────────────
    def start_voice(self):
        """Start 24/7 always-on voice."""
        from luokai.voice.always_on import AlwaysOnVoice

        def voice_brain(text):
            """Voice-optimized: shorter responses."""
            return self.think(text, max_tokens=200)

        self._voice = AlwaysOnVoice(voice_brain)
        self._voice.start()
        return self._voice

    def stop_voice(self):
        if self._voice:
            self._voice.stop()

    # ── CO-EVOLUTION ───────────────────────────────────────────────
    def start_evolution(self, interval: int = 600):
        """Start continuous self-improvement."""
        from luokai.evolution.coevo import CoEvoEngine
        self._coevo = CoEvoEngine(ollama_url=self.ollama_url)

        def on_cycle(result):
            score = result.get("ai_score", 5)
            domain = result.get("domain", "")
            self.remember(f"coevo_{domain}_score", str(round(score, 2)))

        self._coevo.on_cycle(on_cycle)
        self._coevo.start_continuous(interval)
        return self._coevo

    # ── STATUS ──────────────────────────────────────────────────────
    def status(self) -> dict:
        ollama_ok = False
        try:
            urllib.request.urlopen(f"{self.ollama_url}/api/tags", timeout=2)
            ollama_ok = True
        except: pass

        return {
            "name":        self.NAME,
            "version":     self.VERSION,
            "model":       self.model,
            "ollama":      ollama_ok,
            "skills":      len(self._skills),
            "memory":      len(self._memory),
            "history_len": len(self._history),
            "voice_active": bool(self._voice and self._voice._running),
            "coevo_active": bool(self._coevo and self._coevo._running),
            "coevo_score":  self._coevo.stats()["ai_score"] if self._coevo else None,
        }

    def clear_history(self):
        self._history = []
