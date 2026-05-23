"""
LUOKAI Neural Brain
────────────────────
A pure-NumPy character-level transformer with analytical backprop.
No PyTorch, no TensorFlow — runs anywhere Python + NumPy run.

This is LUOKAI's optional learned brain. The cell system, knowledge DB,
and the routing engine handle most queries; this brain is for fluent
free-form generation once trained.

Architecture (configurable, defaults are CPU-trainable):
  - Token embedding + learned positional embedding
  - N transformer blocks (multi-head self-attention + MLP)
  - Pre-LayerNorm, residual connections
  - Tied output projection
  - Adam optimizer with warmup + analytical gradients

Lineage: KAI Agent v22's kai_neural.py. Same design, brought into LuoOS.

HONEST NOTE: training a usable model needs many thousands of steps.
On 1 CPU core that is hours. The train.py script checkpoints so you can
run it incrementally, or run it on a GPU box / Colab. The forward pass
for inference is fast enough for real-time generation once trained.
"""
import json
import math
import pickle
import time
from pathlib import Path

import numpy as np


# ──────────────────────────────────────────────────────────────────────
# Configuration — defaults sized to train on a single CPU core
# ──────────────────────────────────────────────────────────────────────
N_LAYERS   = 4        # transformer blocks
N_HEADS    = 8        # attention heads
D_MODEL    = 256      # embedding / hidden dimension
D_FF       = 512      # feed-forward inner dimension
CTX_LEN    = 128      # context window (characters)
DROPOUT    = 0.0      # kept 0 for deterministic CPU training
WARMUP     = 100      # LR warmup steps
LR         = 3e-4     # peak learning rate
BETA1      = 0.9
BETA2      = 0.95
EPS        = 1e-8
WEIGHT_DECAY = 0.01

MODEL_DIR    = Path.home() / ".luo_os" / "neural"
WEIGHTS_PATH = MODEL_DIR / "luokai_brain.npz"
VOCAB_PATH   = MODEL_DIR / "vocab.json"


# ──────────────────────────────────────────────────────────────────────
# Tokenizer — character-level
# ──────────────────────────────────────────────────────────────────────
class CharTokenizer:
    """Simple, robust character-level tokenizer."""

    def __init__(self, vocab: list[str] | None = None):
        # Default vocab: printable ASCII + newline + tab + common punctuation
        if vocab is None:
            chars = ["\n", "\t"] + [chr(i) for i in range(32, 127)]
            vocab = chars
        self.vocab    = vocab
        self.stoi     = {c: i for i, c in enumerate(vocab)}
        self.itos     = {i: c for i, c in enumerate(vocab)}
        self.unk      = 0  # newline used as fallback

    @property
    def size(self) -> int:
        return len(self.vocab)

    def encode(self, text: str) -> list[int]:
        return [self.stoi.get(c, self.unk) for c in text]

    def decode(self, ids: list[int]) -> str:
        return "".join(self.itos.get(int(i), "") for i in ids)

    def save(self, path: Path = VOCAB_PATH):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"vocab": self.vocab}, ensure_ascii=False))

    @classmethod
    def load(cls, path: Path = VOCAB_PATH) -> "CharTokenizer":
        if path.exists():
            data = json.loads(path.read_text())
            return cls(vocab=data["vocab"])
        return cls()

    @classmethod
    def from_corpus(cls, text: str) -> "CharTokenizer":
        """Build a vocab from the unique chars in a corpus."""
        chars = sorted(set(text))
        # Always include newline/tab
        for c in ("\n", "\t"):
            if c not in chars:
                chars.insert(0, c)
        return cls(vocab=chars)


# ──────────────────────────────────────────────────────────────────────
# Math helpers
# ──────────────────────────────────────────────────────────────────────
def softmax(x, axis=-1):
    x = x - np.max(x, axis=axis, keepdims=True)
    e = np.exp(x)
    return e / np.sum(e, axis=axis, keepdims=True)


