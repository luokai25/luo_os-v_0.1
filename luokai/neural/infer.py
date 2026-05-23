"""
LUOKAI Neural Brain — Inference Wrapper
─────────────────────────────────────────
Clean API for generating text from the trained brain.

The brain is OPTIONAL. If no trained weights exist, is_ready is False
and LuoOS falls back to the cell system / knowledge DB / routing engine.
Once a brain is trained (via train.py), this wrapper loads it and
provides fluent generation.

Usage:
    from luokai.neural.infer import NeuralBrain

    nb = NeuralBrain()
    if nb.is_ready:
        reply = nb.respond("hello")
        # → "Hello! I'm LUOKAI..."
"""
import re
from pathlib import Path

from .brain import LuokaiBrain, CharTokenizer, WEIGHTS_PATH, VOCAB_PATH


class NeuralBrain:
    """Loads the trained brain (if it exists) and generates responses."""

    def __init__(self, weights_path: Path = WEIGHTS_PATH,
                 vocab_path: Path = VOCAB_PATH):
        self.brain: LuokaiBrain | None = None
        self.tok:   CharTokenizer | None = None
        # Prefer trained weights in ~/.luo_os; fall back to repo-bundled brain
        repo_brain = Path(__file__).parent / "luokai_brain.npz"
        repo_vocab = Path(__file__).parent / "vocab.json"
        if not weights_path.exists() and repo_brain.exists():
            weights_path = repo_brain
        if not vocab_path.exists() and repo_vocab.exists():
            vocab_path = repo_vocab
        self._load(weights_path, vocab_path)

    def _load(self, weights_path: Path, vocab_path: Path):
        try:
            if weights_path.exists() and vocab_path.exists():
                self.brain = LuokaiBrain.load(weights_path)
                self.tok   = CharTokenizer.load(vocab_path)
        except Exception as e:
            print(f"[NeuralBrain] Load failed: {e}")
            self.brain = None
            self.tok   = None

    @property
    def is_ready(self) -> bool:
        """True only if a trained brain with enough steps is loaded."""
        return (self.brain is not None
                and self.tok is not None
                and self.brain.steps >= 1000)   # untrained brains are not used

    def respond(self, user_msg: str, max_new: int = 120,
                temperature: float = 0.7, top_k: int = 30) -> str | None:
        """Generate a LUOKAI response to a user message."""
        if not self.is_ready:
            return None
        prompt = f"<user>{user_msg.strip()}</user><luokai>"
        ids    = self.tok.encode(prompt)
        # Keep the prompt itself within the context window
        max_prompt = self.brain.ctx_len - 8
        if len(ids) > max_prompt:
            ids = ids[-max_prompt:]
        # Cap generation so prompt + new stays within ctx during sliding window
        out_ids = self.brain.generate(ids, max_new=max_new,
                                       temperature=temperature, top_k=top_k)
        full = self.tok.decode(out_ids)
        # Extract just the LUOKAI part
        reply = full[len(prompt):]
        # Stop at the closing tag or the next <user>
        for stop in ("</luokai>", "<user>", "\n<"):
            idx = reply.find(stop)
            if idx != -1:
                reply = reply[:idx]
        return reply.strip()

    def stats(self) -> dict:
        if self.brain is None:
            return {"ready": False, "reason": "no trained weights"}
        s = self.brain.stats()
        s["ready"] = self.is_ready
        if not self.is_ready:
            s["reason"] = f"only {self.brain.steps} steps (need 1000+)"
        return s

    def reload(self):
        """Re-load weights from disk (after a fresh training run)."""
        self._load(WEIGHTS_PATH, VOCAB_PATH)


# ── Module-level singleton ────────────────────────────────────────────
_neural: NeuralBrain | None = None


def get_neural() -> NeuralBrain:
    global _neural
    if _neural is None:
        _neural = NeuralBrain()
    return _neural
