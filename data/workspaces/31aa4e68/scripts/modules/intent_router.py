"""Compatibility bridge from legacy code intents to the new parser."""

from __future__ import annotations

from ai_brain.intent_parser import parse_intent
from core.config import load_config
from self_edit.file_policy import risk_level


def parse_code_request(text: str, history: list | None = None) -> dict:
    intent = parse_intent(text)
    if intent.name == "chat":
        return {"is_code_request": False, "action": "none", "target_hint": "unknown", "description": "", "risk": "unknown"}

    action_map = {
        "show_goals": "show_goals",
        "show_drafts": "show_drafts",
        "status": "show_status",
        "rollback_upgrade": "rollback",
        "plan_upgrade": "improve",
    }
    target = intent.entities.get("target") or "unknown"
    risk = "high"
    if target != "unknown":
        risk = risk_level(load_config().root, target)

    return {
        "is_code_request": intent.name != "chat",
        "action": action_map.get(intent.name, "add_feature"),
        "target_hint": target,
        "description": intent.entities.get("description") or text[:200],
        "risk": risk,
    }
