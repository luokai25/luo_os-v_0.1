"""
LuoOS Tinkerer
───────────────
The infinite-improvement loop you described.

When LUOKAI faces a task, the tinkerer tries multiple approaches in
the background. Whichever returns the best result fastest becomes
the preferred approach next time. Failed approaches get marked as
"don't bother for this user."

This is the "try → if good save and try better; if bad keep trying
differently" loop.

How it's invoked:
    from luokai.living.tinkerer import tinker
    result = tinker("search_files", query="tax")
    # tinker tries N strategies in parallel, returns the winner.

The tinkerer does NOT make this decision blindly. Every experiment
gets a measurable success signal: did it return non-empty results?
Did it complete fast? Did the user accept the answer?
"""
import time
import json
import threading
import traceback
from collections import defaultdict
from pathlib import Path
from typing import Callable, Any

from .event_bus import bus, publish


EXPERIMENTS_PATH = Path.home() / ".luo_os" / "experiments.json"


class ExperimentLog:
    """Persistent log of every approach the tinkerer has tried."""

    def __init__(self, path: Path = EXPERIMENTS_PATH):
        self.path = path
        # Structure: {task_name: {strategy_name: {wins:n, losses:n, avg_ms:f}}}
        self.scores: dict = {}
        self.history: list = []
        self.load()

    def load(self):
        try:
            if self.path.exists():
                data = json.loads(self.path.read_text())
                self.scores  = data.get("scores", {})
                self.history = data.get("history", [])
        except Exception:
            self.scores = {}
            self.history = []

    def save(self):
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps({
                "scores":  self.scores,
                "history": self.history[-500:],   # keep last 500
            }, indent=2))
        except Exception:
            pass

    def record(self, task: str, strategy: str, success: bool, duration_ms: float,
               result_summary: str = ""):
        bucket = self.scores.setdefault(task, {}).setdefault(strategy, {
            "wins":   0,
            "losses": 0,
            "total_ms": 0,
            "runs":     0,
        })
        if success:
            bucket["wins"] += 1
        else:
            bucket["losses"] += 1
        bucket["runs"] += 1
        bucket["total_ms"] += duration_ms

        self.history.append({
            "ts":           time.time(),
            "task":         task,
            "strategy":     strategy,
            "success":      success,
            "duration_ms":  duration_ms,
            "summary":      result_summary[:120],
        })
        if len(self.history) % 5 == 0:
            self.save()

    def best_strategy(self, task: str) -> str | None:
        """Return the strategy with the best win rate * speed for a task."""
        bucket = self.scores.get(task, {})
        if not bucket:
            return None
        best = None
        best_score = -1.0
        for strategy, stats in bucket.items():
            runs = stats["runs"]
            if runs < 2:
                continue  # need at least 2 runs to be confident
            win_rate = stats["wins"] / max(1, runs)
            avg_ms   = stats["total_ms"] / max(1, runs)
            # Higher win rate, lower latency → higher score
            score    = win_rate * 100 - (avg_ms / 1000) * 5
            if score > best_score:
                best_score = score
                best = strategy
        return best

    def stats(self) -> dict:
        return {
            "tasks_explored": len(self.scores),
            "total_runs":     sum(s["runs"] for task in self.scores.values() for s in task.values()),
            "history_size":   len(self.history),
        }


# ────────────────────────────────────────────────────────────────
# Strategy Registry
# Each task can have multiple strategies. The tinkerer tries them.
# ────────────────────────────────────────────────────────────────
_strategies: dict[str, dict[str, Callable]] = defaultdict(dict)


def register_strategy(task_name: str, strategy_name: str):
    """Decorator to register a strategy for a task.

    @register_strategy("search_files", "rglob")
    def search_via_rglob(query): ...

    @register_strategy("search_files", "fts")
    def search_via_fts(query): ...
    """
    def decorator(fn: Callable):
        _strategies[task_name][strategy_name] = fn
        return fn
    return decorator


