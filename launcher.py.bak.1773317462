"""Konstance launcher: starts bot.py and restarts on crashes with backoff."""

import os
import subprocess
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(os.getenv("KONSTANCE_ROOT", Path(__file__).resolve().parent)).resolve()
load_dotenv(ROOT / ".env")


def _token_present() -> bool:
    env_token = (os.getenv("TELEGRAM_BOT_TOKEN") or "").strip()
    file_token = (ROOT / "telegram_token.txt").exists()
    return bool(env_token) or file_token


def run_forever() -> int:
    if not _token_present():
        print("ERROR: TELEGRAM_BOT_TOKEN missing (.env or telegram_token.txt)")
        return 1

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
