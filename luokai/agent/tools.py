"""
LUOKAI Agentic Control
─────────────────────────
LUOKAI doesn't just answer — it ACTS.

Tool-calling protocol:
  1. User: "open my files and find tax docs"
  2. LUOKAI parses → emits structured action: {tool:"open_app", args:{app:"files"}}
  3. Server dispatches to UI via SSE
  4. UI executes, reports back
  5. LUOKAI plans next step

Tools registered:
  - open_app(app)       — opens any LuoOS app
  - search_files(query) — recursive file search
  - read_file(path)     — read file contents
  - write_file(path, content) — create/edit file
  - run_command(cmd)    — terminal execution
  - search_web(query)   — DuckDuckGo via Chromium
  - send_chat(msg)      — chat with LUOKAI
  - close_app(id)       — close window
  - notify(title, body) — show notification
  - read_news(category) — WorldMonitor feed

Each tool call has:
  - id (for tracking)
  - tool name
  - args dict
  - result (filled when complete)
"""
import json
import re
import time
import uuid
from pathlib import Path
from typing import Any, Callable

# ── TOOL REGISTRY ──────────────────────────────────────────────────
TOOLS = {
    "open_app": {
        "description": "Open an app in LuoOS (browser, files, terminal, notes, etc.)",
        "args": {"app": "string — app id (luokai/browser/files/terminal/notes/calendar/calculator/music/worldmonitor/blender/handtracking)"},
    },
    "close_app": {
        "description": "Close an open app window",
        "args": {"app": "string — app id"},
    },
    "search_files": {
        "description": "Search for files by name in user's home directory",
        "args": {"query": "string — search keyword"},
    },
    "read_file": {
        "description": "Read contents of a file",
        "args": {"path": "string — absolute or ~ path"},
    },
    "write_file": {
        "description": "Create or overwrite a file",
        "args": {"path": "string", "content": "string"},
    },
    "run_command": {
        "description": "Execute a shell command (bash) and return output",
        "args": {"command": "string"},
    },
    "search_web": {
        "description": "Search the web via Luo Browser",
        "args": {"query": "string"},
    },
    "open_url": {
        "description": "Open a URL in Luo Browser",
        "args": {"url": "string"},
    },
    "notify": {
        "description": "Show a notification toast",
        "args": {"title": "string", "body": "string", "type": "info|warn|error"},
    },
    "read_news": {
        "description": "Fetch latest news from WorldMonitor",
        "args": {"category": "top|tech|finance|defense|science|climate|health|space|us|middle_east"},
    },
    "create_note": {
        "description": "Create a note in the Notes app",
        "args": {"title": "string", "content": "string"},
    },
    "schedule_event": {
        "description": "Add an event to the Calendar",
        "args": {"date": "YYYY-M-D", "event": "string"},
    },
    "remember": {
        "description": "Save a fact to LUOKAI's long-term memory",
        "args": {"fact": "string"},
    },
    "recall": {
        "description": "Search LUOKAI's memory for context",
        "args": {"query": "string"},
    },
}


def get_tools_prompt() -> str:
    """System prompt fragment describing all available tools."""
    lines = ["You have access to these tools to control LuoOS:\n"]
    for name, spec in TOOLS.items():
        args = ", ".join(f"{k}: {v}" for k, v in spec["args"].items())
        lines.append(f"  {name}({args})")
        lines.append(f"    {spec['description']}")
    lines.append("\nTo call a tool, output JSON like:")
    lines.append('  <tool>{"tool": "open_app", "args": {"app": "files"}}</tool>')
    lines.append("\nYou can call multiple tools by emitting multiple <tool> blocks.")
    lines.append("After tool results return, decide if more tools are needed or give a final answer.")
    return "\n".join(lines)


# ── TOOL CALL PARSING ──────────────────────────────────────────────
TOOL_RE = re.compile(r"<tool>(.*?)</tool>", re.DOTALL)


def parse_tool_calls(text: str) -> list[dict]:
    """Extract tool calls from LUOKAI's response text."""
    calls = []
    for match in TOOL_RE.finditer(text):
        try:
            data = json.loads(match.group(1).strip())
            calls.append({
                "id": str(uuid.uuid4())[:8],
                "tool": data.get("tool", ""),
                "args": data.get("args", {}),
            })
        except json.JSONDecodeError:
            continue
    return calls


def strip_tool_calls(text: str) -> str:
    """Remove tool call blocks from text for display."""
    return TOOL_RE.sub("", text).strip()


# ── ACTION QUEUE ──────────────────────────────────────────────────
# Pending UI actions queued for the browser to fetch via SSE.
# Each entry is {id, tool, args, ts, status}.
_pending_actions: list[dict] = []
_completed_actions: dict = {}  # id → result


def queue_action(tool: str, args: dict) -> str:
    """Queue an action for the UI to execute. Returns action ID."""
    aid = str(uuid.uuid4())[:8]
    _pending_actions.append({
        "id":     aid,
        "tool":   tool,
        "args":   args,
        "ts":     time.time(),
        "status": "pending",
    })
    return aid


