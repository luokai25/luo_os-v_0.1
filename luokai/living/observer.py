"""
LuoOS Observer
───────────────
Subscribes to the event bus and continuously updates working memory.

The observer is a pure passive process — it never decides anything.
It just translates raw events into structured situational awareness.

Decisions and actions are handled by the predictor / tinkerer / daemon.
"""
import time
from urllib.parse import urlparse

from .event_bus  import bus, Event
from .working_memory import memory


# ────────────────────────────────────────────────────────────────
# Heuristics for inferring task / topic
# ────────────────────────────────────────────────────────────────
TASK_KEYWORDS = {
    "writing":   ["report", "essay", "letter", "email", "draft", "memo", "doc"],
    "coding":    ["debug", "function", "class", "import", "error", "compile"],
    "research":  ["search", "find", "research", "look up", "investigate"],
    "planning":  ["schedule", "plan", "agenda", "deadline", "calendar"],
    "analysis":  ["data", "chart", "compare", "analyze", "metric"],
    "learning":  ["explain", "what is", "how does", "tutorial", "example"],
    "creative":  ["design", "draw", "compose", "creative", "art"],
}

PERSON_INDICATORS = ["@", "from:", "to:", "with ", "told ", "asked "]


def infer_task(text: str) -> str | None:
    """Try to figure out what kind of task the user is doing."""
    if not text:
        return None
    lower = text.lower()
    scores: dict[str, int] = {}
    for task, keywords in TASK_KEYWORDS.items():
        scores[task] = sum(1 for k in keywords if k in lower)
    if not any(scores.values()):
        return None
    return max(scores, key=scores.get)


def extract_topics(text: str, max_n: int = 3) -> list[str]:
    """Extract topic keywords from text — naive but useful."""
    if not text:
        return []
    # Strip punctuation, lowercase, keep meaningful words
    import re
    words = re.findall(r"[a-zA-Z][a-zA-Z']{3,}", text.lower())
    # Drop common stopwords
    stop = {"that","this","with","from","have","been","were","they","their",
            "what","when","where","which","there","about","would","could",
            "should","because","please","thank","thanks","just","like","really",
            "going","trying","think","know","want","need","make","take","give",
            "find","help","hello","good","fine","right","time","much","more",
            "very","also","some","many","most","other","said","tell","look"}
    filtered = [w for w in words if w not in stop and len(w) >= 4]
    # Frequency count
    from collections import Counter
    counts = Counter(filtered)
    return [w for w, _ in counts.most_common(max_n)]


def extract_url_topic(url: str) -> str | None:
    try:
        parts = urlparse(url)
        host  = parts.netloc.replace("www.", "")
        return host.split(".")[0] if host else None
    except Exception:
        return None


# ────────────────────────────────────────────────────────────────
# Event Handlers
# ────────────────────────────────────────────────────────────────

@bus.subscribe("app.opened")
def _on_app_opened(e: Event):
    app_id = e.data.get("app") or e.data.get("id")
    if not app_id:
        return
    memory.add_to("open_apps", app_id)
    memory.set("current_focus", app_id)


@bus.subscribe("app.closed")
def _on_app_closed(e: Event):
    app_id = e.data.get("app") or e.data.get("id")
    if app_id:
        memory.remove_from("open_apps", app_id)


@bus.subscribe("app.focused")
def _on_app_focused(e: Event):
    app_id = e.data.get("app") or e.data.get("id")
    if app_id:
        memory.set("current_focus", app_id)


@bus.subscribe("file.*")
def _on_file_event(e: Event):
    path = e.data.get("path")
    if path:
        memory.push_recent("open_files", path, max_size=20)


@bus.subscribe("browser.navigate")
def _on_browser_nav(e: Event):
    url = e.data.get("url")
    if url:
        memory.push_recent("recent_urls", url, max_size=20)
        topic = extract_url_topic(url)
        if topic:
            memory.push_recent("recent_topics", topic, max_size=20)


@bus.subscribe("chat.user_msg")
def _on_user_msg(e: Event):
    text = e.data.get("text", "") or e.data.get("message", "")
    memory.increment("interactions_today")
    # Infer task
    task = infer_task(text)
    if task:
        memory.set("current_task", task)
    # Extract topics
    topics = extract_topics(text)
    for t in topics:
        memory.push_recent("recent_topics", t, max_size=20)
    # Detect mentioned people (capital words after "with"/"told"/"from"/etc.)
    import re
    for indicator in PERSON_INDICATORS:
        if indicator in text.lower():
            after = text.lower().split(indicator, 1)[1] if indicator in text.lower() else ""
            # First capitalized word after indicator
            match = re.search(r"\b([A-Z][a-z]{2,15})\b", text[text.lower().find(indicator):])
            if match:
                memory.push_recent("recent_people", match.group(1), max_size=10)


@bus.subscribe("chat.assistant_msg")
def _on_assistant_msg(e: Event):
    text = e.data.get("text", "")
    topics = extract_topics(text, max_n=2)
    for t in topics:
        memory.push_recent("recent_topics", t, max_size=20)


@bus.subscribe("perception.*")
def _on_perception(e: Event):
    state = memory.get("user_state", {})
    if e.type == "perception.gaze":
        # gaze data could update attention if not already
        if "attention" in e.data:
            state["attention"] = e.data["attention"]
    elif e.type == "perception.mood_change":
        if "mood" in e.data:
            state["mood"] = e.data["mood"]
    elif e.type == "perception.bpm":
        if "bpm" in e.data:
            state["bpm"] = e.data["bpm"]
    elif e.type == "perception.stress":
        if "stress" in e.data:
            state["stress"] = e.data["stress"]
    memory.set("user_state", state)


@bus.subscribe("calendar.event_added")
def _on_cal_event(e: Event):
    ev = e.data.get("event")
    if ev:
        memory.push_recent("todays_calendar", ev, max_size=20)


@bus.subscribe("note.created")
@bus.subscribe("note.updated")
def _on_note_event(e: Event):
    title   = e.data.get("title", "")
    content = e.data.get("content", "")
    topics  = extract_topics(title + " " + content, max_n=3)
    for t in topics:
        memory.push_recent("recent_topics", t, max_size=20)


@bus.subscribe("system.*")
def _on_system_event(e: Event):
    if e.type == "system.idle_start":
        memory.set("idle_since", time.time())
    elif e.type == "system.idle_end":
        memory.set("idle_since", None)


# ──── Universal counter ───────────────────────────────────────
@bus.subscribe("*")
def _count_all_events(e: Event):
    memory.increment("events_processed")


# ────────────────────────────────────────────────────────────────
# Public initialization
# ────────────────────────────────────────────────────────────────
def install():
    """Initialize the observer.
    Decorators above auto-register handlers when this module is imported.
    This function exists for explicit initialization.
    """
    print("[Observer] Listening for events on the bus")
    return True


# Auto-install on import
install()
