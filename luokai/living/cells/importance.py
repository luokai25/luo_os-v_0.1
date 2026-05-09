"""
ImportanceCell — heuristic 0..1 scoring of new events
──────────────────────────────────────────────────────
When EpisodicCell stores something, this cell scores it on a few signals:
  • length         — longer = a bit more important
  • code blocks    — code = much more important
  • emotion words  — strong emotion = important
  • imperative kw  — "remember", "important", "never forget" = +0.3
  • file paths     — references to specific files = important
  • numbers/dates  — facts with numbers tend to matter
  • repetition     — already-seen content = lower

Returns a score 0.0..1.0. The score is sent back to EpisodicCell as a
signal so it can update the episode's `importance` column.

This is a HEURISTIC, not a model. Honest about that.
"""
import re
import time

from .base import MemoryCell, Signal


# Important keyword groups
_IMPERATIVES = {"remember","important","never forget","key fact","crucial",
                 "critical","mark this","note this","priority"}
_EMOTIONAL   = {"love","hate","afraid","worried","excited","frustrated",
                 "annoyed","amazing","terrible","awful","wonderful","sad","happy"}


def assess(content: str) -> float:
    """Compute importance score 0..1 from text heuristics."""
    if not content:
        return 0.1
    lower    = content.lower()
    score    = 0.3   # base
    # Length bonus (capped)
    score += min(0.15, len(content) / 4000)
    # Code blocks
    if "```" in content or content.count("    ") > 3:
        score += 0.2
    # Imperatives
    for kw in _IMPERATIVES:
        if kw in lower:
            score += 0.3
            break
    # Emotion
    for kw in _EMOTIONAL:
        if kw in lower:
            score += 0.1
            break
    # File paths or URLs
    if re.search(r"[/\\][\w.\-]+\.\w{1,5}", content):
        score += 0.05
    if re.search(r"https?://", content):
        score += 0.05
    # Numbers / dates
    if re.search(r"\b\d{4}-\d{2}-\d{2}\b", content):
        score += 0.05
    if re.search(r"\$\d+|\b\d+%", content):
        score += 0.05
    return max(0.0, min(1.0, score))


class ImportanceCell(MemoryCell):
    cell_id       = "importance"
    tick_interval = 120.0  # very rarely needed

    def _init_db(self):
        with self._conn() as c:
            c.execute("""
              CREATE TABLE IF NOT EXISTS scores(
                ts        REAL,
                ep_id     INTEGER,
                content_h TEXT,
                score     REAL
              )
            """)
            c.execute("CREATE INDEX IF NOT EXISTS idx_scores_ep ON scores(ep_id)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_scores_h  ON scores(content_h)")

    def on_signal(self, sig: Signal):
        if sig.kind != "assess":
            return
        ep_id   = sig.payload.get("id")
        content = sig.payload.get("content", "")
        if not ep_id or not content:
            return
        # Check for repetition penalty
        import hashlib
        h = hashlib.md5(content.encode("utf-8", errors="ignore")).hexdigest()[:16]
        with self._conn() as c:
            prior = c.execute("SELECT COUNT(*) FROM scores WHERE content_h=?",
                              (h,)).fetchone()[0]
            base = assess(content)
            # Repeated content gets damped
            score = base * (1.0 / (1.0 + 0.2 * prior))
            score = round(min(1.0, score), 3)
            c.execute("INSERT INTO scores(ts, ep_id, content_h, score) VALUES(?,?,?,?)",
                      (time.time(), ep_id, h, score))
        # Tell EpisodicCell the score
        self.emit("importance_score", {"id": ep_id, "score": score},
                  target="episodic")

    def stats(self) -> dict:
        with self._conn() as c:
            total = c.execute("SELECT COUNT(*) FROM scores").fetchone()[0]
            avg   = c.execute("SELECT AVG(score) FROM scores").fetchone()[0] or 0
        return {
            "cell_id":      self.cell_id,
            "running":      self.is_running,
            "scored":       total,
            "avg_score":    round(avg, 2),
        }