def get_pending_actions() -> list[dict]:
    """Return and clear pending actions."""
    actions = list(_pending_actions)
    _pending_actions.clear()
    return actions


def report_result(action_id: str, result: Any) -> None:
    _completed_actions[action_id] = {
        "result": result,
        "ts":     time.time(),
    }


def wait_for_result(action_id: str, timeout: float = 15.0) -> Any:
    """Block until the UI reports back, or timeout."""
    start = time.time()
    while time.time() - start < timeout:
        if action_id in _completed_actions:
            return _completed_actions.pop(action_id)["result"]
        time.sleep(0.05)
    return {"error": "timeout", "action_id": action_id}


# ── SERVER-SIDE TOOL EXECUTORS ─────────────────────────────────────
# Some tools execute fully on the server (no UI round-trip needed).
def execute_server_side(tool: str, args: dict) -> dict:
    """Execute tools that don't need the UI."""
    try:
        if tool == "search_files":
            from pathlib import Path
            q = args.get("query", "").lower()
            results = []
            for p in Path.home().rglob("*"):
                if q in p.name.lower():
                    results.append({
                        "name":   p.name,
                        "path":   str(p),
                        "is_dir": p.is_dir(),
                    })
                if len(results) >= 20:
                    break
            return {"ok": True, "results": results}

        if tool == "read_file":
            p = Path(args.get("path", "")).expanduser()
            if not p.exists() or not p.is_file():
                return {"ok": False, "error": "Not found"}
            if p.stat().st_size > 1024 * 1024:
                return {"ok": False, "error": "File too large"}
            return {"ok": True, "content": p.read_text(errors="replace")}

        if tool == "write_file":
            p = Path(args.get("path", "")).expanduser()
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(args.get("content", ""))
            return {"ok": True, "path": str(p)}

        if tool == "run_command":
            import subprocess as sp
            r = sp.run(args.get("command", ""), shell=True,
                       capture_output=True, text=True, timeout=15)
            return {
                "ok":         True,
                "output":     (r.stdout + r.stderr).strip(),
                "returncode": r.returncode,
            }

        if tool == "remember":
            mem_path = Path.home() / ".luo_os" / "luokai_facts.json"
            mem_path.parent.mkdir(parents=True, exist_ok=True)
            facts = []
            if mem_path.exists():
                facts = json.loads(mem_path.read_text())
            facts.append({"fact": args.get("fact", ""), "ts": time.time()})
            mem_path.write_text(json.dumps(facts, indent=2))
            return {"ok": True, "stored": True}

        if tool == "recall":
            mem_path = Path.home() / ".luo_os" / "luokai_facts.json"
            if not mem_path.exists():
                return {"ok": True, "matches": []}
            facts = json.loads(mem_path.read_text())
            q = args.get("query", "").lower()
            matches = [f for f in facts if q in f["fact"].lower()]
            return {"ok": True, "matches": matches[:10]}

    except Exception as e:
        return {"ok": False, "error": str(e)}

    # Tool requires UI — return None to indicate queue for UI
    return None


# Tools that must execute in the browser UI
UI_TOOLS = {
    "open_app", "close_app", "open_url", "search_web", "notify",
    "read_news", "create_note", "schedule_event"
}


def is_ui_tool(tool: str) -> bool:
    return tool in UI_TOOLS


# ── AGENT LOOP ─────────────────────────────────────────────────────
def run_agent(message: str, infer_fn: Callable, max_steps: int = 5) -> dict:
    """
    Run the agent loop:
      1. Send message to LUOKAI with tool descriptions
      2. Parse response for tool calls
      3. Execute each tool (server-side or queue for UI)
      4. Feed results back to LUOKAI
      5. Repeat until LUOKAI gives a final answer (no more tools)
    """
    system_prompt = get_tools_prompt()
    history = [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": message},
    ]
    final_answer = ""
    actions_taken = []

    for step in range(max_steps):
        response = infer_fn(history)
        if not response:
            break

        tool_calls = parse_tool_calls(response)
        cleaned = strip_tool_calls(response)

        if not tool_calls:
            final_answer = cleaned
            break

        history.append({"role": "assistant", "content": response})

        # Execute each tool call
        results = []
        for call in tool_calls:
            tool = call["tool"]
            args = call["args"]
            actions_taken.append(call)

            if is_ui_tool(tool):
                aid = queue_action(tool, args)
                # Don't wait — UI will execute and we move on
                results.append({"tool": tool, "queued": aid, "status": "queued"})
            else:
                result = execute_server_side(tool, args)
                results.append({"tool": tool, "result": result})

        # Feed results back
        history.append({
            "role": "user",
            "content": f"Tool results:\n{json.dumps(results, indent=2)}\n\nContinue or give final answer."
        })

    return {
        "answer":  final_answer or "Agent loop complete.",
        "actions": actions_taken,
        "steps":   step + 1,
    }
