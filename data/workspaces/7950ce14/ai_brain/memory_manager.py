"""Conversation and runtime memory services."""

from __future__ import annotations

import time

from core.state import RuntimeState


class MemoryManager:
    def __init__(self, state: RuntimeState, max_items: int = 30) -> None:
        self.state = state
        self.max_items = max_items

    def history(self) -> list[dict]:
        return self.state.load_memory()

    def append(self, user_text: str, bot_text: str) -> None:
        history = self.history()
        history.append({"user": user_text, "bot": bot_text, "ts": int(time.time())})
        self.state.save_memory(history, max_items=self.max_items)

