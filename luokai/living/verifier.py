"""
LuoOS Verifier
───────────────
Watches what the user actually does, compares to predictions, scores
them. Right predictions reinforce patterns. Wrong predictions decay.

This is the LEARNING loop. Without the verifier the predictor would
just guess forever — with it, LUOKAI gets measurably better at
predicting the user's behaviour over time.
"""
import time
import threading
from collections import defaultdict
from pathlib import Path
import json

from .event_bus  import bus, Event, publish
from .predictor  import predictor


# ────────────────────────────────────────────────────────────────
# Verification log — for the critic to evaluate
# ────────────────────────────────────────────────────────────────
VERIFICATION_LOG = Path.home() / ".luo_os" / "verifications.json"


class VerificationLog:
    """Tracks every prediction outcome so we can measure improvement."""

    def __init__(self, path: Path = VERIFICATION_LOG):
        self.path = path
        self.records: list[dict] = []
        self.load()

    def load(self):
        try:
            if self.path.exists():
                self.records = json.loads(self.path.read_text())
        except Exception:
            self.records = []

    def save(self):
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            # Keep last 1000
            self.records = self.records[-1000:]
            self.path.write_text(json.dumps(self.records, indent=2))
        except Exception:
            pass

    def record(self, hit: bool, prediction: dict):
        self.records.append({
            "ts":         time.time(),
            "hit":        hit,
            "trigger":    prediction.get("trigger"),
            "predicted":  prediction.get("predicted"),
            "confidence": prediction.get("confidence"),
        })
        if len(self.records) % 10 == 0:
            self.save()

    def stats(self, since_seconds: float | None = None) -> dict:
        """Compute hit rate over a time window."""
        cutoff = time.time() - since_seconds if since_seconds else 0
        relevant = [r for r in self.records if r["ts"] >= cutoff] if since_seconds else self.records
        if not relevant:
            return {"total": 0, "hits": 0, "misses": 0, "accuracy": 0.0}
        hits = sum(1 for r in relevant if r["hit"])
        return {
            "total":    len(relevant),
            "hits":     hits,
            "misses":   len(relevant) - hits,
            "accuracy": hits / len(relevant) if relevant else 0,
        }


# ────────────────────────────────────────────────────────────────
# Verifier
# ────────────────────────────────────────────────────────────────
class Verifier:
    """Watches subsequent events to verify pending predictions."""

    def __init__(self):
        self.log    = VerificationLog()
        self._lock  = threading.Lock()

    def on_event(self, e: Event):
        """Each new event might verify a pending prediction."""
        # Build the actual outcome key in the same format predictor uses
        actual_subject = predictor._extract_subject(e)
        actual_key     = predictor.patterns.key(e.type, actual_subject)

        # Check pending predictions
        with self._lock:
            still_pending = {}
            for pid, pred in predictor.pending.items():
                # Skip if already verified or too old
                if pred.get("verified") or time.time() - pred["ts"] > 120:
                    continue
                # The predicted is in form "type::subject" — but we may have stored without subject for wildcards
                predicted = pred["predicted"]

                # Match: exact, or wildcard subject match
                hit = self._matches(predicted, actual_key)
                if hit:
                    pred["verified"] = True
                    pred["actual"]   = actual_key
                    self.log.record(True, pred)
                    predictor.patterns.reinforce(pred["trigger"], predicted, by=0.1)
                    publish("luokai.verified", {
                        "trigger":    pred["trigger"],
                        "predicted":  predicted,
                        "actual":     actual_key,
                        "hit":        True,
                        "confidence": pred["confidence"],
                    }, source="verifier")
                else:
                    still_pending[pid] = pred
            # Clear verified ones
            predictor.pending = still_pending

        # Periodic cleanup of stale predictions (count as misses)
        self._expire_stale()

    def _matches(self, predicted: str, actual: str) -> bool:
        """Check if a predicted action matches the actual action."""
        if predicted == actual:
            return True
        # Wildcard subject match: "file.opened::*" matches any file.opened
        if "::*" in predicted:
            base = predicted.split("::")[0]
            if actual.startswith(base + "::"):
                return True
        # Wildcard extension: "file.opened::*.py" matches "file.opened::*.py" only
        return False

    def _expire_stale(self):
        """Predictions older than 2 minutes are misses."""
        cutoff = time.time() - 120
        with self._lock:
            stale = []
            still_pending = {}
            for pid, pred in predictor.pending.items():
                if pred["ts"] < cutoff and not pred.get("verified"):
                    stale.append(pred)
                else:
                    still_pending[pid] = pred
            predictor.pending = still_pending
        for pred in stale:
            self.log.record(False, pred)
            predictor.patterns.weaken(pred["trigger"], pred["predicted"], by=0.05)
            publish("luokai.verified", {
                "trigger":    pred["trigger"],
                "predicted":  pred["predicted"],
                "hit":        False,
                "expired":    True,
            }, source="verifier")


# ────────────────────────────────────────────────────────────────
# Singleton + bus wiring
# ────────────────────────────────────────────────────────────────
verifier = Verifier()


@bus.subscribe("app.*")
@bus.subscribe("file.*")
@bus.subscribe("chat.user_msg")
def _on_event_for_verification(e: Event):
    verifier.on_event(e)


def get_accuracy(since_seconds: float | None = None) -> dict:
    return verifier.log.stats(since_seconds=since_seconds)
