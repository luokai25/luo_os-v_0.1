"""
LuoOS Critic
─────────────
Once a day, LUOKAI evaluates HIS OWN PERFORMANCE.

The critic answers: am I getting better at helping this user?

Metrics:
  - Prediction accuracy this week vs last week
  - Tinkerer experiment win rates
  - Total events processed (engagement)
  - Average response time
  - Tasks where LUOKAI is improving vs degrading

This is the meta-loop that prevents the system from spiralling into
confident hallucination. Without measurable success signals, a
self-improvement loop just reinforces noise. With the critic,
LUOKAI can detect when he's getting WORSE and roll back.
"""
import time
import json
from pathlib import Path

from .event_bus  import publish
from .verifier   import verifier, get_accuracy
from .tinkerer   import tinkerer
from .predictor  import predictor


SELF_EVAL_PATH = Path.home() / ".luo_os" / "self_eval.json"


class Critic:
    """LUOKAI's self-evaluator."""

    def __init__(self, path: Path = SELF_EVAL_PATH):
        self.path = path
        self.evals: list = []
        self.load()

    def load(self):
        try:
            if self.path.exists():
                self.evals = json.loads(self.path.read_text())
        except Exception:
            self.evals = []

    def save(self):
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            # Keep last 90 days of evaluations
            self.evals = self.evals[-90:]
            self.path.write_text(json.dumps(self.evals, indent=2))
        except Exception:
            pass

    # ── the daily self-evaluation ──────────────────────────────
    def evaluate(self) -> dict:
        """Run a self-evaluation cycle. Returns the report."""
        now = time.time()
        # Look at last 24 hours and last 7 days
        last_24h = get_accuracy(since_seconds=86400)
        last_7d  = get_accuracy(since_seconds=86400 * 7)
        all_time = get_accuracy()
        tinkerer_stats = tinkerer.log.stats()
        pattern_stats  = predictor.patterns.stats()

        # Detect trend: is accuracy improving?
        trend = "stable"
        if last_24h["total"] >= 5 and last_7d["total"] >= 10:
            if last_24h["accuracy"] > last_7d["accuracy"] + 0.05:
                trend = "improving"
            elif last_24h["accuracy"] < last_7d["accuracy"] - 0.05:
                trend = "degrading"

        # Find best and worst strategies across tinkerer history
        strategy_summary: list = []
        for task, strategies in tinkerer.log.scores.items():
            for name, stats in strategies.items():
                runs = stats["runs"]
                if runs >= 3:
                    win_rate = stats["wins"] / runs
                    avg_ms   = stats["total_ms"] / runs
                    strategy_summary.append({
                        "task":     task,
                        "strategy": name,
                        "win_rate": win_rate,
                        "avg_ms":   round(avg_ms, 1),
                        "runs":     runs,
                    })
        strategy_summary.sort(key=lambda x: -x["win_rate"])

        report = {
            "ts":        now,
            "iso":       time.strftime("%Y-%m-%d %H:%M", time.localtime(now)),
            "accuracy_24h":  last_24h,
            "accuracy_7d":   last_7d,
            "accuracy_all":  all_time,
            "trend":         trend,
            "patterns":      pattern_stats,
            "tinkerer":      tinkerer_stats,
            "best_strategies":  strategy_summary[:5],
            "worst_strategies": strategy_summary[-5:] if len(strategy_summary) >= 5 else [],
        }

        self.evals.append(report)
        self.save()

        # Publish — UI can show this
        publish("luokai.self_eval", report, source="critic")
        return report

    def latest(self) -> dict | None:
        return self.evals[-1] if self.evals else None

    def history(self, n: int = 7) -> list:
        return self.evals[-n:]


# Singleton
critic = Critic()


def evaluate() -> dict:
    return critic.evaluate()


def latest() -> dict | None:
    return critic.latest()


def history(n: int = 7) -> list:
    return critic.history(n)
