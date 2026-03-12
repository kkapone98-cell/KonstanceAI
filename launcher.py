"""Konstance launcher: preflight checks plus supervised bot runtime."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from core.config import load_config
from launcher.preflight import run_preflight
from launcher.service_manager import run_supervisor, start_clean, terminate_running_bot


def run_forever(restart: bool = False, clean: bool = False) -> int:
    os.chdir(Path(__file__).resolve().parent)
    config = load_config()
    root = Path(config.root).resolve()
    bot_path = (root / "bot.py").resolve()
    openclaw_relay = (root / "openclaw" / "openclaw_relay.py").resolve()

    print(f"[launcher] root={root}")
    print(f"[launcher] bot.py={bot_path} exists={bot_path.exists()}")
    print(f"[launcher] openclaw_relay={openclaw_relay} exists={openclaw_relay.exists()}")
    print(f"[launcher] OPENCLAW_CMD={config.openclaw_cmd}")
    print(f"[launcher] OPENCLAW_CWD={config.openclaw_cwd}")

    if clean:
        start_clean(config)
    elif restart:
        terminate_running_bot(config)

    preflight = run_preflight()
    if not preflight.ok:
        print(preflight.summary)
        for key, value in preflight.details.items():
            print(f"{key}: {value}")
        return 1

    print("Starting KonstanceAI bot...")
    code = run_supervisor(config, bot_path)
    if code == 11:
        print("KonstanceAI is already running. Reusing existing bot instance.")
        return 0
    return code


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="KonstanceAI safe launcher")
    parser.add_argument("--restart", action="store_true", help="Terminate active bot process before startup.")
    parser.add_argument("--start-clean", action="store_true", help="Reset runtime lock/restart state before startup.")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Alias flag kept for Telegram compatibility; launcher still supervises the bot.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    raise SystemExit(run_forever(restart=args.restart, clean=args.start_clean))
