"""
LuoOS Living Substrate
───────────────────────
The always-on cognitive layer that makes LUOKAI feel alive.

  event_bus      — system-wide pub/sub channel
  working_memory — structured live state of what is happening
  observer       — fills memory by subscribing to events
  daemon         — the 24/7 cognitive loop

Phase 2 (the loop):
  predictor      — predicts user's next action
  verifier       — scores predictions, learns patterns
  tinkerer       — runs background experiments
  critic         — daily self-evaluation
"""
from .event_bus      import bus, publish, subscribe, history, Event
from .working_memory import memory, snapshot, context_string
from .observer       import install as install_observer
from .daemon         import daemon, start as start_daemon, stop as stop_daemon, status as daemon_status

# Phase 2 loops
from .predictor import predictor, get_pending_predictions, get_pattern_stats
from .verifier  import verifier, get_accuracy
from .tinkerer  import tinker, race, register_strategy, best_strategy, stats as tinkerer_stats
from .critic    import evaluate as critic_evaluate, latest as critic_latest, history as critic_history

__all__ = [
    "bus", "publish", "subscribe", "history", "Event",
    "memory", "snapshot", "context_string",
    "install_observer",
    "daemon", "start_daemon", "stop_daemon", "daemon_status",
    "predictor", "get_pending_predictions", "get_pattern_stats",
    "verifier", "get_accuracy",
    "tinker", "race", "register_strategy", "best_strategy", "tinkerer_stats",
    "critic_evaluate", "critic_latest", "critic_history",
]
