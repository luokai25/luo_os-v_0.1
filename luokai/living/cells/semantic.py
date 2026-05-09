"""
SemanticCell — pattern-to-fact promotion
─────────────────────────────────────────
Watches new episodes. Extracts concept keywords. When a concept has been
seen 3+ times across episodes, it gets promoted to a permanent fact with
a confidence score.

Facts are LUOKAI's long-term knowledge about THIS user — built up purely
from observed patterns, no training, no LLM hallucination.

Fires:
  • new_fact (when something gets promoted)

Listens for:
  • new_episode (from EpisodicCell) — extracts concepts, counts hits
  • dream_consolidate (from DreamCell) — does deeper pattern-merging during idle
"""
import re
import time
from collections import Counter

from .base import MemoryCell, Signal


# Words to ignore when extracting concepts from text
_STOPWORDS = {
    "the","a","an","is","are","was","were","be","been","being","have","has","had",
    "do","does","did","will","would","could","should","may","might","must","shall",
    "i","you","he","she","it","we","they","me","him","her","us","them","my","your",
    "his","its","our","their","mine","yours","ours","theirs","this","that","these",
    "those","what","which","who","whom","where","when","why","how","all","any","both",
    "each","few","more","most","other","some","such","no","nor","not","only","own",
    "same","so","than","too","very","just","with","from","into","onto","upon","about",
    "against","between","through","during","before","after","above","below","up","down",
    "in","out","on","off","over","under","again","further","then","once","and","but","or",
    "if","because","as","until","while","of","at","by","for","like","said","told",
    "yes","no","ok","okay","really","also","still","always","never","often","sometimes",
    "now","later","today","tomorrow","yesterday",
}


def extract_concepts(text: str, max_n: int = 10) -> list[str]:
    """Extract candidate concept keywords from text."""
    words = re.findall(r"[a-zA-Z][a-zA-Z']{3,}", text.lower())
    filtered = [w for w in words if w not in _STOPWORDS and len(w) >= 4]
    if not filtered:
        return []
    counts = Counter(filtered)
    return [w for w, _ in counts.most_common(max_n)]


class SemanticCell(MemoryCell):
    cell_id       = "semantic"
    tick_interval = 60.0  # promote/decay confidence once a minute

    PROMOTION_THRESHOLD = 3   # hits needed to promote to fact

    def _init_db(self):
        with self._conn() as c:
            c.execute("""
              CREATE TABLE IF NOT EXISTS concept_hits(
                concept    TEXT PRIMARY KEY,
                hits       INTEGER DEFAULT 1,
                last_seen  REAL,
                first_seen REAL
              )
            """)
            c.execute("""
              CREATE TABLE IF NOT EXISTS facts(
                concept    TEXT PRIMARY KEY,
                confidence REAL DEFAULT 0.5,
                hits       INTEGER DEFAULT 3,
                first_seen REAL,
                last_seen  REAL,
                example    TEXT
              )
            """)
            c.execute("CREATE INDEX IF NOT EXISTS idx_facts_conf ON facts(confidence DESC)")

    def on_signal(self, sig: Signal):
        if sig.kind == "new_episode":
            text = sig.payload.get("content", "")
            concepts = extract_concepts(text)
            if not concepts:
                return
            now = time.time()
            with self._conn() as c:
                for concept in concepts:
                    # Bump the concept count
                    cur = c.execute(
                        "SELECT hits, first_seen FROM concept_hits WHERE concept=?",
                        (concept,)
                    ).fetchone()
                    if cur:
                        new_hits = cur["hits"] + 1
                        c.execute(
                            "UPDATE concept_hits SET hits=?, last_seen=? WHERE concept=?",
                            (new_hits, now, concept)
                        )
                        # Check for promotion to fact
                        if new_hits >= self.PROMOTION_THRESHOLD:
                            existing = c.execute(
                                "SELECT confidence, hits FROM facts WHERE concept=?",
                                (concept,)
                            ).fetchone()
                            if existing:
                                # Reinforce
                                c.execute("""UPDATE facts
                                             SET confidence=MIN(1.0, confidence+0.05),
                                                 hits=?, last_seen=?
                                             WHERE concept=?""",
                                          (new_hits, now, concept))
                            else:
                                # Promote!
                                c.execute("""INSERT INTO facts(concept, confidence, hits,
                                                first_seen, last_seen, example)
                                             VALUES(?, 0.5, ?, ?, ?, ?)""",
                                          (concept, new_hits, cur["first_seen"], now, text[:200]))
                                self.emit("new_fact", {"concept": concept, "hits": new_hits})
                    else:
                        c.execute("""INSERT INTO concept_hits(concept,hits,first_seen,last_seen)
                                     VALUES(?,1,?,?)""", (concept, now, now))
        elif sig.kind == "dream_consolidate":
            # During dream, do deeper analysis — but for now just bump
            # confidence of facts that have been recently revisited
            self._dream_pass()

    def _dream_pass(self):
        """During dream: bump confidence on recently-active facts, decay stale ones."""
        now = time.time()
        with self._conn() as c:
            # Bump active facts
            c.execute("""UPDATE facts
                         SET confidence = MIN(1.0, confidence + 0.02)
                         WHERE last_seen > ?""", (now - 86400,))   # active in last day
            # Decay long-stale facts
            c.execute("""UPDATE facts
                         SET confidence = MAX(0.0, confidence - 0.01)
                         WHERE last_seen < ?""", (now - 86400 * 7,))  # idle a week+
            # Drop facts whose confidence got too low
            c.execute("DELETE FROM facts WHERE confidence < 0.05")

    def tick(self):
        """Periodic concept-table cleanup so it doesn't bloat forever."""
        now = time.time()
        with self._conn() as c:
            # Drop concepts that are still below threshold and haven't been seen in a week
            c.execute("""DELETE FROM concept_hits
                         WHERE hits < ? AND last_seen < ?""",
                      (self.PROMOTION_THRESHOLD, now - 86400 * 7))

    # ── public API ───────────────────────────────────────────
    def facts(self, limit: int = 50, min_confidence: float = 0.0) -> list[dict]:
        with self._conn() as c:
            rows = c.execute(
                """SELECT concept, confidence, hits, last_seen, example
                   FROM facts WHERE confidence >= ?
                   ORDER BY confidence DESC LIMIT ?""",
                (min_confidence, limit)
            ).fetchall()
        return [dict(r) for r in rows]

    def known(self, concept: str) -> bool:
        with self._conn() as c:
            r = c.execute("SELECT 1 FROM facts WHERE concept=?", (concept.lower(),)).fetchone()
        return r is not None

    def stats(self) -> dict:
        with self._conn() as c:
            tot_hits = c.execute("SELECT COUNT(*) FROM concept_hits").fetchone()[0]
            tot_facts = c.execute("SELECT COUNT(*) FROM facts").fetchone()[0]
            top = c.execute("SELECT concept FROM facts ORDER BY confidence DESC LIMIT 5").fetchall()
        return {
            "cell_id":   self.cell_id,
            "running":   self.is_running,
            "concepts_tracked": tot_hits,
            "facts":     tot_facts,
            "top_facts": [r["concept"] for r in top],
        }
