"""
LuoOS Cell Memory System — Orchestrator
────────────────────────────────────────
Brings the 6 memory cells together as a working organism.

Public API (the rest of LuoOS only needs to know these):

    from luokai.living.cells import system

    system.start()                                # spin up all cells
    eid = system.store("user said hi", "chat")    # → EpisodicCell + ImportanceCell + SemanticCell
    items = system.recall("hi", limit=5)          # ← EpisodicCell
    system.note("user is debugging Flask")        # → WorkingCell
    snapshot = system.working_snapshot()          # ← WorkingCell
    facts = system.facts()                        # ← SemanticCell
    system.force_dream()                          # → DreamCell
    stats = system.stats()                        # whole organism
    system.stop()
"""
import queue
from pathlib import Path

from .base       import CellNetwork
from .episodic   import EpisodicCell
from .semantic   import SemanticCell
from .working    import WorkingCell
from .dream      import DreamCell
from .importance import ImportanceCell
from .decay      import DecayCell


class CellSystem:
    """The 6-cell memory organism."""

    def __init__(self, data_dir: Path | None = None):
        self.data_dir = data_dir or (Path.home() / ".luo_os" / "cells")
        self.network  = CellNetwork()
        self.episodic   = EpisodicCell(self.data_dir)
        self.semantic   = SemanticCell(self.data_dir)
        self.working    = WorkingCell(self.data_dir)
        self.dream      = DreamCell(self.data_dir)
        self.importance = ImportanceCell(self.data_dir)
        self.decay      = DecayCell(self.data_dir)
        for c in (self.episodic, self.semantic, self.working,
                  self.dream, self.importance, self.decay):
            self.network.register(c)

    # ── lifecycle ────────────────────────────────────────────
    def start(self):
        for c in (self.episodic, self.semantic, self.working,
                  self.dream, self.importance, self.decay):
            c.start()

    def stop(self):
        for c in (self.episodic, self.semantic, self.working,
                  self.dream, self.importance, self.decay):
            c.stop()

    # ── public store/recall API ──────────────────────────────
    def store(self, content: str, kind: str = "general",
              context: dict | None = None) -> int:
        """Store an episode; importance is auto-assessed; concepts auto-extracted."""
        return self.episodic.store(kind, content, context)

    def recall(self, query: str = "", limit: int = 10,
               kind: str | None = None) -> list[dict]:
        """Search episodic memory."""
        return self.episodic.recall(query, limit=limit, kind=kind)

    def note(self, content: str, tag: str = "note", meta: dict | None = None) -> int:
        """Add to working memory (the active scratchpad)."""
        return self.working.add(content, tag=tag, meta=meta)

    def working_snapshot(self, limit: int | None = None) -> list[dict]:
        return self.working.snapshot(limit=limit)

    def clear_working(self):
        self.working.clear()

    def facts(self, limit: int = 50, min_confidence: float = 0.3) -> list[dict]:
        """Get semantic facts LUOKAI has learned about the user."""
        return self.semantic.facts(limit=limit, min_confidence=min_confidence)

    def force_dream(self):
        """Trigger a dream cycle right now."""
        self.dream.force_dream()

    # ── stats ────────────────────────────────────────────────
    def stats(self) -> dict:
        net   = self.network.stats()
        s_ep  = self.episodic.stats()
        s_sem = self.semantic.stats()
        s_wk  = self.working.stats()
        s_dr  = self.dream.stats()
        s_im  = self.importance.stats()
        s_de  = self.decay.stats()
        return {
            "cells_running": net["cells_running"],
            "signals_sent":  net["signals_sent"],
            "synapses":      net["synapses"],
            "synapse_avg":   net["synapse_avg"],
            "episodes":      s_ep["episodes"],
            "high_importance": s_ep["high_importance"],
            "facts":         s_sem["facts"],
            "top_facts":     s_sem["top_facts"],
            "working_items": s_wk["items"],
            "working_capacity": s_wk["capacity"],
            "dreams":        s_dr["dreams"],
            "importance_scores": s_im["scored"],
            "decay_pulses":  s_de["pulses_fired"],
            "per_cell": {
                "episodic":   s_ep,
                "semantic":   s_sem,
                "working":    s_wk,
                "dream":      s_dr,
                "importance": s_im,
                "decay":      s_de,
            },
        }


# ──────────────────────────────────────────────────────────────
# Singleton
# ──────────────────────────────────────────────────────────────
_system: CellSystem | None = None


def get_system() -> CellSystem:
    """Get (or create + start) the cell system singleton."""
    global _system
    if _system is None:
        _system = CellSystem()
        _system.start()
    return _system


def stop_system():
    global _system
    if _system is not None:
        _system.stop()
        _system = None
