"""Build the Telegram application around the shared Konstance service."""

from __future__ import annotations

from telegram.ext import Application, CommandHandler, MessageHandler, filters

from core.application import KonstanceApplication
from core.config import AppConfig
from konstance_telegram.handlers import handle_message, handle_start


def build_application(config: AppConfig) -> Application:
    service = KonstanceApplication(config)
    app = Application.builder().token(config.token).build()
    app.bot_data["konstance_app"] = service
    app.add_handler(CommandHandler("start", handle_start))
    app.add_handler(CommandHandler("help", handle_message))
    app.add_handler(CommandHandler("status", handle_message))
    app.add_handler(CommandHandler("health", handle_message))
    app.add_handler(CommandHandler("drafts", handle_message))
    app.add_handler(CommandHandler("approve", handle_message))
    app.add_handler(CommandHandler("reject", handle_message))
    app.add_handler(CommandHandler("rollback", handle_message))
    app.add_handler(CommandHandler("goals", handle_message))
    app.add_handler(CommandHandler("setverbosity", handle_message))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    return app