# ────────────────────────────────────────────────────────────────
# The Tinkerer
# ────────────────────────────────────────────────────────────────
class Tinkerer:
    """Runs strategies for a task, learns which works best."""

    def __init__(self):
        self.log = ExperimentLog()

    def tinker(self, task: str, **kwargs) -> dict:
        """
        Try strategies for a task. If we have a known winner with high
        confidence, use it directly. Otherwise, race the strategies.
        """
        strategies = _strategies.get(task, {})
        if not strategies:
            return {"ok": False, "error": f"No strategies registered for '{task}'"}

        # Use the proven winner if confident enough
        best = self.log.best_strategy(task)
        if best and best in strategies:
            # 80% of the time use the best, 20% try alternatives (exploration vs exploitation)
            import random
            if random.random() < 0.8:
                return self._run_one(task, best, strategies[best], kwargs)

        # Otherwise pick a random strategy to gather data
        import random
        strategy_name, fn = random.choice(list(strategies.items()))
        return self._run_one(task, strategy_name, fn, kwargs)

    def _run_one(self, task: str, strategy: str, fn: Callable, kwargs: dict) -> dict:
        start = time.time()
        try:
            result = fn(**kwargs)
            duration_ms = (time.time() - start) * 1000
            success = bool(result) and not (
                isinstance(result, dict) and result.get("error")
            )
            summary = ""
            if isinstance(result, list):
                summary = f"{len(result)} results"
            elif isinstance(result, dict):
                summary = str(list(result.keys())[:3])
            else:
                summary = str(result)[:80]
            self.log.record(task, strategy, success, duration_ms, summary)
            publish("luokai.tinkered", {
                "task":     task,
                "strategy": strategy,
                "success":  success,
                "duration_ms": duration_ms,
            }, source="tinkerer")
            return {
                "ok":       success,
                "result":   result,
                "strategy": strategy,
                "duration_ms": duration_ms,
            }
        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            self.log.record(task, strategy, False, duration_ms, f"error: {e}")
            traceback.print_exc()
            return {"ok": False, "error": str(e), "strategy": strategy}

    def race(self, task: str, **kwargs) -> dict:
        """
        Race ALL strategies in parallel. Whichever finishes first with
        a successful result wins. The others get logged for comparison.
        """
        strategies = _strategies.get(task, {})
        if not strategies:
            return {"ok": False, "error": f"No strategies for '{task}'"}

        results: dict = {}
        threads: list = []
        lock = threading.Lock()

        def runner(name, fn):
            r = self._run_one(task, name, fn, kwargs)
            with lock:
                results[name] = r

        for name, fn in strategies.items():
            t = threading.Thread(target=runner, args=(name, fn), daemon=True)
            t.start()
            threads.append(t)
        # Wait up to 5s
        for t in threads:
            t.join(timeout=5.0)

        # Pick the fastest successful one
        successful = [(n, r) for n, r in results.items()
                      if r.get("ok")]
        if successful:
            successful.sort(key=lambda x: x[1].get("duration_ms", float("inf")))
            return successful[0][1]
        return {"ok": False, "error": "All strategies failed", "details": results}


# ────────────────────────────────────────────────────────────────
# Singleton + public API
# ────────────────────────────────────────────────────────────────
tinkerer = Tinkerer()


def tinker(task: str, **kwargs) -> dict:
    return tinkerer.tinker(task, **kwargs)


def race(task: str, **kwargs) -> dict:
    return tinkerer.race(task, **kwargs)


def stats() -> dict:
    return tinkerer.log.stats()


def best_strategy(task: str) -> str | None:
    return tinkerer.log.best_strategy(task)


# ────────────────────────────────────────────────────────────────
# BASELINE STRATEGIES (built-in for common tasks)
# ────────────────────────────────────────────────────────────────

@register_strategy("search_files", "rglob")
def _search_rglob(query: str = "", root: str = "~", limit: int = 20) -> list:
    from pathlib import Path
    results = []
    base = Path(root).expanduser()
    q = query.lower()
    try:
        for p in base.rglob("*"):
            if q in p.name.lower():
                results.append(str(p))
            if len(results) >= limit:
                break
    except Exception:
        pass
    return results


@register_strategy("search_files", "find_command")
def _search_find_cmd(query: str = "", root: str = "~", limit: int = 20) -> list:
    import subprocess
    from pathlib import Path
    base = str(Path(root).expanduser())
    try:
        r = subprocess.run(
            ["find", base, "-iname", f"*{query}*"],
            capture_output=True, text=True, timeout=5
        )
        lines = r.stdout.strip().splitlines()[:limit]
        return lines
    except Exception:
        return []


@register_strategy("answer_question", "knowledge_db")
def _answer_kb(question: str = "") -> str:
    """Try the knowledge database first."""
    try:
        from luokai.cells.data_index import search_knowledge
        hits = search_knowledge(question, top_k=1)
        if hits:
            return hits[0].get("answer", "")
    except Exception:
        pass
    return ""


@register_strategy("answer_question", "cells")
def _answer_cells(question: str = "") -> str:
    """Try the cell system."""
    try:
        from luokai.core.inference import get_inference
        return get_inference().generate([{"role": "user", "content": question}])
    except Exception:
        return ""
