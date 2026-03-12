"""Conversational response generation with self-context and memory."""

from __future__ import annotations

from core.state import RuntimeState
from scripts.modules.self_model import build_self_context
from scripts.modules.smart_reply_engine import smart_reply


def generate_reply(state: RuntimeState, user_text: str) -> str:
    prefs = state.load_prefs()
    profile = state.load_profile()
    history = state.load_memory()
    self_context = build_self_context()
    return smart_reply(user_text, prefs, profile, history=history, self_context=self_context)

