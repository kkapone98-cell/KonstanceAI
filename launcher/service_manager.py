"""Service supervision helpers shared by the launcher entrypoints."""

from __future__ import annotations

import os
import subprocess
import sys
import time
import json
import signal
from pathlib import Path
from urllib import request as urllib_request

from core.config import AppConfig
from doctor.monitor import record_restart
from core.state import RuntimeState


CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def _debug_log(config: AppConfig, run_id: str, hypothesis_id: str, location: str, message: str, data: dict) -> None:
    # region agent log
    try:
        with (config.root / "debug-2cefd0.log").open("a", encoding="utf-8") as fh:
            fh.write(
                json.dumps(
                    {
                        "sessionId": "2cefd0",
                        "runId": run_id,
                        "hypothesisId": hypothesis_id,
                        "location": location,
                        "message": message,
                        "data": data,
                        "timestamp": int(time.time() * 1000),
                    },
                    ensure_ascii=True,
                )
                + "\n"
            )
    except Exception:
        pass
    # endregion


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
    _debug_log(
        config,
        run_id="pre-fix",
        hypothesis_id="H2",
        location="launcher/service_manager.py:openclaw_available",
        message="launcher_openclaw_probe_started",
        data={"url": url, "timeout_sec": timeout},
    )
    if not url:
        _debug_log(
            config,
            run_id="pre-fix",
            hypothesis_id="H1",
            location="launcher/service_manager.py:openclaw_available",
            message="launcher_openclaw_probe_skipped_empty_url",
            data={},
        )
        return False
    try:
        with urllib_request.urlopen(f"{url}/health", timeout=timeout):
            _debug_log(
                config,
                run_id="pre-fix",
                hypothesis_id="H2",
                location="launcher/service_manager.py:openclaw_available",
                message="launcher_openclaw_health_ok",
                data={"url": f"{url}/health"},
            )
            return True
    except Exception as exc:
        _debug_log(
            config,
            run_id="pre-fix",
            hypothesis_id="H2",
            location="launcher/service_manager.py:openclaw_available",
            message="launcher_openclaw_health_failed",
            data={"error_type": type(exc).__name__},
        )
        return False


def ensure_openclaw(config: AppConfig) -> None:
    available = openclaw_available(config)
    _debug_log(
        config,
        run_id="pre-fix",
        hypothesis_id="H3",
        location="launcher/service_manager.py:ensure_openclaw",
        message="ensure_openclaw_decision",
        data={"has_openclaw_cmd": bool(config.openclaw_cmd), "already_available": available},
    )
    if not config.openclaw_cmd or available:
        return
    flags = CREATE_NO_WINDOW if sys.platform == "win32" else 0
    cwd = Path(config.openclaw_cwd or config.root)
    if not cwd.is_absolute():
        cwd = (config.root / cwd).resolve()
    try:
        if not cwd.exists():
            cwd.mkdir(parents=True, exist_ok=True)
        if not cwd.is_dir():
            cwd = config.root
    except OSError:
        cwd = config.root
    try:
        subprocess.Popen(
            config.openclaw_cmd,
            cwd=str(cwd),
            env=os.environ.copy(),
            creationflags=flags,
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except OSError as exc:
        _debug_log(
            config,
            run_id="post-fix",
            hypothesis_id="H3",
            location="launcher/service_manager.py:ensure_openclaw",
            message="ensure_openclaw_spawn_failed",
            data={"error_type": type(exc).__name__, "cwd": str(cwd)},
        )
        return

    # Give the relay a short warmup window so /status can report healthy quickly.
    for _ in range(20):
        time.sleep(1)
        if openclaw_available(config, timeout=2):
            break


def _read_lock_pid(config: AppConfig) -> int:
    lock_path = config.data_dir / "bot.lock"
    if not lock_path.exists():
        return 0
    try:
        raw = lock_path.read_text(encoding="utf-8", errors="ignore").strip()
    except OSError:
        return 0
    if not raw.startswith("pid="):
        return 0
    pid_text = raw.split(" ", 1)[0].replace("pid=", "", 1).strip()
    try:
        return int(pid_text)
    except ValueError:
        return 0


def terminate_running_bot(config: AppConfig, timeout_sec: int = 8) -> bool:
    pid = _read_lock_pid(config)
    if not pid:
        return False
    try:
        os.kill(pid, signal.SIGTERM)
    except OSError:
        return False

    start = time.time()
    while time.time() - start <= timeout_sec:
        try:
            os.kill(pid, 0)
            time.sleep(0.4)
        except OSError:
            break
    try:
        (config.data_dir / "bot.lock").unlink(missing_ok=True)
    except OSError:
        pass
    return True


def start_clean(config: AppConfig) -> None:
    terminate_running_bot(config)
    state = RuntimeState(config)
    restart_state_path = state.restart_state_path
    if restart_state_path.exists():
        restart_state_path.write_text(
            json.dumps({"window_started_at": 0, "recent_restart_times": [], "quarantined": False}, indent=2),
            encoding="utf-8",
        )


def run_supervisor(config: AppConfig, entrypoint: Path) -> int:
    state = RuntimeState(config)
    state.ensure()

    if not ensure_ollama(config):
        print("ERROR: Ollama is not available.")
        return 1

    ensure_openclaw(config)
    restart_count = 0
    if not entrypoint.exists():
        print(f"ERROR: Bot entrypoint missing: {entrypoint}")
        return 1
    while True:
        proc = subprocess.Popen([config.python_executable, str(entrypoint)], cwd=str(config.root), env=os.environ.copy())
        code = proc.wait()

        if code == 0:
            return 0
        if code == 11:
            print("INFO: Existing bot instance detected (code 11). Reusing active poller.")
            return 11

        restart_count += 1
        restart_state = record_restart(state)
        if restart_state.get("quarantined"):
            print("ERROR: Restart quarantine active. Run doctor diagnostics from Telegram.")
            return 12
        time.sleep(min(5 * restart_count, 60))

