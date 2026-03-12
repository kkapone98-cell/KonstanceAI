"""Health, restart, and quarantine tracking."""

from __future__ import annotations

import time

from core.state import RuntimeState, read_json, write_json


def record_restart(state: RuntimeState, max_restarts: int = 5, window_seconds: int = 300) -> dict:
    payload = read_json(state.restart_state_path, {"window_started_at": 0, "recent_restart_times": [], "quarantined": False})
    now = int(time.time())
    recent = [ts for ts in payload.get("recent_restart_times", []) if now - ts <= window_seconds]
    recent.append(now)
    payload["recent_restart_times"] = recent
    payload["window_started_at"] = recent[0] if recent else now
    payload["quarantined"] = len(recent) > max_restarts
    write_json(state.restart_state_path, payload)
    state.update_health(restart_count=len(recent), quarantined=payload["quarantined"])
    return payload


def clear_quarantine(state: RuntimeState) -> None:
    payload = {"window_started_at": 0, "recent_restart_times": [], "quarantined": False}
    write_json(state.restart_state_path, payload)
    state.update_health(quarantined=False, restart_count=0)

