#!/usr/bin/env python3
"""
luo_cells.py — The Eight Specialized Luo-Cells
================================================
Each cell is a living, autonomous memory capability.
They run in the background, signal each other, and together
form a memory organism that is more than the sum of its parts.

  EpisodicCell      — stores raw events with full temporal context
  SemanticCell      — promotes repeated episodes into permanent facts
  SkillCell         — crystallizes successful tool chains into reusable skills
  WorkingCell       — in-session scratchpad, auto-flushes to palace on exit
  DecayCell         — continuously weakens cold memories (Ebbinghaus curve)
  DreamCell         — idle-time consolidation (hippocampal replay)
  ImportanceCell    — tags high-impact events to resist decay
  AssociativeCell   — graph of linked memories for spreading activation

Created by Luo Kai (luokai25) — luo_memory v1.0
"""

import json
import logging
import os
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from luo_cell import LuoCell, LuoCellNetwork, Signal

logger = logging.getLogger("luo_memory")


# ─────────────────────────────────────────────
# EpisodicCell  (hippocampus)
# ─────────────────────────────────────────────

class EpisodicCell(LuoCell):
    """
    Stores every event verbatim with who/what/when/where context.
    Fires a 'new_episode' signal to SemanticCell after every store.
    Never discards — the human brain lossy-compresses, we don't.
    """

    TICK_INTERVAL = 60.0

    def __init__(self, network: LuoCellNetwork, palace_path: str):
        super().__init__("episodic", "EpisodicCell", network, palace_path)
        self._init_db()

    def _db_path(self) -> str:
        p = self.cell_path()
        return str(p / "episodes.db")

    def _init_db(self):
        with sqlite3.connect(self._db_path()) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS episodes (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id  TEXT,
                    agent_id    TEXT,
                    content     TEXT NOT NULL,
                    role        TEXT DEFAULT 'exchange',
                    importance  REAL DEFAULT 0.5,
                    access_count INTEGER DEFAULT 0,
                    last_accessed REAL DEFAULT 0,
                    timestamp   REAL NOT NULL,
                    metadata    TEXT DEFAULT '{}'
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_session ON episodes(session_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON episodes(timestamp)")
            conn.commit()

    async def on_signal(self, signal: Signal):
        if signal.signal_type == "store":
            episode_id = self._store(signal.payload)
            # notify semantic cell
            self.fire("semantic", "new_episode", {
                "episode_id": episode_id,
                "content": signal.payload.get("content", ""),
                "session_id": signal.payload.get("session_id", ""),
            })
            # notify importance cell
            self.fire("importance", "assess", {
                "episode_id": episode_id,
                "content": signal.payload.get("content", ""),
            })

        elif signal.signal_type == "recall":
            results = self._recall(
                query=signal.payload.get("query", ""),
                session_id=signal.payload.get("session_id"),
                limit=signal.payload.get("limit", 10),
            )
            # put results into payload for caller to read
            signal.payload["_results"] = results

        elif signal.signal_type == "repair_request":
            # another cell is asking for help — log and try to re-index
            logger.info(f"[{self.cell_id}] repair request received from "
                        f"{signal.payload.get('damaged_cell')}")

    def _store(self, payload: Dict) -> int:
        with sqlite3.connect(self._db_path()) as conn:
            cursor = conn.execute("""
                INSERT INTO episodes
                (session_id, agent_id, content, role, importance, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                payload.get("session_id", "default"),
                payload.get("agent_id", "luo_agent"),
                payload.get("content", ""),
                payload.get("role", "exchange"),
                payload.get("importance", 0.5),
                time.time(),
                json.dumps(payload.get("metadata", {})),
            ))
            conn.commit()
            return cursor.lastrowid

    def _recall(
        self,
        query: str = "",
        session_id: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict]:
        with sqlite3.connect(self._db_path()) as conn:
            if session_id:
                rows = conn.execute("""
                    SELECT id, content, role, importance, timestamp, session_id
                    FROM episodes WHERE session_id = ?
                    ORDER BY timestamp DESC LIMIT ?
                """, (session_id, limit)).fetchall()
            elif query:
                rows = conn.execute("""
                    SELECT id, content, role, importance, timestamp, session_id
                    FROM episodes WHERE content LIKE ?
                    ORDER BY importance DESC, timestamp DESC LIMIT ?
                """, (f"%{query}%", limit)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT id, content, role, importance, timestamp, session_id
                    FROM episodes ORDER BY timestamp DESC LIMIT ?
                """, (limit,)).fetchall()

            # update access counts
            ids = [r[0] for r in rows]
            if ids:
                conn.execute(
                    f"UPDATE episodes SET access_count=access_count+1, "
                    f"last_accessed=? WHERE id IN ({','.join('?'*len(ids))})",
                    [time.time()] + ids
                )
                conn.commit()

        return [
            {
                "id": r[0], "content": r[1], "role": r[2],
                "importance": r[3], "timestamp": r[4], "session_id": r[5],
            }
            for r in rows
        ]

    async def tick(self):
        # log how many episodes we hold
        with sqlite3.connect(self._db_path()) as conn:
            count = conn.execute("SELECT COUNT(*) FROM episodes").fetchone()[0]
        logger.debug(f"[{self.cell_id}] holding {count} episodes")


# ─────────────────────────────────────────────
# SemanticCell  (cerebral cortex)
# ─────────────────────────────────────────────

class SemanticCell(LuoCell):
    """
    Promotes repeated episodes into permanent semantic facts.
    When the same concept appears 3+ times across sessions,
    it stops being a 'memory of an event' and becomes 'knowledge'.
    This mirrors how the brain semantizes episodic memory over time.
    """

    TICK_INTERVAL = 120.0
    PROMOTION_THRESHOLD = 3   # episodes needed to promote a fact

    def __init__(self, network: LuoCellNetwork, palace_path: str):
        super().__init__("semantic", "SemanticCell", network, palace_path)
        self._init_db()
        self._episode_buffer: List[Dict] = []

    def _db_path(self) -> str:
        return str(self.cell_path() / "facts.db")

    def _init_db(self):
        with sqlite3.connect(self._db_path()) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS facts (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    key         TEXT UNIQUE NOT NULL,
                    value       TEXT NOT NULL,
                    confidence  REAL DEFAULT 0.5,
                    source_count INTEGER DEFAULT 1,
                    first_seen  REAL,
                    last_updated REAL,
                    metadata    TEXT DEFAULT '{}'
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS candidates (
                    content     TEXT PRIMARY KEY,
                    seen_count  INTEGER DEFAULT 1,
                    last_seen   REAL
                )
            """)
            conn.commit()

    async def on_signal(self, signal: Signal):
        if signal.signal_type == "new_episode":
            content = signal.payload.get("content", "")
            self._track_candidate(content)

        elif signal.signal_type == "learn_fact":
            self._store_fact(
                key=signal.payload.get("key", ""),
                value=signal.payload.get("value", ""),
                confidence=signal.payload.get("confidence", 0.8),
            )

        elif signal.signal_type == "get_facts":
            signal.payload["_results"] = self._get_all_facts()

    def _track_candidate(self, content: str):
        """Track how many times a concept appears — promote when threshold met."""
        key = content[:120].lower().strip()
        with sqlite3.connect(self._db_path()) as conn:
            conn.execute("""
                INSERT INTO candidates (content, seen_count, last_seen)
                VALUES (?, 1, ?)
                ON CONFLICT(content) DO UPDATE SET
                    seen_count = seen_count + 1,
                    last_seen = ?
            """, (key, time.time(), time.time()))
            conn.commit()

            row = conn.execute(
                "SELECT seen_count FROM candidates WHERE content=?", (key,)
            ).fetchone()

            if row and row[0] >= self.PROMOTION_THRESHOLD:
                # promote to fact
                self._store_fact(
                    key=key[:60],
                    value=content,
                    confidence=min(0.99, row[0] / 10.0),
                )
                logger.info(
                    f"[{self.cell_id}] promoted fact after {row[0]} observations: "
                    f"{key[:50]}..."
                )

    def _store_fact(self, key: str, value: str, confidence: float = 0.8):
        with sqlite3.connect(self._db_path()) as conn:
            conn.execute("""
                INSERT INTO facts (key, value, confidence, source_count, first_seen, last_updated)
                VALUES (?, ?, ?, 1, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value = ?,
                    confidence = MIN(0.99, confidence + 0.05),
                    source_count = source_count + 1,
                    last_updated = ?
            """, (key, value, confidence, time.time(), time.time(),
                  value, time.time()))
            conn.commit()

    def _get_all_facts(self) -> List[Dict]:
        with sqlite3.connect(self._db_path()) as conn:
            rows = conn.execute("""
                SELECT key, value, confidence, source_count, last_updated
                FROM facts ORDER BY confidence DESC, source_count DESC
            """).fetchall()
        return [
            {"key": r[0], "value": r[1], "confidence": r[2],
             "source_count": r[3], "last_updated": r[4]}
            for r in rows
        ]

    async def tick(self):
        with sqlite3.connect(self._db_path()) as conn:
            facts = conn.execute("SELECT COUNT(*) FROM facts").fetchone()[0]
            candidates = conn.execute("SELECT COUNT(*) FROM candidates").fetchone()[0]
        logger.debug(f"[{self.cell_id}] {facts} facts, {candidates} candidates")


# ─────────────────────────────────────────────
# SkillCell  (cerebellum)
# ─────────────────────────────────────────────

class SkillCell(LuoCell):
    """
    Observes tool execution chains and crystallizes successful ones into skills.
    A skill is a named sequence of tool calls that achieved a goal.
    Once crystallized, LUOKAI can invoke the skill by name instead of
    reasoning through it from scratch each time.
    """

    TICK_INTERVAL = 90.0
    SUCCESS_THRESHOLD = 2   # successful runs needed to crystallize a skill

    def __init__(self, network: LuoCellNetwork, palace_path: str):
        super().__init__("skill", "SkillCell", network, palace_path)
        self._init_db()
        self._current_chain: List[Dict] = []

    def _db_path(self) -> str:
        return str(self.cell_path() / "skills.db")

    def _init_db(self):
        with sqlite3.connect(self._db_path()) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS skills (
                    id           INTEGER PRIMARY KEY AUTOINCREMENT,
                    name         TEXT UNIQUE NOT NULL,
                    description  TEXT,
                    tool_chain   TEXT NOT NULL,
                    success_count INTEGER DEFAULT 1,
                    last_used    REAL,
                    created_at   REAL,
                    metadata     TEXT DEFAULT '{}'
                )
            """)
            conn.commit()

    async def on_signal(self, signal: Signal):
        if signal.signal_type == "tool_executed":
            self._current_chain.append({
                "tool": signal.payload.get("tool"),
                "args": signal.payload.get("args", {}),
                "result_summary": signal.payload.get("result_summary", ""),
                "success": signal.payload.get("success", True),
                "timestamp": time.time(),
            })

        elif signal.signal_type == "task_completed":
            if signal.payload.get("success") and len(self._current_chain) >= 2:
                self._consider_crystallization(
                    goal=signal.payload.get("goal", ""),
                    chain=self._current_chain.copy(),
                )
            self._current_chain.clear()

        elif signal.signal_type == "get_skill":
            name = signal.payload.get("name", "")
            signal.payload["_result"] = self._get_skill(name)

        elif signal.signal_type == "list_skills":
            signal.payload["_results"] = self._list_skills()

    def _consider_crystallization(self, goal: str, chain: List[Dict]):
        """Attempt to save or reinforce a skill from a successful chain."""
        skill_name = goal[:60].lower().replace(" ", "_")[:40] if goal else (
            "_".join(c["tool"] for c in chain[:3])
        )
        chain_json = json.dumps(chain)

        with sqlite3.connect(self._db_path()) as conn:
            conn.execute("""
                INSERT INTO skills (name, description, tool_chain, success_count,
                                    last_used, created_at)
                VALUES (?, ?, ?, 1, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    success_count = success_count + 1,
                    last_used = ?,
                    tool_chain = ?
            """, (skill_name, goal, chain_json, time.time(), time.time(),
                  time.time(), chain_json))
            conn.commit()
            logger.info(f"[{self.cell_id}] skill crystallized: {skill_name}")

    def _get_skill(self, name: str) -> Optional[Dict]:
        with sqlite3.connect(self._db_path()) as conn:
            row = conn.execute(
                "SELECT name, description, tool_chain, success_count FROM skills WHERE name=?",
                (name,)
            ).fetchone()
        if row:
            return {
                "name": row[0], "description": row[1],
                "tool_chain": json.loads(row[2]), "success_count": row[3],
            }
        return None

    def _list_skills(self) -> List[Dict]:
        with sqlite3.connect(self._db_path()) as conn:
            rows = conn.execute("""
                SELECT name, description, success_count, last_used
                FROM skills ORDER BY success_count DESC
            """).fetchall()
        return [
            {"name": r[0], "description": r[1],
             "success_count": r[2], "last_used": r[3]}
            for r in rows
        ]

    async def tick(self):
        with sqlite3.connect(self._db_path()) as conn:
            count = conn.execute("SELECT COUNT(*) FROM skills").fetchone()[0]
        logger.debug(f"[{self.cell_id}] {count} crystallized skills")


# ─────────────────────────────────────────────
# WorkingCell  (prefrontal cortex)
# ─────────────────────────────────────────────

class WorkingCell(LuoCell):
    """
    In-session scratchpad — the '7±2 items' short-term buffer.
    Holds the current task context, tool results, and reasoning steps.
    Auto-flushes to EpisodicCell at session end.
    """

    TICK_INTERVAL = 10.0
    MAX_SLOTS = 12   # slightly more generous than human working memory

    def __init__(self, network: LuoCellNetwork, palace_path: str):
        super().__init__("working", "WorkingCell", network, palace_path)
        self._slots: List[Dict] = []
        self._session_id: str = f"session_{int(time.time())}"

    async def on_signal(self, signal: Signal):
        if signal.signal_type == "push":
            self._push(signal.payload)
            signal.payload["_session_id"] = self._session_id

        elif signal.signal_type == "peek":
            signal.payload["_slots"] = self._slots.copy()

        elif signal.signal_type == "flush":
            await self._flush()

        elif signal.signal_type == "new_session":
            await self._flush()
            self._session_id = signal.payload.get(
                "session_id", f"session_{int(time.time())}"
            )
            self._slots.clear()

    def _push(self, payload: Dict):
        """Add item to working memory, evicting oldest if full."""
        item = {
            "content": payload.get("content", ""),
            "role": payload.get("role", "observation"),
            "timestamp": time.time(),
        }
        if len(self._slots) >= self.MAX_SLOTS:
            evicted = self._slots.pop(0)
            logger.debug(
                f"[{self.cell_id}] evicted: {evicted['content'][:40]}..."
            )
        self._slots.append(item)

    async def _flush(self):
        """Push all slots to EpisodicCell for long-term storage."""
        if not self._slots:
            return
        for slot in self._slots:
            self.fire("episodic", "store", {
                "content": slot["content"],
                "role": slot["role"],
                "session_id": self._session_id,
                "importance": 0.4,
            })
        logger.info(
            f"[{self.cell_id}] flushed {len(self._slots)} items "
            f"from session {self._session_id}"
        )
        self._slots.clear()

    async def tick(self):
        logger.debug(
            f"[{self.cell_id}] {len(self._slots)}/{self.MAX_SLOTS} slots used "
            f"in session {self._session_id}"
        )


# ─────────────────────────────────────────────
# DecayCell  (Ebbinghaus forgetting curve)
# ─────────────────────────────────────────────

class DecayCell(LuoCell):
    """
    Always ticking. Weakens synapse connections that haven't fired recently.
    High-importance memories and recently-accessed memories decay slower.
    This is the Ebbinghaus forgetting curve applied to AI memory.

    decay_score = base_decay × (1 / (1 + access_count)) × time_factor
    """

    TICK_INTERVAL = 300.0    # run every 5 minutes
    DECAY_RATE = 0.005        # per tick, per cold connection
    HOT_THRESHOLD = 3600      # seconds — memories accessed within 1 hour are "hot"

    def __init__(self, network: LuoCellNetwork, palace_path: str):
        super().__init__("decay", "DecayCell", network, palace_path)

    async def on_signal(self, signal: Signal):
        if signal.signal_type == "force_decay":
            await self._run_decay()

    async def tick(self):
        await self._run_decay()

    async def _run_decay(self):
        """
        Decay all synaptic connections proportional to time since last fire.
        Hot connections (recently used) are protected.
        """
        synapses_db = os.path.join(self.palace_path, "synapses.db")
        if not os.path.exists(synapses_db):
            return

        now = time.time()
        hot_cutoff = now - self.HOT_THRESHOLD
        decayed_count = 0

        with sqlite3.connect(synapses_db) as conn:
            cold = conn.execute(
                "SELECT cell_a, cell_b, weight FROM synapses WHERE last_fired < ?",
                (hot_cutoff,)
            ).fetchall()

            for cell_a, cell_b, weight in cold:
                if weight <= 0.01:
                    continue  # already dead
                time_cold = now - hot_cutoff
                decay = self.DECAY_RATE * min(1.0, time_cold / 86400)
                new_weight = max(0.0, weight - decay)
                conn.execute(
                    "UPDATE synapses SET weight=? WHERE cell_a=? AND cell_b=?",
                    (new_weight, cell_a, cell_b)
                )
                decayed_count += 1

            conn.commit()

        if decayed_count:
            logger.debug(
                f"[{self.cell_id}] decayed {decayed_count} cold connections"
            )


# ─────────────────────────────────────────────
# DreamCell  (hippocampal replay / sleep)
# ─────────────────────────────────────────────

class DreamCell(LuoCell):
    """
    Activates when the system is idle. Replays recent episodes,
    clusters related memories, and fires promotions to SemanticCell.
    This is the AI equivalent of hippocampal replay during sleep.
    """

    TICK_INTERVAL = 600.0      # every 10 minutes
    IDLE_THRESHOLD = 120.0     # seconds of no activity before dreaming
    CLUSTER_WINDOW = 3600.0    # look at last hour's episodes

    def __init__(self, network: LuoCellNetwork, palace_path: str):
        super().__init__("dream", "DreamCell", network, palace_path)
        self._last_system_activity: float = time.time()

    async def on_signal(self, signal: Signal):
        if signal.signal_type in ("store", "new_episode", "tool_executed"):
            # any activity resets the idle timer
            self._last_system_activity = time.time()

        elif signal.signal_type == "force_dream":
            await self._consolidate()

    async def tick(self):
        idle_time = time.time() - self._last_system_activity
        if idle_time >= self.IDLE_THRESHOLD:
            logger.info(
                f"[{self.cell_id}] system idle {idle_time:.0f}s — dreaming"
            )
            await self._consolidate()

    async def _consolidate(self):
        """
        Replay recent episodes and emit promotion signals for patterns found.
        """
        # ask episodic cell for recent episodes via direct signal
        payload: Dict = {"limit": 50}
        self.fire("episodic", "recall", payload)
        # give episodic cell a moment to process
        import asyncio
        await asyncio.sleep(0.2)

        episodes = payload.get("_results", [])
        if len(episodes) < 3:
            return

        # simple clustering: find content that appears in multiple episodes
        content_words: Dict[str, int] = {}
        for ep in episodes:
            for word in ep["content"].lower().split():
                if len(word) > 4:
                    content_words[word] = content_words.get(word, 0) + 1

        # promote words that appear 3+ times as semantic signals
        promoted = 0
        for word, count in content_words.items():
            if count >= 3:
                self.fire("semantic", "learn_fact", {
                    "key": f"recurring_concept:{word}",
                    "value": f"concept '{word}' has appeared {count} times recently",
                    "confidence": min(0.9, count / 10.0),
                })
                promoted += 1

        if promoted:
            logger.info(
                f"[{self.cell_id}] dream consolidation: promoted {promoted} "
                f"concepts from {len(episodes)} episodes"
            )


# ─────────────────────────────────────────────
# ImportanceCell  (amygdala)
# ─────────────────────────────────────────────

class ImportanceCell(LuoCell):
    """
    The amygdala equivalent. Assesses incoming episodes for high importance
    and boosts their score so they resist decay.

    High-importance triggers:
      - error / exception keywords
      - decision / choice keywords
      - breakthrough / solved / completed keywords
      - explicit user-flagged items
    """

    TICK_INTERVAL = 60.0

    HIGH_IMPORTANCE_KEYWORDS = {
        "error", "exception", "failed", "crash", "bug",         # errors
        "decided", "decision", "chose", "choice",                # decisions
        "solved", "completed", "finished", "breakthrough",       # achievements
        "critical", "important", "remember", "never forget",     # explicit flags
        "goal", "objective", "priority",                         # goals
    }

    def __init__(self, network: LuoCellNetwork, palace_path: str):
        super().__init__("importance", "ImportanceCell", network, palace_path)

    async def on_signal(self, signal: Signal):
        if signal.signal_type == "assess":
            episode_id = signal.payload.get("episode_id")
            content = signal.payload.get("content", "").lower()
            importance = self._score(content)

            if importance >= 0.7:
                # update the episode's importance directly
                self.fire("episodic", "boost_importance", {
                    "episode_id": episode_id,
                    "importance": importance,
                })
                logger.info(
                    f"[{self.cell_id}] high-importance event "
                    f"(score={importance:.2f}): {content[:60]}..."
                )

    def _score(self, content: str) -> float:
        words = set(content.lower().split())
        hits = words & self.HIGH_IMPORTANCE_KEYWORDS
        base = 0.5
        boost = len(hits) * 0.15
        return min(0.95, base + boost)

    async def tick(self):
        pass


# ─────────────────────────────────────────────
# AssociativeCell  (spreading activation)
# ─────────────────────────────────────────────

class AssociativeCell(LuoCell):
    """
    Maintains a graph of associations between concepts.
    When one concept is activated, it spreads activation to its neighbors —
    exactly like how 'cat' activates 'dog', 'pet', 'fur' in the human brain.

    This enables luo_memory to surface related memories
    even when the query doesn't directly mention them.
    """

    TICK_INTERVAL = 180.0

    def __init__(self, network: LuoCellNetwork, palace_path: str):
        super().__init__("associative", "AssociativeCell", network, palace_path)
        self._init_db()

    def _db_path(self) -> str:
        return str(self.cell_path() / "associations.db")

    def _init_db(self):
        with sqlite3.connect(self._db_path()) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS associations (
                    concept_a   TEXT NOT NULL,
                    concept_b   TEXT NOT NULL,
                    strength    REAL DEFAULT 0.1,
                    co_count    INTEGER DEFAULT 1,
                    PRIMARY KEY (concept_a, concept_b)
                )
            """)
            conn.commit()

    async def on_signal(self, signal: Signal):
        if signal.signal_type == "new_episode":
            content = signal.payload.get("content", "")
            self._extract_and_link(content)

        elif signal.signal_type == "activate":
            concept = signal.payload.get("concept", "")
            neighbors = self._spread(concept)
            signal.payload["_neighbors"] = neighbors

    def _extract_and_link(self, content: str):
        """Extract meaningful words and link co-occurring ones."""
        words = [
            w.strip(".,!?;:") for w in content.split()
            if len(w) > 4 and w.isalpha()
        ]
        # link all word pairs that appear in same sentence
        with sqlite3.connect(self._db_path()) as conn:
            for i, word_a in enumerate(words):
                for word_b in words[i+1:i+5]:  # window of 5
                    if word_a == word_b:
                        continue
                    a, b = sorted([word_a.lower(), word_b.lower()])
                    conn.execute("""
                        INSERT INTO associations (concept_a, concept_b, strength, co_count)
                        VALUES (?, ?, 0.1, 1)
                        ON CONFLICT(concept_a, concept_b) DO UPDATE SET
                            strength = MIN(1.0, strength + 0.02),
                            co_count = co_count + 1
                    """, (a, b))
            conn.commit()

    def _spread(self, concept: str, depth: int = 1) -> List[Dict]:
        """Return concepts associated with the given concept."""
        with sqlite3.connect(self._db_path()) as conn:
            rows = conn.execute("""
                SELECT concept_b, strength FROM associations
                WHERE concept_a = ? AND strength >= 0.15
                UNION
                SELECT concept_a, strength FROM associations
                WHERE concept_b = ? AND strength >= 0.15
                ORDER BY strength DESC LIMIT 10
            """, (concept.lower(), concept.lower())).fetchall()
        return [{"concept": r[0], "strength": r[1]} for r in rows]

    async def tick(self):
        with sqlite3.connect(self._db_path()) as conn:
            count = conn.execute(
                "SELECT COUNT(*) FROM associations"
            ).fetchone()[0]
        logger.debug(f"[{self.cell_id}] {count} associations in graph")
