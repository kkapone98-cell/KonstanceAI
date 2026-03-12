"""Legacy compatibility helpers that delegate to the governed upgrade system."""

from __future__ import annotations

import re

from ai_brain.self_upgrade_agent import approve_upgrade, list_drafts
from core.config import load_config
from core.state import RuntimeState, read_json

ROOT = load_config().root
_APPROVAL_PHRASES = frozenset(
    {"yes", "yep", "yeah", "ok", "okay", "sure", "go ahead", "do it", "apply", "approve", "approved"}
)


def _state() -> RuntimeState:
    state = RuntimeState(load_config(ROOT))
    state.ensure()
    return state


def store_draft(user_id, target, content, description, bak_path="") -> str:
    return ""


def get_draft(did: str) -> dict | None:
    return read_json(_state().drafts_path, {"drafts": {}}).get("drafts", {}).get(did)


def delete_draft(did: str):
    payload = read_json(_state().drafts_path, {"drafts": {}})
    payload.setdefault("drafts", {}).pop(did, None)
    from core.state import write_json

    write_json(_state().drafts_path, payload)


def list_drafts_dict() -> dict:
    return read_json(_state().drafts_path, {"drafts": {}}).get("drafts", {})


def list_drafts() -> dict:
    return list_drafts_dict()


def build_status_report() -> str:
    state = _state()
    health = state.load_health()
    return "\n".join(
        [
            "Konstance status",
            f"Relay available: {health.get('relay_available')}",
            f"Ollama available: {health.get('ollama_available')}",
            f"Pending drafts: {len(list_drafts_dict())}",
        ]
    )


async def handle_natural_approval(update, context, text: str, owner_id: int) -> bool:
    user_id = getattr(update.effective_user, "id", None)
    if user_id != owner_id:
        return False
    normalized = (text or "").strip().lower()
    draft_id = None
    match = re.search(r"\b([a-f0-9]{8})\b", normalized)
    if match:
        draft_id = match.group(1)
    if normalized in _APPROVAL_PHRASES or "approve" in normalized or "apply" in normalized:
        await update.message.reply_text(approve_upgrade(_state(), draft_id))
        return True
    return False


async def handle_code_request(update, context, intent: dict, owner_id: int):
    await update.message.reply_text("The governed upgrade pipeline is now handled directly by the Telegram application layer.")


async def maybe_handle_code_after_reply(update, context, text: str, owner_id: int) -> None:
    return None
