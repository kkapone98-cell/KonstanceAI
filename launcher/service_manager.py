"""Service supervision helpers shared by the launcher entrypoints."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path
from urllib import request as urllib_request

from core.config import AppConfig
from doctor.monitor import record_restart
from core.state import RuntimeState


CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def _ollama_available(timeout: int = 3) -> bool:
    try:
        with urllib_request.urlopen("http://127.0.0.1:11434/api/tags", timeout=timeout):
            return True
    except Exception:
        return False


def ensure_ollama(config: AppConfig) -> bool:
    if _ollama_available():
        return True
    flags = CREATE_NO_WINDOW if sys.platform == "win32" else 0
    try:
        subprocess.Popen(
            ["ollama", "serve"],
            cwd=str(config.root),
            env=os.environ.copy(),
            creationflags=flags,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        return False

    for _ in range(30):
        time.sleep(1)
        if _ollama_available():
            return True
    return False


def _relay_http_url(config: AppConfig) -> str:
    url = config.openclaw_relay_url
    if url.startswith("ws://"):
        return "http://" + url[5:]
    if url.startswith("wss://"):
        return "https://" + url[6:]
    return url


def openclaw_available(config: AppConfig, timeout: int = 5) -> bool:
    url = _relay_http_url(config).rstrip("/")
    if not url:
        return False
    try:
        with urllib_request.urlopen(f"{url}/health", timeout=timeout):
            return True
    except Exception:
        return False


def ensure_openclaw(config: AppConfig) -> None:
    if not config.openclaw_cmd or openclaw_available(config):
        return
    flags = CREATE_NO_WINDOW if sys.platform == "win32" else 0
    subprocess.Popen(
        config.openclaw_cmd,
        cwd=config.openclaw_cwd or str(config.root),
        env=os.environ.copy(),
        creationflags=flags,
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def run_supervisor(config: AppConfig, entrypoint: Path) -> int:
    state = RuntimeState(config)
    state.ensure()

    if not ensure_ollama(config):
        print("ERROR: Ollama is not available.")
        return 1

    ensure_openclaw(config)
    restart_count = 0
    while True:
        proc = subprocess.Popen([config.python_executable, str(entrypoint)], cwd=str(config.root), env=os.environ.copy())
        code = proc.wait()

        if code == 0:
            return 0
        if code == 11:
            time.sleep(10)
            continue

        restart_count += 1
        restart_state = record_restart(state)
        if restart_state.get("quarantined"):
            print("ERROR: Restart quarantine active. Run doctor diagnostics from Telegram.")
            return 12
        time.sleep(min(5 * restart_count, 60))

