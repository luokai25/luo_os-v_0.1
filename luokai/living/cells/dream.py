"""
DreamCell — background consolidation during idle
─────────────────────────────────────────────────
Sleeps 90% of the time. When LUOKAI has been idle (no events for 5+ min),
or when manually triggered, it runs a "dream cycle":
  1. Tells SemanticCell to consolidate concepts → facts
  2. Tells DecayCell to apply decay to old episodes
  3. Logs what it dreamed about (for the Dreams app to display)

Listens for:
  • idle_start (from anyone) — note that we've gone idle
  • idle_end                — note that we're active again
  • force_dream             — trigger a cycle right now

The dream cycle is read by ~/.luo_os/dreams.json which is also what the
Dreams app from Phase 1 already shows.
"""
import json
import time
from pathlib import Path

from .base import MemoryCell, Signal


class DreamCell(MemoryCell):
    cell_id       = "dream"
    tick_interval = 60.0   # check idle status every minute

    IDLE_THRESHOLD_S       = 300   # 5 min of no activity
    MIN_INTERVAL_S         = 600   # at most 1 dream per 10 min
    DREAMS_LOG = Path.home() / ".luo_os" / "dreams.json"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._last_activity: float = time.time()
        self._last_dream:    float = 0.0
        self._dreaming:      bool  = False

    def _init_db(self):
        with self._conn() as c:
            c.execute("""
              CREATE TABLE IF NOT EXISTS cycles(
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                ts      REAL,
                kind    TEXT,
                summary TEXT
              )
            """)

    def on_signal(self, sig: Signal):
        if sig.kind in ("new_episode", "note_request", "user_activity"):
            self._last_activity = time.time()
        elif sig.kind == "idle_start":
            self._last_activity = sig.payload.get("ts", time.time()) - self.IDLE_THRESHOLD_S
        elif sig.kind == "idle_end":
            self._last_activity = time.time()
        elif sig.kind == "force_dream":
            self._dream("manual")

    def tick(self):
        now = time.time()
        # Have we been idle long enough?
        idle_for = now - self._last_activity
        if idle_for < self.IDLE_THRESHOLD_S:
            return
        # Recently dreamed?
        if now - self._last_dream < self.MIN_INTERVAL_S:
            return
        if self._dreaming:
            return
        self._dream("idle")

    def _dream(self, trigger: str):
        """Run a dream cycle."""
        self._dreaming   = True
        now = time.time()
        try:
            # Tell semantic cell to consolidate
            self.emit("dream_consolidate", {"trigger": trigger}, target="semantic")
            # Tell decay cell to apply
            self.emit("decay_pulse", {"trigger": trigger}, target="decay")
            summary = f"Consolidated semantic memory + applied decay (trigger={trigger})"
            with self._conn() as c:
                c.execute("INSERT INTO cycles(ts, kind, summary) VALUES(?,?,?)",
                          (now, trigger, summary))
            self._append_dream_log({
                "ts":      time.strftime("%Y-%m-%d %H:%M", time.localtime(now)),
                "content": summary,
                "msgs_processed": 0,
                "trigger": trigger,
            })
            self._last_dream = now
            self.emit("dream_complete", {"summary": summary}, target="*")
        finally:
            self._dreaming = False

    def _append_dream_log(self, dream: dict):
        """Append to ~/.luo_os/dreams.json so the Dreams app can show it."""
        try:
            existing = []
            if self.DREAMS_LOG.exists():
                existing = json.loads(self.DREAMS_LOG.read_text())
            existing.append(dream)
            existing = existing[-50:]
            self.DREAMS_LOG.parent.mkdir(parents=True, exist_ok=True)
            self.DREAMS_LOG.write_text(json.dumps(existing, indent=2))
        except Exception:
            pass

    def force_dream(self):
        self._dream("manual")

    def stats(self) -> dict:
        with self._conn() as c:
            count = c.execute("SELECT COUNT(*) FROM cycles").fetchone()[0]
            last = c.execute("SELECT ts FROM cycles ORDER BY ts DESC LIMIT 1").fetchone()
        return {
            "cell_id":   self.cell_id,
            "running":   self.is_running,
            "dreams":    count,
            "last_dream_ts": last["ts"] if last else None,
            "idle_for_s":    int(time.time() - self._last_activity),
        }
