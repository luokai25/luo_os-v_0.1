"""
WorkingCell — bounded scratchpad for active context
────────────────────────────────────────────────────
The "now" of LUOKAI's awareness. Capacity-bounded (50 items default).
When full, oldest items get demoted to long-term episodic memory.

Listens for:
  • note_request   — adds an item to working memory
  • snapshot       — synchronous response with the current contents
  • clear_working  — drops all items
"""
import json
import time

from .base import MemoryCell, Signal


class WorkingCell(MemoryCell):
    cell_id       = "working"
    tick_interval = 30.0
    CAPACITY      = 50

    def _init_db(self):
        with self._conn() as c:
            c.execute("""
              CREATE TABLE IF NOT EXISTS items(
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                ts      REAL,
                tag     TEXT,
                content TEXT,
                meta    TEXT
              )
            """)

    def add(self, content: str, tag: str = "note", meta: dict | None = None) -> int:
        with self._conn() as c:
            cur = c.execute(
                "INSERT INTO items(ts,tag,content,meta) VALUES(?,?,?,?)",
                (time.time(), tag, content[:1000], json.dumps(meta or {})[:500])
            )
            new_id = cur.lastrowid
            # Enforce capacity
            count = c.execute("SELECT COUNT(*) FROM items").fetchone()[0]
            if count > self.CAPACITY:
                # Find the oldest items
                overflow = count - self.CAPACITY
                rows = c.execute(
                    "SELECT id, content, tag FROM items ORDER BY ts ASC LIMIT ?",
                    (overflow,)
                ).fetchall()
                for r in rows:
                    # Demote to long-term episodic
                    self.emit("demote_to_episodic", {
                        "kind":    f"working_overflow:{r['tag']}",
                        "content": r["content"],
                    }, target="episodic")
                # Delete from working
                c.executemany("DELETE FROM items WHERE id=?",
                              [(r["id"],) for r in rows])
        return new_id

    def snapshot(self, limit: int | None = None) -> list[dict]:
        sql = "SELECT id, ts, tag, content FROM items ORDER BY ts DESC"
        if limit:
            sql += f" LIMIT {limit}"
        with self._conn() as c:
            return [dict(r) for r in c.execute(sql).fetchall()]

    def clear(self):
        with self._conn() as c:
            c.execute("DELETE FROM items")

    # ── signal handlers ────────────────────────────────────────
    def on_signal(self, sig: Signal):
        if sig.kind == "note_request":
            tag     = sig.payload.get("tag", "note")
            content = sig.payload.get("content", "")
            meta    = sig.payload.get("meta")
            self.add(content, tag=tag, meta=meta)
        elif sig.kind == "snapshot_request":
            rq = sig.payload.get("response_q")
            if rq is not None:
                rq.put(self.snapshot(limit=sig.payload.get("limit")))
        elif sig.kind == "clear_working":
            self.clear()

    def stats(self) -> dict:
        with self._conn() as c:
            count = c.execute("SELECT COUNT(*) FROM items").fetchone()[0]
        return {
            "cell_id":  self.cell_id,
            "running":  self.is_running,
            "items":    count,
            "capacity": self.CAPACITY,
        }
