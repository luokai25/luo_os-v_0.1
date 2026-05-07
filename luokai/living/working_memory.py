"""
LuoOS Working Memory
─────────────────────
This is NOT chat history. This is LUOKAI's live model of what's
happening RIGHT NOW. Updated on every event.

Working memory holds:
  - Current task and goal (inferred or explicit)
  - Open files and apps
  - Recent people/entities mentioned
  - Today's calendar
  - Unfinished threads
  - Patterns observed so far

This is what gets injected as context into every chat request,
so LUOKAI ALWAYS knows what you're doing.

Persisted to ~/.luo_os/working_memory.json — survives restarts.
"""
import json
import time
import threading
from collections import deque
from pathlib import Path
from typing import Any


class WorkingMemory:
    """LUOKAI's live structured awareness of the user's state."""

    DEFAULT_STATE = {
        "version":          "1.0",
        "session_started":  None,
        "last_updated":     None,

        # ── what the user is doing ──
        "current_focus":    None,        # app id of focused window
        "current_task":     None,        # inferred task description
        "current_goal":     None,        # higher-level goal

        # ── workspace state ──
        "open_apps":        [],          # list of app ids currently open
        "open_files":       [],          # list of file paths recently touched
        "recent_urls":      [],          # last 20 URLs visited

        # ── people & entities ──
        "recent_people":    [],          # last 10 people mentioned
        "recent_topics":    [],          # last 20 topic keywords

        # ── time-bound context ──
        "todays_calendar":  [],          # events today
        "unfinished":       [],          # tasks user started but didn't finish

        # ── inferred patterns ──
        "active_patterns":  [],          # patterns LUOKAI is currently using
        "user_preferences": {},          # accumulated preferences

        # ── biofeedback (if perception is on) ──
        "user_state": {
            "mood":       None,
            "attention":  None,
            "stress":     None,
            "bpm":        None,
        },

        # ── stats ──
        "events_processed": 0,
        "interactions_today": 0,
    }

    def __init__(self, persist_path: Path | None = None):
        self._state = dict(self.DEFAULT_STATE)
        self._lock  = threading.Lock()
        self._path  = persist_path or (Path.home() / ".luo_os" / "working_memory.json")
        self._load()
        if not self._state.get("session_started"):
            self._state["session_started"] = time.time()

    # ── persistence ────────────────────────────────────────────
    def _load(self):
        try:
            if self._path.exists():
                data = json.loads(self._path.read_text())
                # Merge with defaults to handle new fields
                merged = dict(self.DEFAULT_STATE)
                merged.update(data)
                self._state = merged
        except Exception as e:
            print(f"[WorkingMemory] Load error: {e}")

    def save(self):
        """Persist state to disk. Called periodically by daemon."""
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._state["last_updated"] = time.time()
            self._path.write_text(json.dumps(self._state, indent=2))
        except Exception as e:
            print(f"[WorkingMemory] Save error: {e}")

    # ── access ─────────────────────────────────────────────────
    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            return self._state.get(key, default)

    def snapshot(self) -> dict:
        """Return a thread-safe copy of the entire state."""
        with self._lock:
            return json.loads(json.dumps(self._state))

    def set(self, key: str, value: Any):
        with self._lock:
            self._state[key] = value

    def update(self, **kwargs):
        with self._lock:
            self._state.update(kwargs)

    # ── list operations (with bounded size) ────────────────────
    def push_recent(self, key: str, value: Any, max_size: int = 20):
        """Push an item to a recent-list, deduplicate, cap size."""
        with self._lock:
            lst = self._state.setdefault(key, [])
            # Remove duplicates (case-insensitive for strings)
            if isinstance(value, str):
                lst = [v for v in lst if (isinstance(v, str) and v.lower() != value.lower()) or not isinstance(v, str)]
            else:
                lst = [v for v in lst if v != value]
            lst.insert(0, value)
            self._state[key] = lst[:max_size]

    def add_to(self, key: str, value: Any):
        """Append unique to a list."""
        with self._lock:
            lst = self._state.setdefault(key, [])
            if value not in lst:
                lst.append(value)

    def remove_from(self, key: str, value: Any):
        with self._lock:
            lst = self._state.get(key, [])
            self._state[key] = [v for v in lst if v != value]

    def increment(self, key: str, by: int = 1):
        with self._lock:
            self._state[key] = self._state.get(key, 0) + by

    # ── context generation ─────────────────────────────────────
    def to_context_string(self, brief: bool = False) -> str:
        """
        Render the working memory as a context string for LLM prompts.
        This is the PRIMARY way LUOKAI gets situational awareness.
        """
        s = self.snapshot()
        lines = []
        if s.get("current_focus"):
            lines.append(f"User is currently in: {s['current_focus']}")
        if s.get("current_task"):
            lines.append(f"Current task: {s['current_task']}")
        if s.get("open_apps") and not brief:
            lines.append(f"Open apps: {', '.join(s['open_apps'][:6])}")
        if s.get("open_files") and not brief:
            recent_files = [f for f in s["open_files"][:3]]
            if recent_files:
                lines.append(f"Recent files: {', '.join(recent_files)}")
        if s.get("recent_people"):
            lines.append(f"Recent people: {', '.join(s['recent_people'][:5])}")
        if s.get("recent_topics"):
            lines.append(f"Recent topics: {', '.join(s['recent_topics'][:5])}")
        ust = s.get("user_state", {})
        if ust.get("mood") or ust.get("bpm"):
            ustparts = []
            if ust.get("mood"):      ustparts.append(f"mood={ust['mood']}")
            if ust.get("attention"): ustparts.append(f"attention={ust['attention']:.0%}")
            if ust.get("bpm"):       ustparts.append(f"hr={ust['bpm']}bpm")
            if ust.get("stress"):    ustparts.append(f"stress={ust['stress']:.0%}")
            if ustparts:
                lines.append(f"User state: {', '.join(ustparts)}")
        if not lines:
            return ""
        return "[Workspace Context]\n" + "\n".join(lines) + "\n"

    # ── reset ──────────────────────────────────────────────────
    def reset_session(self):
        """Start a fresh session — keeps preferences/patterns, clears transients."""
        with self._lock:
            preferences      = self._state.get("user_preferences", {})
            active_patterns  = self._state.get("active_patterns", [])
            self._state = dict(self.DEFAULT_STATE)
            self._state["session_started"]  = time.time()
            self._state["user_preferences"] = preferences
            self._state["active_patterns"]  = active_patterns


# ──── Singleton ──────────────────────────────────────────────────
memory = WorkingMemory()


# ──── Convenience accessors ──────────────────────────────────────
def get(key: str, default: Any = None) -> Any:
    return memory.get(key, default)


def set_(key: str, value: Any):
    memory.set(key, value)


def update(**kwargs):
    memory.update(**kwargs)


def snapshot() -> dict:
    return memory.snapshot()


def context_string(brief: bool = False) -> str:
    return memory.to_context_string(brief=brief)


def save():
    memory.save()
