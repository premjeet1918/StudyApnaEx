"""
Shared bot status tracker — keeps extraction progress
visible to the Flask dashboard.

Uses a JSON file on disk so the Flask process and the
Telegram-bot process (which run as separate OS processes
via multiprocessing) can share state.
"""
import json
import os
import threading
from datetime import datetime
import pytz

india_tz = pytz.timezone("Asia/Kolkata")

STATUS_FILE = os.path.join(os.path.dirname(__file__), ".bot_status.json")
_lock = threading.Lock()


def _default_state():
    return {
        "bot_info": {
            "running": False,
            "started_at": None,
            "bot_username": "",
            "bot_name": "",
        },
        "tasks": [],
    }


def _read():
    """Read current state from disk."""
    try:
        with open(STATUS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return _default_state()


def _write(state):
    """Persist state to disk."""
    try:
        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False)
    except Exception:
        pass


# ── Bot lifecycle ──────────────────────────────────────────

def mark_bot_running(username="", name=""):
    with _lock:
        state = _read()
        state["bot_info"]["running"] = True
        state["bot_info"]["started_at"] = datetime.now(india_tz).strftime(
            "%d-%m-%Y %I:%M %p"
        )
        state["bot_info"]["bot_username"] = username
        state["bot_info"]["bot_name"] = name
        _write(state)

def mark_bot_stopped():
    with _lock:
        state = _read()
        state["bot_info"]["running"] = False
        _write(state)


# ── Task tracking ──────────────────────────────────────────

def add_task(batch_id, name, total=0, user_id=0, app_name=""):
    now = datetime.now(india_tz).strftime("%Y-%m-%d")
    entry = {
        "batch_id": str(batch_id),
        "name": name,
        "total": total,
        "done": 0,
        "status": "Running",
        "date_added": now,
        "user_id": user_id,
        "app_name": app_name,
        "elapsed": 0,
    }
    with _lock:
        state = _read()
        state["tasks"].insert(0, entry)
        # keep last 50 entries
        state["tasks"] = state["tasks"][:50]
        _write(state)
    return entry


def update_task(batch_id, done=None, total=None, status=None, elapsed=None):
    with _lock:
        state = _read()
        for t in state["tasks"]:
            if t["batch_id"] == str(batch_id):
                if done is not None:
                    t["done"] = done
                if total is not None:
                    t["total"] = total
                if status is not None:
                    t["status"] = status
                if elapsed is not None:
                    t["elapsed"] = elapsed
                break
        _write(state)


def get_tasks():
    state = _read()
    return state.get("tasks", [])


def get_bot_info():
    state = _read()
    return state.get("bot_info", _default_state()["bot_info"])
