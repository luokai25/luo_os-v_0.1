"""
LUOKAI Neural Brain — Training Script
──────────────────────────────────────
Trains the NumPy transformer on a corpus, with checkpointing so you can
run it incrementally (each run resumes from the last checkpoint).

Usage:
    python -m luokai.neural.train                    # train 2000 steps
    python -m luokai.neural.train --steps 5000       # custom step count
    python -m luokai.neural.train --corpus my.txt    # custom corpus
    python -m luokai.neural.train --fresh            # ignore checkpoint, start over

HONEST NOTE ON COMPUTE:
  On 1 CPU core, the default 4-layer/256-dim model trains at roughly
  100-200ms/step. A usable model needs 20,000-50,000 steps. That is
  1-3 hours of wall time. The script checkpoints every 500 steps so you
  can stop and resume freely, or run it on a GPU box / Colab where it
  finishes in minutes.

  This script does NOT pretend to fully train in one short run. It does
  exactly as many steps as you ask, saves, and reports honestly.
"""
import argparse
import math
import sys
import time
from pathlib import Path

import numpy as np

from .brain import (
    LuokaiBrain, CharTokenizer,
    WEIGHTS_PATH, VOCAB_PATH, CTX_LEN,
    N_LAYERS, N_HEADS, D_MODEL, D_FF,
)


CORPUS_PATH = Path(__file__).parent / "corpus.txt"


def load_corpus(path: Path) -> str:
    if not path.exists():
        print(f"[train] Corpus not found: {path}")
        print("[train] Run corpus generation first or pass --corpus")
        sys.exit(1)
    return path.read_text(encoding="utf-8", errors="replace")


def train(steps: int = 2000, corpus_path: Path = CORPUS_PATH,
          fresh: bool = False, log_every: int = 100,
          ckpt_every: int = 500, seed: int = 42):
    np.random.seed(seed)

    print("=" * 60)
    print("  LUOKAI Neural Brain — Training")
    print("=" * 60)

    # ── Load or build corpus + tokenizer ──
    text = load_corpus(corpus_path)
    print(f"  Corpus: {len(text):,} chars from {corpus_path.name}")

    # ── Load or create brain ──
    brain = None
    if not fresh:
        brain = LuokaiBrain.load(WEIGHTS_PATH)
        if brain is not None:
            tok = CharTokenizer.load(VOCAB_PATH)
            print(f"  Resumed from checkpoint: {brain.steps:,} steps, "
                  f"loss {brain.stats()['loss']}")

    if brain is None:
        tok   = CharTokenizer.from_corpus(text)
        brain = LuokaiBrain(vocab_size=tok.size)
        tok.save(VOCAB_PATH)
        print(f"  Fresh brain: {brain.n_params():,} params, "
              f"vocab {tok.size}")

    print(f"  Architecture: {brain.n_layers}L / {brain.n_heads}H / "
          f"{brain.d_model}d / ctx {brain.ctx_len}")

    ids = np.array(tok.encode(text), dtype=np.int32)
    if len(ids) < brain.ctx_len + 2:
        print("[train] Corpus too small for context window.")
        sys.exit(1)
    print(f"  Tokens: {len(ids):,}")
    print()

    # ── Training loop ──
    print(f"  Training {steps:,} steps...")
    print("  " + "-" * 50)
    t0 = time.time()
    losses: list[float] = []

    for step in range(1, steps + 1):
        s = np.random.randint(0, len(ids) - brain.ctx_len - 1)
        chunk   = ids[s:s + brain.ctx_len + 1]
        loss    = brain.train_step(chunk[:-1].astype(np.int64),
                                    chunk[1:].astype(np.int64))
        losses.append(loss)

        if step % log_every == 0:
            recent  = sum(losses[-log_every:]) / log_every
            elapsed = time.time() - t0
            rate    = step / elapsed
            eta     = (steps - step) / rate
            print(f"  step {step:5d}/{steps}  loss {recent:.3f}  "
                  f"{rate:.1f} step/s  eta {eta:4.0f}s")

        if step % ckpt_every == 0:
            brain.save(WEIGHTS_PATH)
            print(f"    [checkpoint @ step {brain.steps:,}]")

    brain.save(WEIGHTS_PATH)
    elapsed = time.time() - t0

    print()
    print("  " + "=" * 50)
    print(f"  Training complete:")
    print(f"    Total time:    {elapsed:.0f}s")
    print(f"    Steps this run: {steps:,}")
    print(f"    Total steps:    {brain.steps:,}")
    if len(losses) >= 100:
        print(f"    First 50 avg:   {sum(losses[:50])/50:.3f}")
        print(f"    Last 50 avg:    {sum(losses[-50:])/50:.3f}")
    print(f"    Weights saved:  {WEIGHTS_PATH} "
          f"({WEIGHTS_PATH.stat().st_size/1024:.0f} KB)")

    # ── Sample generations ──
    print()
    print("  Sample generations:")
    for prompt in ["<user>hello</user><luokai>",
                   "<user>open my files</user><luokai>",
                   "<user>what can you do</user><luokai>"]:
        pids = tok.encode(prompt)
        gen  = brain.generate(pids, max_new=60, temperature=0.7, top_k=20)
        out  = tok.decode(gen)
        print(f"    {prompt!r}")
        print(f"      → {out[len(prompt):][:80]!r}")

    return brain


def main():
    ap = argparse.ArgumentParser(description="Train LUOKAI's neural brain")
    ap.add_argument("--steps",  type=int, default=2000)
    ap.add_argument("--corpus", type=str, default=str(CORPUS_PATH))
    ap.add_argument("--fresh",  action="store_true",
                    help="Ignore checkpoint, start from scratch")
    args = ap.parse_args()
    train(steps=args.steps, corpus_path=Path(args.corpus), fresh=args.fresh)


if __name__ == "__main__":
    main()
