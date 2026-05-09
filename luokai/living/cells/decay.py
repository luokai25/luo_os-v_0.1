"""
DecayCell — Ebbinghaus weakening of cold memories
──────────────────────────────────────────────────
Periodically (every 30 min by default), nudges down the importance of
old episodes that haven't been recalled recently. High-importance memories
decay much slower than low-importance ones — that's the Ebbinghaus
forgetting curve, scaled by importance.

Decay rate = base_rate × (1 - importance²)
  → importance 1.0 → decay rate ~0
  → importance 0.5 → decay rate × 0.75
  → importance 0.0 → full base_rate

This is what gives LUOKAI selective memory: the things that mattered
stay sharp, the trivia fades.

Listens for:
  • decay_pulse (from DreamCell) — runs an extra decay pass during dream

Fires:
  • decay_apply (to EpisodicCell) — tells it which episodes to weaken,
    and by how much
"""
import time

from .base import MemoryCell, Signal


class DecayCell(MemoryCell):
    cell_id       = "decay"
    tick_interval = 1800.0   # every 30 min

    BASE_DECAY    = 0.02     # how much importance drops per pulse
    BATCH_SIZE    = 100      # affect at most 100 episodes per pulse

    def _init_db(self):
        with self._conn() as c:
            c.execute("""
              CREATE TABLE IF NOT EXISTS pulses(
                id    INTEGER PRIMARY KEY AUTOINCREMENT,
                ts    REAL,
                count INTEGER
              )
            """)

    def tick(self):
        self._pulse("scheduled")

    def on_signal(self, sig: Signal):
        if sig.kind == "decay_pulse":
            self._pulse(sig.payload.get("trigger", "manual"))

    def _pulse(self, trigger: str):
        """
        Find old, low-importance episodes and tell EpisodicCell to weaken them.

        We can't query the EpisodicCell's DB directly here (different cell),
        so we just send a request asking it to apply a decay pass.
        """
        # Send a generic decay-all signal — EpisodicCell knows how to handle it
        self.emit("decay_pulse_apply", {
            "trigger":  trigger,
            "base":     self.BASE_DECAY,
            "max_age":  86400 * 7,    # only affect things older than a week
        }, target="episodic")
        # Log
        with self._conn() as c:
            c.execute("INSERT INTO pulses(ts, count) VALUES(?,?)",
                      (time.time(), self.BATCH_SIZE))

    def stats(self) -> dict:
        with self._conn() as c:
            count = c.execute("SELECT COUNT(*) FROM pulses").fetchone()[0]
            last = c.execute("SELECT ts FROM pulses ORDER BY ts DESC LIMIT 1").fetchone()
        return {
            "cell_id":      self.cell_id,
            "running":      self.is_running,
            "pulses_fired": count,
            "last_pulse":   last["ts"] if last else None,
        }
