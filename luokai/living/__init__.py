"""
LuoOS Living Substrate
───────────────────────
The always-on cognitive layer that makes LUOKAI feel alive.

  event_bus      — system-wide pub/sub channel
  working_memory — structured live state of what's happening
  observer       — fills memory by subscribing to events
  daemon         — the 24/7 cognitive loop

Usage from anywhere in LuoOS:

    from luokai.living import bus, memory, daemon

    # Publish an event when anything happens
    bus.publish("file.opened", {"path": "/home/u/x.txt"})

    # LUOKAI's current understanding of what's happening
    context = memory.to_context_string()
    # → "User is currently in: vscode\nCurrent task: coding\n..."

    # Start the daemon (already auto-started by luo_server.py)
    daemon.start()
"""
from .event_bus      import bus, publish, subscribe, history, Event
from .working_memory import memory, snapshot, context_string
from .observer       import install as install_observer
from .daemon         import daemon, start as start_daemon, stop as stop_daemon, status as daemon_status

__all__ = [
    "bus", "publish", "subscribe", "history", "Event",
    "memory", "snapshot", "context_string",
    "install_observer",
    "daemon", "start_daemon", "stop_daemon", "daemon_status",
]
