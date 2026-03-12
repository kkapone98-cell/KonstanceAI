import json
import logging
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from scripts.modules.smart_reply_engine import (
    ollama_fallback_available,
    openclaw_generate,
    relay_available,
    smart_reply,
)

ROOT = Path(os.getenv("KONSTANCE_ROOT", Path(__file__).resolve().parent)).resolve()
DATA_DIR = ROOT / "data"
LOGS_DIR = ROOT / "logs"
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

PREFS_FILE = DATA_DIR / "prefs.json"
PROFILE_FILE = DATA_DIR / "profile.json"
HEALTH_FILE = DATA_DIR / "health.json"
LOG_FILE = LOGS_DIR / "bot.log"


class BotLockError(RuntimeError):
    pass


def _acquire_single_instance_lock() -> object:
    lock_path = DATA_DIR / "bot.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    handle = open(lock_path, "a+", encoding="utf-8")

    try:
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except Exception:
        handle.close()
        raise BotLockError("Another bot instance is already running.")

    handle.seek(0)
    handle.truncate(0)
    handle.write(f"pid={os.getpid()} started={int(time.time())}\n")
    handle.flush()
    return handle


def _setup_logging() -> logging.Logger:
    logger = logging.getLogger("konstance.bot")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
    fh.setFormatter(fmt)
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(fmt)

    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger


log = _setup_logging()


def _load_json(path: Path, fallback):
    if not path.exists():
        return fallback
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return fallback


def _save_json(path: Path, payload) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _load_token() -> str:
    load_dotenv(ROOT / ".env")
    token = (os.getenv("TELEGRAM_BOT_TOKEN") or "").strip()
    if token:
        return token
    token_file = ROOT / "telegram_token.txt"
    if token_file.exists():
        return token_file.read_text(encoding="utf-8").strip()
    return ""


def _touch_health(**kwargs) -> None:
    health = _load_json(
        HEALTH_FILE,
        {"last_start": 0, "last_message": 0, "relay_available": False, "ollama_available": False},
    )
    health.update(kwargs)
    _save_json(HEALTH_FILE, health)


def _owner_only(update: Update) -> bool:
    owner_id = (os.getenv("OWNER_ID") or "").strip()
    if not owner_id:
        return True
    user = update.effective_user
    return bool(user and str(user.id) == owner_id)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("KonstanceAI online ✅")


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prefs = _load_json(PREFS_FILE, {"verbosity": "medium"})
    await update.message.reply_text(
        "\n".join(
            [
                "Status: running",
                f"Root: {ROOT}",
                f"Relay available: {relay_available()}",
                f"Ollama available: {ollama_fallback_available()}",
                f"Verbosity: {prefs.get('verbosity', 'medium')}",
            ]
        )
    )


async def cmd_health(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(json.dumps(_load_json(HEALTH_FILE, {}), indent=2))


async def cmd_cloudtest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prefs = _load_json(PREFS_FILE, {"verbosity": "medium"})
    profile = _load_json(PROFILE_FILE, {"name": "Konstance"})
    out = openclaw_generate("Reply exactly CLOUD_OK", prefs, profile, timeout_sec=20)
    await update.message.reply_text("Cloud test: OK" if out else "Cloud test: FAILED")


async def cmd_setverbosity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _owner_only(update):
        await update.message.reply_text("Not authorized.")
        return

    if not context.args or context.args[0] not in {"short", "medium", "long"}:
        await update.message.reply_text("Usage: /setverbosity <short|medium|long>")
        return

    prefs = _load_json(PREFS_FILE, {"verbosity": "medium"})
    prefs["verbosity"] = context.args[0]
    _save_json(PREFS_FILE, prefs)
    await update.message.reply_text(f"Verbosity updated: {prefs['verbosity']}")


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()
    prefs = _load_json(PREFS_FILE, {"verbosity": "medium"})
    profile = _load_json(PROFILE_FILE, {"name": "Konstance"})

    _touch_health(last_message=int(time.time()))
    reply = smart_reply(text, prefs, profile)
    await update.message.reply_text(reply[:3900])


def main() -> int:
    token = _load_token()
    if not token or ":" not in token:
        log.error("Missing TELEGRAM_BOT_TOKEN in .env or telegram_token.txt")
        return 1

    _touch_health(
        last_start=int(time.time()),
        relay_available=relay_available(),
        ollama_available=ollama_fallback_available(),
    )

    try:
        lock_handle = _acquire_single_instance_lock()
    except BotLockError as e:
        log.error(str(e))
        return 11

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("health", cmd_health))
    app.add_handler(CommandHandler("cloudtest", cmd_cloudtest))
    app.add_handler(CommandHandler("setverbosity", cmd_setverbosity))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))

    log.info("Bot starting polling.")
    try:
        app.run_polling(drop_pending_updates=True)
    finally:
        # keep lock referenced for process lifetime; close only on shutdown
        lock_handle.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
