"""Persistent context loader for KonstanceAI.

Reads from .konstance_context/ (progress.json, recap.md, versions.json, goals.json).
Falls back to data/ when context files are missing.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CTX_DIR = ROOT / ".konstance_context"
DATA_DIR = ROOT / "data"


def _ctx_path(name: str) -> Path:
    return CTX_DIR / name


def _data_path(name: str) -> Path:
    return DATA_DIR / name


def _ensure_ctx() -> None:
    CTX_DIR.mkdir(parents=True, exist_ok=True)


def load_progress() -> dict:
    """Load progress.json from .konstance_context or create default."""
    p = _ctx_path("progress.json")
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    default = {
        "phase": "operational",
        "last_build_ts": int(time.time()),
        "last_build_summary": "",
        "steps_completed": [],
        "current_goal": "Persistent context active",
    }
    _ensure_ctx()
    try:
        p.write_text(json.dumps(default, indent=2), encoding="utf-8")
    except Exception:
        pass
    return default


def load_recap() -> str:
    """Load recap.md from .konstance_context or return empty."""
    p = _ctx_path("recap.md")
    if p.exists():
        try:
            return p.read_text(encoding="utf-8").strip()
        except Exception:
            pass
    return ""


def load_versions() -> dict:
    """Load versions.json from .konstance_context or create default."""
    p = _ctx_path("versions.json")
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"context_version": 1, "modules": {}, "updated_at": int(time.time())}


def load_goals_fallback() -> dict:
    """Load goals from .konstance_context first, then data/goals.json."""
    p = _ctx_path("goals.json")
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    q = _data_path("goals.json")
    if q.exists():
        try:
            return json.loads(q.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"active": [], "achieved": [], "version": 1}


def context_summary() -> str:
    """Brief summary for status/report."""
    prog = load_progress()
    recap = load_recap()
    phase = prog.get("phase", "unknown")
    current = prog.get("current_goal", "")
    lines = [f"Context phase: {phase}"]
    if current:
        lines.append(f"Current goal: {current}")
    if recap and len(recap) < 200:
        lines.append(f"Recap: {recap[:150]}...")
    return "\n".join(lines)


def update_progress(phase: str = None, steps: list = None, current_goal: str = None) -> None:
    """Update progress.json."""
    prog = load_progress()
    if phase is not None:
        prog["phase"] = phase
    if steps is not None:
        prog.setdefault("steps_completed", []).extend(steps)
    if current_goal is not None:
        prog["current_goal"] = current_goal
    prog["last_build_ts"] = int(time.time())
    _ensure_ctx()
    try:
        _ctx_path("progress.json").write_text(json.dumps(prog, indent=2), encoding="utf-8")
    except Exception:
        pass
