"""Telegram runtime entrypoint for KonstanceAI."""

from __future__ import annotations

import logging
import os
import sys
import time
from pathlib import Path

from telegram.error import Conflict

from core.config import load_config
from core.state import RuntimeState
from konstance_telegram.adapter import build_application
from scripts.modules.smart_reply_engine import ollama_fallback_available, relay_available

ROOT = Path(os.getenv("KONSTANCE_ROOT", Path(__file__).resolve().parent)).resolve()
CONFIG = load_config(ROOT)
LOG_FILE = CONFIG.logs_dir / "bot.log"


class BotLockError(RuntimeError):
    """Raised when another polling instance already owns the bot lock."""


def _load_token() -> str:
    return load_config(ROOT).token


def _setup_logging() -> logging.Logger:
    CONFIG.ensure_runtime_dirs()
    logger = logging.getLogger("konstance.bot")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setFormatter(formatter)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    return logger


log = _setup_logging()


def _acquire_single_instance_lock() -> object:
    lock_path = CONFIG.data_dir / "bot.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    handle = open(lock_path, "a+", encoding="utf-8")
    try:
        if os.name == "nt":
            import msvcrt

            # Lock the first byte consistently; locking at EOF can allow duplicates.
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except Exception as exc:
        handle.close()
        raise BotLockError("Another bot instance is already running.") from exc

    try:
        handle.seek(0)
        handle.truncate(0)
        handle.write(f"pid={os.getpid()} started={int(time.time())}\n")
        handle.flush()
    except OSError:
        # On Windows, byte-range locking can reject writes to the same file region.
        # Lock ownership is the authoritative singleton signal; metadata is optional.
        pass
    return handle


def main() -> int:
    token = _load_token()
    if not token or ":" not in token:
        log.error("Missing TELEGRAM_BOT_TOKEN in .env or telegram_token.txt")
        return 1
    if not CONFIG.has_owner:
        log.error("Missing OWNER_ID in .env")
        return 1

    state = RuntimeState(CONFIG)
    state.ensure()
    state.update_health(
        last_start=int(time.time()),
        relay_available=relay_available(),
        ollama_available=ollama_fallback_available(),
    )

    try:
        lock_handle = _acquire_single_instance_lock()
    except BotLockError as exc:
        log.info(str(exc))
        return 11

    app = build_application(CONFIG)
    log.info("Bot starting polling.")
    try:
        app.run_polling(drop_pending_updates=True)
        if app.bot_data.get("telegram_conflict"):
            return 11
    except Conflict:
        log.error("Telegram polling conflict detected. Another getUpdates consumer is active.")
        return 11
    finally:
        lock_handle.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
