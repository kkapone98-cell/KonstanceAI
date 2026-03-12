"""Konstance launcher: starts bot.py and restarts on crashes with backoff."""

import os
import subprocess
import sys
import time
from pathlib import Path
from urllib import request as urllib_request

from dotenv import load_dotenv

ROOT = Path(os.getenv("KONSTANCE_ROOT", Path(__file__).resolve().parent)).resolve()
load_dotenv(ROOT / ".env")

CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def _token_present() -> bool:
    env_token = (os.getenv("TELEGRAM_BOT_TOKEN") or "").strip()
    file_token = (ROOT / "telegram_token.txt").exists()
    return bool(env_token) or file_token


def _ollama_available(timeout: int = 3) -> bool:
    try:
        with urllib_request.urlopen("http://127.0.0.1:11434/api/tags", timeout=timeout) as _:
            return True
    except Exception:
        return False


def _ensure_ollama() -> bool:
    if _ollama_available():
        print("Checking Ollama... OK")
        return True
    print("Ollama not responding. Starting ollama serve...")
    flags = CREATE_NO_WINDOW if sys.platform == "win32" else 0
    try:
        subprocess.Popen(
            ["ollama", "serve"],
            cwd=str(ROOT),
            env=os.environ.copy(),
            creationflags=flags,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        print("ERROR: 'ollama' not found. Install Ollama from https://ollama.ai")
        print("Then run: ollama pull qwen2.5:3b")
        return False
    for i in range(30):
        time.sleep(1)
        if _ollama_available():
            print("Checking Ollama... OK")
            return True
        print(f"  Waiting for Ollama... ({i + 1}/30)")
    print("ERROR: Ollama did not start within 30s.")
    print("Try manually: ollama serve")
    print("Then: ollama pull qwen2.5:3b")
    return False


def _relay_http_url() -> str:
    url = (os.getenv("OPENCLAW_RELAY_URL") or "").strip()
    if not url:
        return ""
    if url.startswith("ws://"):
        return "http://" + url[5:]
    if url.startswith("wss://"):
        return "https://" + url[6:]
    return url


def _openclaw_available(timeout: int = 5) -> bool:
    url = _relay_http_url()
    if not url:
        return False
    health_url = url.rstrip("/") + "/health"
    try:
        with urllib_request.urlopen(health_url, timeout=timeout) as _:
            return True
    except Exception:
        return False


def _ensure_openclaw() -> None:
    cmd = (os.getenv("OPENCLAW_CMD") or "").strip()
    if not cmd:
        return
    if _openclaw_available():
        print("Checking OpenClaw relay... OK")
        return
    print("OpenClaw relay not responding. Starting...")
    cwd = (os.getenv("OPENCLAW_CWD") or "").strip() or str(ROOT)
    flags = CREATE_NO_WINDOW if sys.platform == "win32" else 0
    try:
        subprocess.Popen(
            cmd,
            cwd=cwd,
            env=os.environ.copy(),
            creationflags=flags,
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception as e:
        print(f"WARNING: Could not start OpenClaw: {e}")
        print("Continuing with Ollama fallback.")
        return
    for i in range(90):
        time.sleep(1)
        if _openclaw_available():
            print("Checking OpenClaw relay... OK")
            return
        if (i + 1) % 10 == 0:
            print(f"  Waiting for OpenClaw relay... ({i + 1}/90)")
    print("WARNING: OpenClaw relay did not start within 90s. Using Ollama fallback.")


def run_forever() -> int:
    if not _token_present():
        print("ERROR: TELEGRAM_BOT_TOKEN missing (.env or telegram_token.txt)")
        return 1

    if not _ensure_ollama():
        return 1

    _ensure_openclaw()

    print("Starting KonstanceAI bot...")
    restart_count = 0
    while True:
        proc = subprocess.Popen([sys.executable, str(ROOT / "bot.py")], cwd=str(ROOT), env=os.environ.copy())
        code = proc.wait()

        if code == 0:
            print("Bot exited normally.")
            return 0

        if code == 11:
            print("Another bot instance is already running. Sleeping 30s before retry...")
            time.sleep(30)
            continue

        restart_count += 1
        delay = min(5 * restart_count, 60)
        print(f"Bot crashed (exit={code}). Restarting in {delay}s...")
        time.sleep(delay)


if __name__ == "__main__":
    raise SystemExit(run_forever())
