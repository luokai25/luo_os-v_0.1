"""
LuoOS Memory Cells — Base Cell class
─────────────────────────────────────
Each memory cell is a daemon thread that:
  1. owns its own SQLite database (~/.luo_os/cells/<cell_id>/state.db)
  2. listens for signals from other cells via a queue
  3. ticks periodically to do background work (decay, consolidation, etc.)
  4. emits signals to other cells when interesting things happen

Cells form a memory ORGANISM:
  • EpisodicCell stores everything verbatim
  • SemanticCell promotes patterns into facts
  • WorkingCell holds active context
  • DreamCell consolidates during idle
  • ImportanceCell scores each new event 0..1
  • DecayCell weakens cold memories over time

They communicate by signal-passing on a CellNetwork bus, and form
Hebbian synapses — cells that fire together strengthen their connection.

Threaded synchronous version (no asyncio) so it integrates cleanly
with LuoOS's existing daemon architecture.

Lineage: KAI Agent v22 → which was inspired by luokai25/luo_os.
This is the reference implementation, brought home to LuoOS.
"""
import queue
import sqlite3
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path


# ────────────────────────────────────────────────────────────────────────
# Signal — one message between cells
# ────────────────────────────────────────────────────────────────────────
@dataclass
class Signal:
    """A message between cells."""
    kind:     str
    payload:  dict     = field(default_factory=dict)
    sender:   str      = ""
    target:   str      = "*"
    ts:       float    = field(default_factory=time.time)
    response: queue.Queue | None = None


# ────────────────────────────────────────────────────────────────────────
# CellNetwork — the bus connecting all memory cells
# ────────────────────────────────────────────────────────────────────────
class CellNetwork:
    """
    Routes signals between cells. Each cell registers itself.
    Tracks Hebbian synapse weights between co-firing cells.
    """

    def __init__(self):
        self._cells:    dict[str, "MemoryCell"] = {}
        self._synapses: dict[tuple[str, str], float] = {}
        self._lock      = threading.Lock()
        self._signal_count = 0

    def register(self, cell: "MemoryCell"):
        with self._lock:
            self._cells[cell.cell_id] = cell
            cell.network = self

    def send(self, signal: Signal):
        """Deliver signal to target cell(s)."""
        with self._lock:
            self._signal_count += 1
            if signal.target == "*":
                targets = list(self._cells.values())
            elif signal.target in self._cells:
                targets = [self._cells[signal.target]]
            else:
                targets = []
            # Strengthen synapses
            if signal.sender:
                for t in targets:
                    if t.cell_id != signal.sender:
                        key = (signal.sender, t.cell_id)
                        self._synapses[key] = min(1.0, self._synapses.get(key, 0.1) + 0.05)
        # Deliver outside lock
        for t in targets:
            if t.cell_id != signal.sender:
                t.inbox.put(signal)

    def get_cell(self, cell_id: str) -> "MemoryCell | None":
        return self._cells.get(cell_id)

    def synapse(self, sender: str, target: str) -> float:
        return self._synapses.get((sender, target), 0.0)

    def all_synapses(self) -> dict:
        return dict(self._synapses)

    def stats(self) -> dict:
        with self._lock:
            return {
                "cells":         list(self._cells.keys()),
                "cells_running": sum(1 for c in self._cells.values() if c.is_running),
                "signals_sent":  self._signal_count,
                "synapses":      len(self._synapses),
                "synapse_avg":   round(sum(self._synapses.values()) / max(1, len(self._synapses)), 2),
            }


# ────────────────────────────────────────────────────────────────────────
# MemoryCell — base class for all 6 specialized cells
# ────────────────────────────────────────────────────────────────────────
class MemoryCell:
    """Base class. Subclasses set cell_id and override on_signal/tick."""

    cell_id:       str   = "cell"
    tick_interval: float = 5.0     # seconds between tick() calls

    def __init__(self, data_dir: Path | None = None):
        self.cell_id    = self.__class__.cell_id
        self.network: CellNetwork | None = None
        self.inbox      = queue.Queue()
        self.is_running = False
        self._thread: threading.Thread | None = None
        self._stop      = threading.Event()
        # Per-cell SQLite database
        base       = data_dir or (Path.home() / ".luo_os" / "cells")
        self._dir  = base / self.cell_id
        self._dir.mkdir(parents=True, exist_ok=True)
        self._db_path = self._dir / "state.db"
        self._init_db()

    # ── persistence ──────────────────────────────────────────────
    def _init_db(self):
        """Subclasses override to create their tables."""
        pass

    def _conn(self) -> sqlite3.Connection:
        """Each thread gets its own connection (SQLite quirk)."""
        c = sqlite3.connect(str(self._db_path), timeout=5,
                             check_same_thread=False)
        c.row_factory = sqlite3.Row
        return c

    # ── lifecycle ────────────────────────────────────────────────
    def start(self):
        if self.is_running:
            return
        self.is_running = True
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._loop, daemon=True,
            name=f"Cell-{self.cell_id}",
        )
        self._thread.start()

    def stop(self):
        self.is_running = False
        self._stop.set()

    def _loop(self):
        last_tick = time.time()
        while not self._stop.is_set():
            # Drain inbox (blocking with short timeout)
            try:
                sig = self.inbox.get(timeout=0.5)
                try:
                    self.on_signal(sig)
                except Exception as e:
                    print(f"[Cell-{self.cell_id}] on_signal error: {e}")
                # Synchronous response if requested
                if sig.response is not None:
                    try:
                        sig.response.put_nowait(None)
                    except Exception:
                        pass
            except queue.Empty:
                pass
            # Periodic background work
            now = time.time()
            if now - last_tick >= self.tick_interval:
                try:
                    self.tick()
                except Exception as e:
                    print(f"[Cell-{self.cell_id}] tick error: {e}")
                last_tick = now

    # ── overridable ──────────────────────────────────────────────
    def on_signal(self, signal: Signal):
        """Override to handle incoming signals."""
        pass

    def tick(self):
        """Override for periodic background work."""
        pass

    def emit(self, kind: str, payload: dict | None = None, target: str = "*"):
        """Send a signal to other cells (or to all)."""
        if self.network is None:
            return
        self.network.send(Signal(
            kind=kind,
            payload=payload or {},
            sender=self.cell_id,
            target=target,
        ))

    def stats(self) -> dict:
        """Override to surface per-cell stats."""
        return {"cell_id": self.cell_id, "running": self.is_running}
