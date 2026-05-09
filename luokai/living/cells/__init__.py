"""
LuoOS Memory Cell Organism
───────────────────────────
6 specialized cells working together as a living memory system:

  EpisodicCell    Verbatim event storage with importance scoring
  SemanticCell    Pattern → fact promotion (3+ hits = fact)
  WorkingCell     Bounded scratchpad (capacity 50, oldest demoted)
  DreamCell       Idle-time consolidation, fires DecayPulse + SemanticPass
  ImportanceCell  Heuristic 0..1 scoring of new events
  DecayCell       Ebbinghaus weakening of cold memories

Each cell is a daemon thread with its own SQLite DB, communicating via
signals on a CellNetwork bus. Cells form Hebbian synapses — those that
fire together strengthen their connection.

Lineage: KAI Agent v22 (which was inspired by luokai25/luo_os).
This is the reference implementation, integrated into LuoOS proper.

Usage:
    from luokai.living.cells import get_system

    cells = get_system()                          # spawns all 6 daemon threads
    eid = cells.store("user opened Flask", "app") # → all relevant cells fire
    cells.note("currently debugging server.py")   # → WorkingCell
    items = cells.recall("flask")                 # ← EpisodicCell
    facts = cells.facts()                         # ← SemanticCell facts
    cells.force_dream()                           # → DreamCell consolidation
    stats = cells.stats()                         # whole organism
"""
from .base       import MemoryCell, CellNetwork, Signal
from .episodic   import EpisodicCell
from .semantic   import SemanticCell, extract_concepts
from .working    import WorkingCell
from .dream      import DreamCell
from .importance import ImportanceCell, assess
from .decay      import DecayCell
from .system     import CellSystem, get_system, stop_system

__all__ = [
    "MemoryCell", "CellNetwork", "Signal",
    "EpisodicCell", "SemanticCell", "extract_concepts",
    "WorkingCell", "DreamCell",
    "ImportanceCell", "assess",
    "DecayCell",
    "CellSystem", "get_system", "stop_system",
]
