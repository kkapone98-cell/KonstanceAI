"""Codebase awareness helpers exposed to Telegram workflows."""

from __future__ import annotations

from core.state import RuntimeState, read_json
from scripts.modules.self_model import build_self_context


def summarize_system(state: RuntimeState) -> str:
    mission = read_json(state.config.data_dir / "mission.json", {})
    health = state.load_health()
    lines = [
        f"Mission: {mission.get('primary_goal') or mission.get('mission') or 'Not configured.'}",
        f"Owner: {mission.get('owner', 'Unknown')}",
        f"Relay available: {health.get('relay_available')}",
        f"Ollama available: {health.get('ollama_available')}",
        "",
        "Self-model excerpt:",
        build_self_context()[:2200],
    ]
    return "\n".join(lines)

