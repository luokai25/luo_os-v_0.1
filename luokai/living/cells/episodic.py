"""
EpisodicCell — verbatim event storage
──────────────────────────────────────
Stores every significant event with full context. Never auto-deletes.
Each episode has: id, ts, kind, content, context (json), importance.

Fires:
  • new_episode    → SemanticCell  (so it can look for repeating patterns)
  • assess         → ImportanceCell (to score the episode)

Listens for:
  • importance_score (from ImportanceCell) — updates the episode's score
  • recall (from anyone) — synchronous query, payload['response_q'] gets results
  • decay_check (from DecayCell) — returns episodes ranked by age vs importance
"""
import json
import time

from .base import MemoryCell, Signal


class EpisodicCell(MemoryCell):
    cell_id       = "episodic"
    tick_interval = 30.0   # rarely needs to do background work

    def _init_db(self):
        with self._conn() as c:
            c.execute("""
              CREATE TABLE IF NOT EXISTS episodes(
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                ts          REAL    NOT NULL,
                kind        TEXT    NOT NULL,
                content     TEXT    NOT NULL,
                context     TEXT,
                importance  REAL    DEFAULT 0.5,
                last_recall REAL    DEFAULT 0
              )
            """)
            c.execute("CREATE INDEX IF NOT EXISTS idx_kind ON episodes(kind)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_ts ON episodes(ts)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_imp ON episodes(importance DESC)")

    # ── public API ────────────────────────────────────────────
    def store(self, kind: str, content: str, context: dict | None = None) -> int:
        """Store an episode. Returns its id."""
        with self._conn() as c:
            cur = c.execute(
                "INSERT INTO episodes(ts,kind,content,context) VALUES(?,?,?,?)",
                (time.time(), kind, content[:5000],
                 json.dumps(context or {})[:2000])
            )
            ep_id = cur.lastrowid
        # Tell SemanticCell about new episode
        self.emit("new_episode", {"id": ep_id, "kind": kind, "content": content[:500]},
                  target="semantic")
        # Ask ImportanceCell to score it
        self.emit("assess", {"id": ep_id, "kind": kind, "content": content[:500]},
                  target="importance")
        return ep_id

    def recall(self, query: str = "", limit: int = 10,
               kind: str | None = None) -> list[dict]:
        """Search episodes by content substring + recency + importance."""
        sql = "SELECT id, ts, kind, content, importance FROM episodes "
        params: list = []
        clauses: list[str] = []
        if query:
            clauses.append("content LIKE ?")
            params.append(f"%{query}%")
        if kind:
            clauses.append("kind = ?")
            params.append(kind)
        if clauses:
            sql += "WHERE " + " AND ".join(clauses) + " "
        sql += "ORDER BY importance DESC, ts DESC LIMIT ?"
        params.append(limit)
        with self._conn() as c:
            rows = c.execute(sql, params).fetchall()
            # Update last_recall for hits
            now = time.time()
            for r in rows:
                c.execute("UPDATE episodes SET last_recall=? WHERE id=?",
                          (now, r["id"]))
        return [dict(r) for r in rows]

    def count(self) -> int:
        with self._conn() as c:
            return c.execute("SELECT COUNT(*) FROM episodes").fetchone()[0]

    # ── signal handlers ───────────────────────────────────────
    def on_signal(self, sig: Signal):
        if sig.kind == "importance_score":
            ep_id = sig.payload.get("id")
            score = sig.payload.get("score")
            if ep_id and score is not None:
                with self._conn() as c:
                    c.execute("UPDATE episodes SET importance=? WHERE id=?",
                              (float(score), int(ep_id)))
        elif sig.kind == "recall_request":
            q     = sig.payload.get("query", "")
            limit = sig.payload.get("limit", 10)
            results = self.recall(q, limit=limit)
            rq = sig.payload.get("response_q")
            if rq is not None:
                rq.put(results)
        elif sig.kind == "decay_apply":
            # Decay cell tells us to weaken specific episodes
            ids   = sig.payload.get("ids", [])
            delta = sig.payload.get("delta", 0.01)
            if ids:
                with self._conn() as c:
                    c.executemany(
                        "UPDATE episodes SET importance=MAX(0.0, importance-?) WHERE id=?",
                        [(delta, i) for i in ids]
                    )
        elif sig.kind == "decay_pulse_apply":
            # Decay cell asked us to apply a decay pass over all old episodes
            base    = float(sig.payload.get("base", 0.02))
            max_age = float(sig.payload.get("max_age", 86400 * 7))
            cutoff  = time.time() - max_age
            with self._conn() as c:
                # Decay rate scales with (1 - importance^2): high-importance memories barely move
                c.execute("""
                    UPDATE episodes
                    SET importance = MAX(0.0, importance - ? * (1 - importance*importance))
                    WHERE ts < ? AND last_recall < ?
                """, (base, cutoff, cutoff))

    # ── stats ─────────────────────────────────────────────────
    def stats(self) -> dict:
        with self._conn() as c:
            tot = c.execute("SELECT COUNT(*) FROM episodes").fetchone()[0]
            avg = c.execute("SELECT AVG(importance) FROM episodes").fetchone()[0] or 0
            high = c.execute("SELECT COUNT(*) FROM episodes WHERE importance > 0.7").fetchone()[0]
        return {
            "cell_id":       self.cell_id,
            "running":       self.is_running,
            "episodes":      tot,
            "high_importance": high,
            "avg_importance": round(avg, 2),
        }