def layernorm(x, gamma, beta, eps=1e-5):
    mu  = np.mean(x, axis=-1, keepdims=True)
    var = np.var(x, axis=-1, keepdims=True)
    xn  = (x - mu) / np.sqrt(var + eps)
    return gamma * xn + beta, (xn, mu, var)


def layernorm_backward(dout, cache, gamma, eps=1e-5):
    xn, mu, var = cache
    N      = xn.shape[-1]
    dgamma = np.sum(dout * xn, axis=tuple(range(dout.ndim - 1)))
    dbeta  = np.sum(dout, axis=tuple(range(dout.ndim - 1)))
    dxn    = dout * gamma
    istd   = 1.0 / np.sqrt(var + eps)
    dx = (1.0 / N) * istd * (
        N * dxn
        - np.sum(dxn, axis=-1, keepdims=True)
        - xn * np.sum(dxn * xn, axis=-1, keepdims=True)
    )
    return dx, dgamma, dbeta


def gelu(x):
    return 0.5 * x * (1.0 + np.tanh(np.sqrt(2.0 / np.pi) * (x + 0.044715 * x**3)))


def gelu_backward(x):
    c   = np.sqrt(2.0 / np.pi)
    t   = np.tanh(c * (x + 0.044715 * x**3))
    dt  = c * (1 + 3 * 0.044715 * x**2)
    return 0.5 * (1 + t) + 0.5 * x * (1 - t**2) * dt


