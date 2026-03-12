"""Telegram response formatting helpers."""

from __future__ import annotations

from core.contracts import MessageResponse


def render_response(response: MessageResponse) -> list[str]:
    messages = [response.text] if response.text else []
    messages.extend([item for item in response.followups if item])
    return messages or ["..."]

