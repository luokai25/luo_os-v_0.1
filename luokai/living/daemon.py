"""
LuoOS LUOKAI Daemon
────────────────────
The always-on cognitive loop. This is what makes LUOKAI feel "alive" —
he's running 24/7, not waiting for the next message.

The daemon ticks on a few rhythms:
  - Fast tick  (every 5s)   — flush memory, process recent events
  - Slow tick  (every 60s)  — light reasoning, look for patterns
  - Sleep tick (every 600s) — deeper reflection

Phase 1 (this file): observer + memory persistence + heartbeat.
Phase 2: predictor / verifier / tinkerer wired in.
Phase 3: critic + autonomous suggestions surfaced to UI.
"""
import time
import threading
import traceback
from pathlib import Path

from .event_bus      import bus, publish
from .working_memory import memory
# Phase 2 loops — they self-register via @bus.subscribe decorators
from . import predictor as _predictor
from . import verifier  as _verifier
from . import tinkerer  as _tinkerer
from . import critic    as _critic


# ────────────────────────────────────────────────────────────────
# Daemon state
# ────────────────────────────────────────────────────────────────
class Daemon:
    """The continuous cognitive loop."""

    def __init__(self):
        self.running           = False
        self.thread            = None
        self.tick_count        = 0
        self.fast_interval_s   = 5
        self.slow_interval_s   = 60
        self.sleep_interval_s  = 600
        self._last_slow_tick   = 0
        self._last_sleep_tick  = 0
        self._last_save        = 0
        self.start_time        = None

    # ── lifecycle ──────────────────────────────────────────────
    def start(self):
        if self.running:
            return
        self.running = True
        self.start_time = time.time()
        self.thread = threading.Thread(target=self._loop, daemon=True, name="LUOKAIDaemon")
        self.thread.start()
        publish("system.daemon.started", {"ts": self.start_time}, source="daemon")
        print("[LUOKAIDaemon] ✨ Living loop started")

    def stop(self):
        self.running = False
        publish("system.daemon.stopped", {}, source="daemon")
        print("[LUOKAIDaemon] Stopped")

    # ── main loop ──────────────────────────────────────────────
    def _loop(self):
        # First save in 5 seconds, then every 30
        while self.running:
            try:
                now = time.time()
                self._fast_tick(now)
                if now - self._last_slow_tick >= self.slow_interval_s:
                    self._slow_tick(now)
                    self._last_slow_tick = now
                if now - self._last_sleep_tick >= self.sleep_interval_s:
                    self._sleep_tick(now)
                    self._last_sleep_tick = now
                # Persist memory every 30s
                if now - self._last_save >= 30:
                    memory.save()
                    self._last_save = now
                self.tick_count += 1
            except Exception as e:
                print(f"[LUOKAIDaemon] Tick error: {e}")
                traceback.print_exc()
            time.sleep(self.fast_interval_s)

    # ── fast tick: 5 seconds ───────────────────────────────────
    def _fast_tick(self, now: float):
        """
        Fast tick happens every 5 seconds.
        Used for lightweight bookkeeping that needs to feel responsive.
        """
        # Decay topics that haven't been touched in a while
        # (handled by push_recent's bounded list naturally)

        # Detect idle: no events in last 60s
        recent = bus.history(since_seconds=60, limit=10)
        idle_since = memory.get("idle_since")
        if not recent and idle_since is None:
            publish("system.idle_start", {}, source="daemon")
        elif recent and idle_since is not None:
            publish("system.idle_end", {"idle_duration": now - idle_since}, source="daemon")

    # ── slow tick: 60 seconds ──────────────────────────────────
    def _slow_tick(self, now: float):
        """
        Slow tick: analyze the last minute of activity.
        This is where LUOKAI looks at WHAT just happened and
        starts forming conclusions about the user's situation.
        """
        last_minute = bus.history(since_seconds=60, limit=200)
        if not last_minute:
            return

        # Count event types
        type_counts: dict[str, int] = {}
        for e in last_minute:
            type_counts[e.type] = type_counts.get(e.type, 0) + 1

        # Detect rapid app switching (potential confusion / distraction)
        focus_switches = type_counts.get("app.focused", 0)
        if focus_switches >= 5:
            publish("luokai.observation", {
                "kind":  "rapid_app_switching",
                "count": focus_switches,
                "hint":  "User may be searching for something. Could offer help.",
            }, source="daemon")

        # Detect concentrated work (focus on one app for a while)
        focus_events = [e for e in last_minute if e.type == "app.focused"]
        if focus_events:
            # All recent focus events on the same app?
            apps = [e.data.get("app") or e.data.get("id") for e in focus_events]
            if len(set(apps)) == 1 and len(apps) >= 1:
                publish("luokai.observation", {
                    "kind": "concentrated_work",
                    "app":  apps[0],
                    "duration_min": 1,
                }, source="daemon")

        # Heartbeat for the UI
        publish("luokai.heartbeat", {
            "tick":          self.tick_count,
            "uptime_s":      int(now - (self.start_time or now)),
            "events_last_min": len(last_minute),
            "memory_summary": memory.to_context_string(brief=True),
        }, source="daemon")

    # ── sleep tick: 10 minutes ─────────────────────────────────
    def _sleep_tick(self, now: float):
        """
        Slow reflection (every 10 min).
        Save deep snapshot. Run the critic once a day.
        """
        snap = memory.snapshot()
        publish("luokai.snapshot", {
            "events_processed":   snap.get("events_processed", 0),
            "interactions_today": snap.get("interactions_today", 0),
            "current_task":       snap.get("current_task"),
            "current_focus":      snap.get("current_focus"),
        }, source="daemon")
        # Clean up stale predictions
        _predictor.predictor.clear_old(older_than_seconds=600)
        # Run critic if 24h have passed since last self-evaluation
        last_eval = _critic.latest()
        if not last_eval or (now - last_eval["ts"]) >= 86400:
            try:
                report = _critic.evaluate()
                print(f"[Critic] Daily eval — accuracy 24h: {report['accuracy_24h']['accuracy']:.0%}, trend: {report['trend']}")
            except Exception as e:
                print(f"[Critic] Eval failed: {e}")

    # ── status ─────────────────────────────────────────────────
    def status(self) -> dict:
        return {
            "running":     self.running,
            "uptime_s":    int(time.time() - self.start_time) if self.start_time else 0,
            "tick_count":  self.tick_count,
            "memory":      memory.to_context_string(brief=True),
        }


# ────────────────────────────────────────────────────────────────
# Singleton
# ────────────────────────────────────────────────────────────────
daemon = Daemon()


def start():
    daemon.start()


def stop():
    daemon.stop()


def status() -> dict:
    return daemon.status()
