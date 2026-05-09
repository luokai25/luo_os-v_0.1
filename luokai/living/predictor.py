"""
LuoOS Predictor
────────────────
Watches events. After each significant event, predicts what the user
will do next. Predictions are stored with confidence scores and
checked later by the verifier.

The predictor's job is NOT to be right. It's to make falsifiable
guesses. The verifier scores them. Right guesses become patterns
LUOKAI uses. Wrong guesses get pruned.

Phase 2: rule-based predictor with frequency learning.
Phase 3 (later): trained on the user's actual event log.
"""
import time
import json
import threading
from collections import defaultdict, Counter
from pathlib import Path

from .event_bus      import bus, Event, publish
from .working_memory import memory


# ────────────────────────────────────────────────────────────────
# Pattern Memory — what LUOKAI has learned
# ────────────────────────────────────────────────────────────────
PATTERNS_PATH = Path.home() / ".luo_os" / "patterns.json"


class PatternMemory:
    """
    Learned patterns of user behaviour.
    Each pattern is: trigger → predicted_action with weight.

    Example:
      ("app.opened", "browser") → ("file.opened", "*.py")  weight=0.8
      meaning: when user opens browser, they often open a Python file next.
    """

    def __init__(self, path: Path = PATTERNS_PATH):
        self.path = path
        self.patterns: dict = {}
        self.load()

    def load(self):
        try:
            if self.path.exists():
                self.patterns = json.loads(self.path.read_text())
        except Exception:
            self.patterns = {}

    def save(self):
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps(self.patterns, indent=2))
        except Exception:
            pass

    def key(self, trigger_type: str, trigger_subject: str = "") -> str:
        return f"{trigger_type}::{trigger_subject}"

    def reinforce(self, trigger: str, predicted: str, by: float = 0.1):
        """Strengthen a pattern. Successful predictions become more confident."""
        bucket = self.patterns.setdefault(trigger, {})
        bucket[predicted] = min(1.0, bucket.get(predicted, 0.5) + by)
        self.save()

    def weaken(self, trigger: str, predicted: str, by: float = 0.05):
        """Weaken a pattern. Wrong predictions decay."""
        bucket = self.patterns.setdefault(trigger, {})
        bucket[predicted] = max(0.0, bucket.get(predicted, 0.5) - by)
        if bucket[predicted] < 0.1:
            bucket.pop(predicted, None)
        self.save()

    def predict(self, trigger: str, top_k: int = 3) -> list[tuple[str, float]]:
        """Return top-k predicted next actions for a trigger."""
        bucket = self.patterns.get(trigger, {})
        if not bucket:
            return []
        ranked = sorted(bucket.items(), key=lambda x: x[1], reverse=True)
        return ranked[:top_k]

    def stats(self) -> dict:
        total = sum(len(v) for v in self.patterns.values())
        return {
            "total_triggers": len(self.patterns),
            "total_patterns": total,
        }


# ────────────────────────────────────────────────────────────────
# Predictor
# ────────────────────────────────────────────────────────────────
class Predictor:
    """Generates predictions on each significant event."""

    def __init__(self):
        self.patterns          = PatternMemory()
        self.pending           = {}          # event_id → prediction
        self._lock             = threading.Lock()
        # Hard-coded baseline patterns to bootstrap on a fresh install
        self._bootstrap()

    def _bootstrap(self):
        """Seed common-sense patterns so a brand-new user gets useful predictions."""
        if self.patterns.patterns:
            return  # already have learned patterns
        baseline = {
            "app.opened::browser":  {"file.opened::*": 0.5},
            "app.opened::vscode":   {"file.opened::*.py": 0.7},
            "app.opened::files":    {"file.opened::*": 0.6},
            "app.opened::terminal": {"command.run::*": 0.8},
            "app.opened::notes":    {"note.updated::*": 0.6},
            "file.opened::*.py":    {"app.opened::terminal": 0.5},
            "chat.user_msg::error": {"app.opened::vscode": 0.5,
                                     "app.opened::terminal": 0.4},
            "chat.user_msg::email": {"app.opened::browser": 0.7},
            "chat.user_msg::find":  {"app.opened::files": 0.6},
        }
        self.patterns.patterns = baseline
        self.patterns.save()

    # ── prediction trigger ────────────────────────────────────
    def on_event(self, e: Event):
        """Called for every event. Decides whether to predict."""
        # Build trigger key (event_type + subject)
        subject = self._extract_subject(e)
        trigger = self.patterns.key(e.type, subject)

        # Look up predictions
        candidates = self.patterns.predict(trigger, top_k=3)
        if not candidates:
            # Try wildcard subject
            wildcard_trigger = self.patterns.key(e.type, "*")
            candidates = self.patterns.predict(wildcard_trigger, top_k=3)
        if not candidates:
            return

        # Take the top prediction with confidence > 0.4
        top_predicted, confidence = candidates[0]
        if confidence < 0.3:
            return

        prediction = {
            "trigger":    trigger,
            "predicted":  top_predicted,
            "confidence": confidence,
            "ts":         time.time(),
            "verified":   False,
        }
        # Stash so verifier can find it
        with self._lock:
            self.pending[id(e)] = prediction

        # Publish the prediction
        publish("luokai.predicted", {
            "trigger":    trigger,
            "predicted":  top_predicted,
            "confidence": confidence,
        }, source="predictor")

    def _extract_subject(self, e: Event) -> str:
        """Extract a short subject from an event for pattern matching."""
        if e.type.startswith("app."):
            return e.data.get("app", "") or e.data.get("id", "")
        if e.type.startswith("file."):
            path = e.data.get("path", "")
            # Reduce to extension pattern
            if "." in path:
                ext = path.rsplit(".", 1)[1].lower()
                return f"*.{ext}"
            return "*"
        if e.type == "chat.user_msg":
            text = (e.data.get("text", "") or "").lower()
            # Pick the most semantic keyword
            for kw in ["error", "debug", "email", "find", "schedule",
                       "meeting", "summary", "explain", "code", "search"]:
                if kw in text:
                    return kw
            return "general"
        return e.data.get("subject", "")

    # ── recent predictions ────────────────────────────────────
    def get_pending(self) -> list[dict]:
        with self._lock:
            return list(self.pending.values())

    def clear_old(self, older_than_seconds: float = 300):
        """Remove pending predictions older than 5 min — they're stale."""
        cutoff = time.time() - older_than_seconds
        with self._lock:
            self.pending = {
                k: v for k, v in self.pending.items()
                if v["ts"] >= cutoff
            }


# ────────────────────────────────────────────────────────────────
# Singleton + bus subscription
# ────────────────────────────────────────────────────────────────
predictor = Predictor()


@bus.subscribe("app.*")
@bus.subscribe("file.*")
@bus.subscribe("chat.user_msg")
def _on_significant_event(e: Event):
    predictor.on_event(e)


def get_pending_predictions():
    return predictor.get_pending()


def get_pattern_stats():
    return predictor.patterns.stats()
