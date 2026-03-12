"""Owner-only safe local command execution for Telegram operations."""

from __future__ import annotations

import os
import re
import shlex
import subprocess
from pathlib import Path

from core.config import AppConfig

CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
_SAFE_CMD_RE = re.compile(r"^[\w./:\\\-\s=]+$")
_PKG_RE = re.compile(r"^[A-Za-z0-9_.\-]+$")


def _blocked(raw: str) -> bool:
    lowered = raw.lower()
    blocked_tokens = (
        "&&",
        "||",
        ";",
        ">",
        "<",
        "|",
        "rm ",
        "rmdir ",
        "del ",
        "format ",
        "shutdown ",
        "powershell -enc",
    )
    return any(token in lowered for token in blocked_tokens)


def _parse_cmd(raw: str) -> list[str]:
    if not raw or _blocked(raw):
        return []
    try:
        return shlex.split(raw, posix=False)
    except ValueError:
        return []


def _normalize(raw: str) -> str:
    text = (raw or "").strip()
    prefixes = (
        "run command ",
        "please run ",
        "execute ",
        "command ",
        "/run ",
        "run ",
    )
    lowered = text.lower()
    for prefix in prefixes:
        if lowered.startswith(prefix):
            return text[len(prefix) :].strip()
    return text


def _allowlist(command: list[str], config: AppConfig) -> bool:
    if not command:
        return False
    exe = command[0].lower()
    root = str(config.root).lower()

    if exe in {"python", "python.exe", config.python_executable.lower()}:
        if len(command) < 2:
            return False
        if command[1:3] == ["-m", "pip"]:
            return True
        if command[1:3] == ["-m", "unittest"]:
            return True
        target = command[1].replace("\\", "/").lower()
        if target in {"launcher.py", "bot.py", "start.py", "openclaw/openclaw_relay.py", "openclaw\\openclaw_relay.py"}:
            return True
        if target.startswith("scripts/"):
            return True
        return False

    if exe in {"pip", "pip.exe"}:
        return len(command) >= 2 and command[1].lower() in {"install", "uninstall", "list", "show"}

    if exe in {"where", "ollama", "ollama.exe"}:
        return True

    if exe == "git":
        return len(command) >= 2 and command[1].lower() in {"status", "diff", "log"}

    # Allow explicit absolute python path under repo venv only.
    if exe.endswith("python.exe") and root in exe:
        return _allowlist(["python", *command[1:]], config)
    return False


def execute_owner_command(config: AppConfig, request_text: str, timeout_sec: int = 180) -> dict[str, object]:
    raw = _normalize(request_text)
    if not raw:
        return {"ok": False, "error": "No command provided."}
    if not _SAFE_CMD_RE.match(raw):
        return {"ok": False, "error": "Command contains blocked characters."}

    command = _parse_cmd(raw)
    if not _allowlist(command, config):
        return {"ok": False, "error": "Command blocked by safety policy."}

    flags = CREATE_NO_WINDOW if os.name == "nt" else 0
    try:
        proc = subprocess.run(
            command,
            cwd=str(config.root),
            env=os.environ.copy(),
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            creationflags=flags,
            shell=False,
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"Command timed out after {timeout_sec}s.", "command": command}
    except OSError as exc:
        return {"ok": False, "error": f"Command failed to start: {exc}", "command": command}

    output = ((proc.stdout or "") + "\n" + (proc.stderr or "")).strip()[:3500]
    return {
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "output": output or "(no output)",
        "command": command,
    }


def install_dependency(config: AppConfig, package: str | None = None) -> dict[str, object]:
    if package:
        pkg = package.strip()
        if not _PKG_RE.match(pkg):
            return {"ok": False, "error": "Invalid package name."}
        return execute_owner_command(config, f"python -m pip install {pkg}")
    return execute_owner_command(config, "python -m pip install -r requirements.txt")
