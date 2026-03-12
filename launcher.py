"""Konstance launcher: preflight checks plus supervised bot runtime."""

from __future__ import annotations

from pathlib import Path

from core.config import load_config
from launcher.preflight import run_preflight
from launcher.service_manager import run_supervisor


def run_forever() -> int:
    config = load_config()
    preflight = run_preflight()
    if not preflight.ok:
        print(preflight.summary)
        for key, value in preflight.details.items():
            print(f"{key}: {value}")
        return 1

    print("Starting KonstanceAI bot...")
    return run_supervisor(config, Path(config.root) / "bot.py")


if __name__ == "__main__":
    raise SystemExit(run_forever())
