"""Telegram command and text handlers built on the application service."""

from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from core.application import KonstanceApplication
from core.contracts import MessageContext
from konstance_telegram.renderers import render_response


def _context_from_update(app: KonstanceApplication, update: Update, text: str) -> MessageContext:
    user = update.effective_user
    return MessageContext(
        user_id=getattr(user, "id", 0) or 0,
        text=text,
        is_owner=bool(user and app.config.has_owner and user.id == app.config.owner_id),
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    app_service: KonstanceApplication = context.application.bot_data["konstance_app"]
    text = (update.message.text or "").strip()
    if not text:
        return

    response = app_service.handle_user_message(_context_from_update(app_service, update, text))
    for message in render_response(response):
        await update.message.reply_text(message[:3900])


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await handle_message(update, context)

