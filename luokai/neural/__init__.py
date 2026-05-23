"""
LUOKAI Neural Brain
────────────────────
An optional, locally-trainable language model for LUOKAI.

  brain.py   — pure-NumPy transformer with analytical backprop
  train.py   — training loop with checkpointing (resume-friendly)
  corpus.py  — generates the training corpus
  infer.py   — clean inference wrapper

The brain is OPTIONAL. LuoOS works fully without it (cell system +
knowledge DB + routing engine). Once trained, the brain adds fluent
free-form generation.

To train:
    python -m luokai.neural.corpus              # build corpus.txt
    python -m luokai.neural.train --steps 5000  # train (resumes if checkpoint exists)

Training a usable brain needs ~20-50k steps. On CPU that is hours;
on a GPU/Colab it is minutes. The train script checkpoints every 500
steps so you can stop and resume freely.
"""
from .brain import LuokaiBrain, CharTokenizer
from .infer import NeuralBrain, get_neural

__all__ = ["LuokaiBrain", "CharTokenizer", "NeuralBrain", "get_neural"]
