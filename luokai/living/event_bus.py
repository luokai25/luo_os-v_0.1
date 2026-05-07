"""
LuoOS Event Bus
─────────────────
A system-wide pub/sub channel. Every app publishes activity here.
LUOKAI's daemon subscribes. The UI subscribes. Everything talks.

This is the foundation that makes LuoOS feel like ONE living system
instead of 14 separate apps.

Usage:
    from luokai.living import bus

    # Publish an event
    bus.publish("file.opened", {"path": "~/budget.xlsx", "app": "files"})

    # Subscribe (called for every event matching pattern)
    @bus.subscribe("file.*")
    def on_file_event(event):
        print(event.type, event.data)

    # Get recent history
    recent = bus.history(since_seconds=60)
"""
import json
import time
import threading
import fnmatch
from collections import deque
from pathlib import Path
from typing import Callable, Any


# ──── Event ──────────────────────────────────────────────────────
class Event:
    """A single event flowing through the bus."""
    __slots__ = ("type", "data", "ts", "source")

    def __init__(self, event_type: str, data: dict | None = None, source: str = "unknown"):
        self.type   = event_type
        self.data   = data or {}
        self.ts     = time.time()
        self.source = source

    def to_dict(self) -> dict:
        return {
            "type":   self.type,
            "data":   self.data,
            "ts":     self.ts,
            "source": self.source,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Event":
        e = cls(d.get("type", "unknown"), d.get("data", {}), d.get("source", "unknown"))
        e.ts = d.get("ts", time.time())
        return e

    def __repr__(self):
        return f"Event({self.type}, {self.data})"


# ──── Bus ────────────────────────────────────────────────────────
class EventBus:
    """In-process pub/sub event channel with rolling history."""

    def __init__(self, history_size: int = 5000, log_path: Path | None = None):
        self._subscribers: list[tuple[str, Callable[[Event], None]]] = []
        self._history:     deque[Event] = deque(maxlen=history_size)
        self._lock         = threading.Lock()
        self._log_path     = log_path
        self._log_path and self._log_path.parent.mkdir(parents=True, exist_ok=True)

    # ── publish ────────────────────────────────────────────────
    def publish(self, event_type: str, data: dict | None = None, source: str = "system") -> Event:
        """Publish an event. Notifies all matching subscribers."""
        event = Event(event_type, data, source)
        with self._lock:
            self._history.append(event)
            subs = list(self._subscribers)
        # Persist to log file (best-effort)
        if self._log_path:
            try:
                with self._log_path.open("a") as f:
                    f.write(json.dumps(event.to_dict()) + "\n")
            except Exception:
                pass
        # Notify outside the lock to prevent deadlocks
        for pattern, callback in subs:
            if fnmatch.fnmatch(event_type, pattern):
                try:
                    callback(event)
                except Exception as e:
                    print(f"[EventBus] Subscriber error on {event_type}: {e}")
        return event

    # ── subscribe ──────────────────────────────────────────────
    def subscribe(self, pattern: str = "*"):
        """Decorator/function to subscribe to events.
        Pattern uses fnmatch (wildcards: *, ?). Examples:
            "file.*"       → all file events
            "file.opened"  → only file.opened
            "*"            → everything
        """
        def decorator(callback: Callable[[Event], None]):
            with self._lock:
                self._subscribers.append((pattern, callback))
            return callback
        return decorator

    def unsubscribe(self, callback: Callable):
        with self._lock:
            self._subscribers = [(p, cb) for (p, cb) in self._subscribers if cb is not callback]

    # ── history ────────────────────────────────────────────────
    def history(self, since_seconds: float | None = None,
                event_pattern: str | None = None,
                limit: int = 100) -> list[Event]:
        """Return recent events, optionally filtered."""
        cutoff = time.time() - since_seconds if since_seconds else 0
        with self._lock:
            events = list(self._history)
        if since_seconds:
            events = [e for e in events if e.ts >= cutoff]
        if event_pattern:
            events = [e for e in events if fnmatch.fnmatch(e.type, event_pattern)]
        return events[-limit:]

    def clear(self):
        with self._lock:
            self._history.clear()

    def stats(self) -> dict:
        """Return bus statistics for monitoring."""
        with self._lock:
            events = list(self._history)
            sub_count = len(self._subscribers)
        type_counts: dict[str, int] = {}
        for e in events:
            type_counts[e.type] = type_counts.get(e.type, 0) + 1
        return {
            "total_events":     len(events),
            "subscriber_count": sub_count,
            "event_types":      type_counts,
            "oldest":           events[0].ts if events else None,
            "newest":           events[-1].ts if events else None,
        }


# ──── Singleton ──────────────────────────────────────────────────
_LOG_PATH = Path.home() / ".luo_os" / "event_log.jsonl"
bus = EventBus(history_size=5000, log_path=_LOG_PATH)


# ──── Convenience publishers ─────────────────────────────────────
def publish(event_type: str, data: dict | None = None, source: str = "system") -> Event:
    """Module-level shortcut for bus.publish."""
    return bus.publish(event_type, data, source)


def subscribe(pattern: str = "*"):
    """Module-level shortcut for bus.subscribe."""
    return bus.subscribe(pattern)


def history(**kwargs) -> list[Event]:
    return bus.history(**kwargs)


# ──── Standard event taxonomy ────────────────────────────────────
# Use these conventions when publishing for consistency:
#
# user.input.*         — user typed/clicked/spoke
#   user.input.text    — text submitted to LUOKAI
#   user.input.click   — UI button clicked
#   user.input.voice   — voice command transcribed
#
# app.*                — app lifecycle
#   app.opened         — user opened an app
#   app.closed         — app window closed
#   app.focused        — app window focused
#
# file.*               — file operations
#   file.opened        — file opened in editor/viewer
#   file.saved         — file written to disk
#   file.deleted
#   file.renamed
#
# chat.*               — LUOKAI conversation
#   chat.user_msg      — user sent a chat message
#   chat.assistant_msg — LUOKAI responded
#   chat.tool_call     — agent invoked a tool
#
# perception.*         — face/gaze/biofeedback events
#   perception.gaze
#   perception.mood_change
#   perception.attention_change
#
# system.*             — system-level events
#   system.startup
#   system.shutdown
#   system.idle_start
#   system.idle_end
#
# luokai.*             — LUOKAI's own thoughts
#   luokai.predicted
#   luokai.verified
#   luokai.learned
#   luokai.suggested
