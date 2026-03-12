#!/usr/bin/env python3
"""Automated KonstanceAI build, validation, and launch.

Ensures venv, model alignment, context, runs tests, updates persistent context, and commits.
Run from project root: python build.py
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LOG_DIR = ROOT / ".workspace" / "logs"
BUILD_LOG = LOG_DIR / "build.log"


def _log(msg: str) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}\n"
    try:
        with BUILD_LOG.open("a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        pass
    print(msg)


def _run(cmd: list[str], cwd: Path | None = None, timeout: int = 120) -> tuple[int, str]:
    try:
        r = subprocess.run(
            cmd,
            cwd=cwd or ROOT,
            capture_output=True,
            text=True,
            timeout=timeout,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0,
        )
        out = (r.stdout or "") + (r.stderr or "")
        return r.returncode, out
    except subprocess.TimeoutExpired:
        return -1, "Command timed out"
    except Exception as e:
        return -1, str(e)


def _ensure_venv() -> bool:
    if hasattr(sys, "real_prefix") or (hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix):
        _log("venv already active")
        return True
    _log("venv not detected; run: .venv\\Scripts\\Activate.ps1 (Windows) or source .venv/bin/activate")
    return False


def _check_ollama() -> bool:
    code, out = _run(["ollama", "list"], timeout=10)
    if code != 0:
        _log("Ollama not responding; start with: ollama serve")
        return False
    _log("Ollama OK")
    return True


def _check_relay() -> bool:
    try:
        from urllib.request import urlopen
        url = os.getenv("OPENCLAW_RELAY_URL", "ws://127.0.0.1:18789").strip()
        http = url.replace("ws://", "http://").replace("wss://", "https://").rstrip("/")
        with urlopen(f"{http}/health", timeout=5):
            _log("OpenClaw relay OK")
            return True
    except Exception as e:
        _log(f"Relay not reachable: {e}. Start with launcher or: python openclaw/openclaw_relay.py")
        return False


def _ensure_context() -> None:
    ctx = ROOT / ".konstance_context"
    ctx.mkdir(parents=True, exist_ok=True)
    for name, default in (
        ("progress.json", {"phase": "operational", "last_build_ts": int(time.time()), "steps_completed": []}),
        ("versions.json", {"context_version": 1, "modules": {}, "updated_at": int(time.time())}),
    ):
        p = ctx / name
        if not p.exists():
            p.write_text(json.dumps(default, indent=2), encoding="utf-8")
            _log(f"Created {p}")
    if not (ctx / "recap.md").exists():
        (ctx / "recap.md").write_text("# KonstanceAI Context\n", encoding="utf-8")
    if not (ctx / "goals.json").exists():
        (ctx / "goals.json").write_text(
            json.dumps({"active": [], "achieved": [], "version": 1}, indent=2),
            encoding="utf-8",
        )
    _log("Persistent context ensured")


def _run_tests() -> tuple[bool, str]:
    code, out = _run([sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short", "-q"], timeout=120)
    return code == 0, out[:2000] if out else ""


def _update_context(phase: str = "operational") -> None:
    try:
        from scripts.modules.konstance_context import update_progress
        update_progress(phase=phase, steps=["build_complete"])
        _log("Context updated")
    except Exception as e:
        _log(f"Context update skipped: {e}")


def _git_commit() -> bool:
    code, out = _run(["git", "rev-parse", "--git-dir"])
    if code != 0 or not out.strip():
        _log("Not a git repo or git unavailable")
        return False
    code, out = _run(["git", "status", "--short"])
    if not out.strip():
        _log("No changes to commit")
        return True
    ts = time.strftime("%Y-%m-%d %H:%M")
    msg = f"KonstanceAI build {ts}"
    code, _ = _run(["git", "add", "-A"])
    code, _ = _run(["git", "commit", "-m", msg])
    _log(f"Committed: {msg}")
    return True


def main() -> int:
    _log("=== KonstanceAI build start ===")
    os.chdir(ROOT)

    _ensure_venv()
    _ensure_context()

    ok_ollama = _check_ollama()
    ok_relay = _check_relay()

    ok_tests, test_out = _run_tests()
    if ok_tests:
        _log("Tests passed")
    else:
        _log(f"Tests failed or no tests: {test_out[:500]}")

    _update_context()

    if ok_ollama and ok_relay:
        _log("Ollama and relay OK; bot can run with: python start.py")
    else:
        _log("Start Ollama and/or relay before running the bot")

    _git_commit()
    _log("=== KonstanceAI build complete ===")
    _log("Ready for: python start.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