# ──────────────────────────────────────────────────────────────────────
# The Brain
# ──────────────────────────────────────────────────────────────────────
class LuokaiBrain:
    """Pure-NumPy transformer language model."""

    def __init__(self, vocab_size: int,
                 n_layers: int = N_LAYERS, n_heads: int = N_HEADS,
                 d_model: int = D_MODEL, d_ff: int = D_FF,
                 ctx_len: int = CTX_LEN, seed: int = 42):
        self.vocab_size = vocab_size
        self.n_layers   = n_layers
        self.n_heads    = n_heads
        self.d_model    = d_model
        self.d_ff       = d_ff
        self.ctx_len    = ctx_len
        self.d_head     = d_model // n_heads
        assert d_model % n_heads == 0, "d_model must divide n_heads"

        rng = np.random.default_rng(seed)
        scale = 0.02
        self.P: dict[str, np.ndarray] = {}

        # Embeddings
        self.P["tok_emb"] = rng.normal(0, scale, (vocab_size, d_model))
        self.P["pos_emb"] = rng.normal(0, scale, (ctx_len, d_model))

        # Transformer blocks
        for L in range(n_layers):
            self.P[f"ln1_g{L}"] = np.ones(d_model)
            self.P[f"ln1_b{L}"] = np.zeros(d_model)
            self.P[f"Wq{L}"]    = rng.normal(0, scale, (d_model, d_model))
            self.P[f"Wk{L}"]    = rng.normal(0, scale, (d_model, d_model))
            self.P[f"Wv{L}"]    = rng.normal(0, scale, (d_model, d_model))
            self.P[f"Wo{L}"]    = rng.normal(0, scale, (d_model, d_model))
            self.P[f"ln2_g{L}"] = np.ones(d_model)
            self.P[f"ln2_b{L}"] = np.zeros(d_model)
            self.P[f"W1_{L}"]   = rng.normal(0, scale, (d_model, d_ff))
            self.P[f"b1_{L}"]   = np.zeros(d_ff)
            self.P[f"W2_{L}"]   = rng.normal(0, scale, (d_ff, d_model))
            self.P[f"b2_{L}"]   = np.zeros(d_model)

        # Final layernorm
        self.P["lnf_g"] = np.ones(d_model)
        self.P["lnf_b"] = np.zeros(d_model)

        # Adam state
        self.m = {k: np.zeros_like(v) for k, v in self.P.items()}
        self.v = {k: np.zeros_like(v) for k, v in self.P.items()}
        self.adam_t = 0
        self.steps  = 0
        self.loss_history: list[float] = []

        # Causal mask
        self._mask = np.triu(np.full((ctx_len, ctx_len), -1e9), k=1)

    # ── parameter count ──
    def n_params(self) -> int:
        return sum(p.size for p in self.P.values())

    # ── forward ──────────────────────────────────────────────────────
    def forward(self, ids: np.ndarray, cache: bool = False):
        """ids: (T,) integer array. Returns logits (T, vocab) + optional cache."""
        T = len(ids)
        x = self.P["tok_emb"][ids] + self.P["pos_emb"][:T]   # (T, d)
        caches = [] if cache else None

        for L in range(self.n_layers):
            # Attention sub-block
            xn, ln1c = layernorm(x, self.P[f"ln1_g{L}"], self.P[f"ln1_b{L}"])
            q = xn @ self.P[f"Wq{L}"]
            k = xn @ self.P[f"Wk{L}"]
            v = xn @ self.P[f"Wv{L}"]
            # Reshape to heads: (H, T, d_head)
            qh = q.reshape(T, self.n_heads, self.d_head).transpose(1, 0, 2)
            kh = k.reshape(T, self.n_heads, self.d_head).transpose(1, 0, 2)
            vh = v.reshape(T, self.n_heads, self.d_head).transpose(1, 0, 2)
            scores = (qh @ kh.transpose(0, 2, 1)) / math.sqrt(self.d_head)
            scores = scores + self._mask[:T, :T]
            attn   = softmax(scores, axis=-1)
            out_h  = attn @ vh                                  # (H, T, d_head)
            out    = out_h.transpose(1, 0, 2).reshape(T, self.d_model)
            attn_out = out @ self.P[f"Wo{L}"]
            x = x + attn_out                                    # residual

            # MLP sub-block
            xn2, ln2c = layernorm(x, self.P[f"ln2_g{L}"], self.P[f"ln2_b{L}"])
            h_pre = xn2 @ self.P[f"W1_{L}"] + self.P[f"b1_{L}"]
            h_act = gelu(h_pre)
            mlp_out = h_act @ self.P[f"W2_{L}"] + self.P[f"b2_{L}"]
            x = x + mlp_out                                     # residual

            if cache:
                caches.append({
                    "xn": xn, "ln1c": ln1c, "q": q, "k": k, "v": v,
                    "qh": qh, "kh": kh, "vh": vh, "attn": attn,
                    "out": out, "xn2": xn2, "ln2c": ln2c,
                    "h_pre": h_pre, "h_act": h_act,
                })

        xf, lnfc = layernorm(x, self.P["lnf_g"], self.P["lnf_b"])
        logits = xf @ self.P["tok_emb"].T                       # tied weights
        if cache:
            return logits, {"caches": caches, "lnfc": lnfc, "xf": xf,
                            "ids": ids, "x_final": x}
        return logits

    # ── loss + backward (analytical) ─────────────────────────────────
    def loss_and_grad(self, ids: np.ndarray, targets: np.ndarray):
        """Cross-entropy loss + gradients. ids/targets: (T,)."""
        T = len(ids)
        logits, fc = self.forward(ids, cache=True)
        probs = softmax(logits, axis=-1)
        # Cross-entropy
        eps = 1e-9
        loss = -np.mean(np.log(probs[np.arange(T), targets] + eps))

        # ── backprop ──
        G = {k: np.zeros_like(v) for k, v in self.P.items()}

        # dlogits
        dlogits = probs.copy()
        dlogits[np.arange(T), targets] -= 1.0
        dlogits /= T

        # logits = xf @ tok_emb.T
        G["tok_emb"] += dlogits.T @ fc["xf"]
        dxf = dlogits @ self.P["tok_emb"]

        # final layernorm
        dx, dg, db = layernorm_backward(dxf, fc["lnfc"], self.P["lnf_g"])
        G["lnf_g"] += dg
        G["lnf_b"] += db

        # transformer blocks (reverse)
        for L in reversed(range(self.n_layers)):
            c = fc["caches"][L]
            # MLP residual: x = x + mlp_out
            d_mlp = dx
            # mlp_out = h_act @ W2 + b2
            G[f"W2_{L}"] += c["h_act"].T @ d_mlp
            G[f"b2_{L}"] += np.sum(d_mlp, axis=0)
            d_hact = d_mlp @ self.P[f"W2_{L}"].T
            # h_act = gelu(h_pre)
            d_hpre = d_hact * gelu_backward(c["h_pre"])
            # h_pre = xn2 @ W1 + b1
            G[f"W1_{L}"] += c["xn2"].T @ d_hpre
            G[f"b1_{L}"] += np.sum(d_hpre, axis=0)
            d_xn2 = d_hpre @ self.P[f"W1_{L}"].T
            # layernorm 2
            d_x_ln2, dg2, db2 = layernorm_backward(d_xn2, c["ln2c"], self.P[f"ln2_g{L}"])
            G[f"ln2_g{L}"] += dg2
            G[f"ln2_b{L}"] += db2
            dx = dx + d_x_ln2   # residual path

            # Attention residual: x = x + attn_out
            d_attn_out = dx
            # attn_out = out @ Wo
            G[f"Wo{L}"] += c["out"].T @ d_attn_out
            d_out = d_attn_out @ self.P[f"Wo{L}"].T
            # out reshape from heads
            d_out_h = d_out.reshape(T, self.n_heads, self.d_head).transpose(1, 0, 2)
            # out_h = attn @ vh
            d_attn = d_out_h @ c["vh"].transpose(0, 2, 1)
            d_vh   = c["attn"].transpose(0, 2, 1) @ d_out_h
            # softmax backward
            d_scores = c["attn"] * (d_attn - np.sum(d_attn * c["attn"], axis=-1, keepdims=True))
            # scores = qh @ kh^T / sqrt(d_head)
            scale = 1.0 / math.sqrt(self.d_head)
            d_qh = (d_scores @ c["kh"]) * scale
            d_kh = (d_scores.transpose(0, 2, 1) @ c["qh"]) * scale
            # merge heads back
            d_q = d_qh.transpose(1, 0, 2).reshape(T, self.d_model)
            d_k = d_kh.transpose(1, 0, 2).reshape(T, self.d_model)
            d_v = d_vh.transpose(1, 0, 2).reshape(T, self.d_model)
            # q = xn @ Wq, etc.
            G[f"Wq{L}"] += c["xn"].T @ d_q
            G[f"Wk{L}"] += c["xn"].T @ d_k
            G[f"Wv{L}"] += c["xn"].T @ d_v
            d_xn = d_q @ self.P[f"Wq{L}"].T + d_k @ self.P[f"Wk{L}"].T + d_v @ self.P[f"Wv{L}"].T
            # layernorm 1
            d_x_ln1, dg1, db1 = layernorm_backward(d_xn, c["ln1c"], self.P[f"ln1_g{L}"])
            G[f"ln1_g{L}"] += dg1
            G[f"ln1_b{L}"] += db1
            dx = dx + d_x_ln1   # residual path

        # embeddings
        ids_arr = fc["ids"]
        np.add.at(G["tok_emb"], ids_arr, dx)
        G["pos_emb"][:T] += dx

        return loss, G

    # ── Adam step ────────────────────────────────────────────────────
    def adam_step(self, G: dict, lr_scale: float = 1.0):
        self.adam_t += 1
        t  = self.adam_t
        lr = LR * lr_scale
        for k in self.P:
            g = G[k]
            self.m[k] = BETA1 * self.m[k] + (1 - BETA1) * g
            self.v[k] = BETA2 * self.v[k] + (1 - BETA2) * (g * g)
            mhat = self.m[k] / (1 - BETA1**t)
            vhat = self.v[k] / (1 - BETA2**t)
            update = mhat / (np.sqrt(vhat) + EPS)
            # Decoupled weight decay (AdamW) — skip for norms/biases
            if k.startswith(("W", "tok_emb", "pos_emb")):
                update += WEIGHT_DECAY * self.P[k]
            self.P[k] -= lr * update

    # ── training step ────────────────────────────────────────────────
    def train_step(self, ids: np.ndarray, targets: np.ndarray) -> float:
        # LR warmup
        lr_scale = min(1.0, (self.adam_t + 1) / WARMUP)
        loss, G  = self.loss_and_grad(ids, targets)
        # Gradient clipping
        total_norm = math.sqrt(sum(np.sum(g * g) for g in G.values()))
        clip = 1.0
        if total_norm > clip:
            scale = clip / (total_norm + 1e-6)
            for k in G:
                G[k] *= scale
        self.adam_step(G, lr_scale=lr_scale)
        self.steps += 1
        self.loss_history.append(float(loss))
        self.loss_history = self.loss_history[-1000:]
        return float(loss)

    # ── generation ───────────────────────────────────────────────────
    def generate(self, prompt_ids: list[int], max_new: int = 100,
                 temperature: float = 0.8, top_k: int = 40) -> list[int]:
        ids = list(prompt_ids)
        for _ in range(max_new):
            ctx = ids[-self.ctx_len:]
            logits = self.forward(np.array(ctx, dtype=np.int64))
            last = logits[-1] / max(temperature, 1e-6)
            # top-k filter
            if top_k and top_k < len(last):
                kth = np.partition(last, -top_k)[-top_k]
                last = np.where(last < kth, -1e9, last)
            probs = softmax(last)
            nxt = int(np.random.choice(len(probs), p=probs))
            ids.append(nxt)
        return ids

    # ── persistence ──────────────────────────────────────────────────
    def save(self, path: Path = WEIGHTS_PATH):
        path.parent.mkdir(parents=True, exist_ok=True)
        arrays = {f"P_{k}": v for k, v in self.P.items()}
        arrays.update({f"m_{k}": v for k, v in self.m.items()})
        arrays.update({f"v_{k}": v for k, v in self.v.items()})
        meta = np.array([self.adam_t, self.steps, self.vocab_size,
                         self.n_layers, self.n_heads, self.d_model,
                         self.d_ff, self.ctx_len], dtype=np.int64)
        arrays["__meta__"]    = meta
        arrays["__losshist__"] = np.array(self.loss_history[-500:], dtype=np.float32)
        np.savez_compressed(path, **arrays)

    def save_inference(self, path: Path):
        """Save ONLY the weights (no optimizer state) — small file for shipping."""
        path.parent.mkdir(parents=True, exist_ok=True)
        arrays = {f"P_{k}": v.astype(np.float32) for k, v in self.P.items()}
        meta = np.array([self.adam_t, self.steps, self.vocab_size,
                         self.n_layers, self.n_heads, self.d_model,
                         self.d_ff, self.ctx_len], dtype=np.int64)
        arrays["__meta__"]    = meta
        arrays["__losshist__"] = np.array(self.loss_history[-100:], dtype=np.float32)
        np.savez_compressed(path, **arrays)

    @classmethod
    def load(cls, path: Path = WEIGHTS_PATH) -> "LuokaiBrain | None":
        if not path.exists():
            return None
        data = np.load(path, allow_pickle=False)
        meta = data["__meta__"]
        (adam_t, steps, vocab_size, n_layers, n_heads,
         d_model, d_ff, ctx_len) = meta.tolist()
        brain = cls(vocab_size=vocab_size, n_layers=n_layers, n_heads=n_heads,
                    d_model=d_model, d_ff=d_ff, ctx_len=ctx_len)
        for k in list(brain.P.keys()):
            if f"P_{k}" in data:
                brain.P[k] = data[f"P_{k}"]
            if f"m_{k}" in data:
                brain.m[k] = data[f"m_{k}"]
            if f"v_{k}" in data:
                brain.v[k] = data[f"v_{k}"]
        brain.adam_t = int(adam_t)
        brain.steps  = int(steps)
        if "__losshist__" in data:
            brain.loss_history = data["__losshist__"].tolist()
        return brain

    # ── stats ────────────────────────────────────────────────────────
    def stats(self) -> dict:
        recent = self.loss_history[-50:]
        return {
            "n_params":   self.n_params(),
            "steps":      self.steps,
            "loss":       round(sum(recent) / len(recent), 4) if recent else None,
            "n_layers":   self.n_layers,
            "n_heads":    self.n_heads,
            "d_model":    self.d_model,
            "ctx_len":    self.ctx_len,
        }
