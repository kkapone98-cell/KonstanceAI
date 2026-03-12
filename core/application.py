"""Transport-agnostic application service for KonstanceAI."""

from __future__ import annotations

import time

from ai_brain.assistant_service import generate_reply
from ai_brain.code_analysis_agent import summarize_system
from ai_brain.doctor_agent import run_doctor
from ai_brain.intent_parser import parse_intent
from ai_brain.self_upgrade_agent import (
    approve_upgrade,
    latest_diff,
    list_drafts,
    plan_upgrade_request,
    reject_upgrade,
    rollback_upgrade,
    summarize_upgrade_history,
)
from ai_brain.task_planner import select_workflow
from ai_brain.memory_manager import MemoryManager
from core.config import AppConfig
from core.contracts import MessageContext, MessageResponse
from core.state import RuntimeState
from scripts.modules.goal_engine import goals_summary
from scripts.modules.smart_reply_engine import ollama_fallback_available, relay_available


class KonstanceApplication:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.state = RuntimeState(config)
        self.state.ensure()
        self.memory = MemoryManager(self.state)

    def _status_text(self) -> str:
        health = self.state.update_health(
            relay_available=relay_available(),
            ollama_available=ollama_fallback_available(),
            last_message=int(time.time()),
        )
        return "\n".join(
            [
                "Status: running",
                f"Root: {self.config.root}",
                f"Relay available: {health.get('relay_available')}",
                f"Ollama available: {health.get('ollama_available')}",
                f"Restart count: {health.get('restart_count', 0)}",
                summarize_upgrade_history(self.state),
            ]
        )

    def handle_user_message(self, context: MessageContext) -> MessageResponse:
        intent = parse_intent(context.text)
        if intent.requires_owner and not context.is_owner:
            return MessageResponse(text="Not authorized for that action.")

        workflow = select_workflow(intent)
        self.state.update_health(last_message=int(time.time()))

        if workflow == "operations":
            if intent.name == "status":
                return MessageResponse(text=self._status_text())
            if intent.name == "show_drafts":
                drafts_text = list_drafts(self.state)
                followups = []
                if "No pending" not in drafts_text:
                    followups.append(latest_diff(self.state))
                return MessageResponse(text=drafts_text, followups=followups)
            if intent.name == "approve_upgrade":
                return MessageResponse(text=approve_upgrade(self.state, intent.entities.get("draft_id")))
            if intent.name == "reject_upgrade":
                return MessageResponse(text=reject_upgrade(self.state, intent.entities.get("draft_id")))
            if intent.name == "rollback_upgrade":
                return MessageResponse(text=rollback_upgrade(self.state))

        if workflow == "doctor":
            return MessageResponse(text=run_doctor(self.state))

        if workflow == "analysis":
            if intent.name == "show_goals":
                return MessageResponse(text=goals_summary())
            return MessageResponse(text=summarize_system(self.state))

        if workflow == "preferences":
            verbosity = intent.entities.get("verbosity")
            if verbosity not in {"short", "medium", "long"}:
                return MessageResponse(text="Usage: set verbosity to short, medium, or long.")
            prefs = self.state.load_prefs()
            prefs["verbosity"] = verbosity
            self.state.save_prefs(prefs)
            return MessageResponse(text=f"Verbosity updated to `{verbosity}`.")

        if workflow == "upgrade":
            result = plan_upgrade_request(
                self.state,
                user_id=context.user_id,
                description=intent.entities.get("description") or context.text,
                target_hint=intent.entities.get("target"),
            )
            return MessageResponse(text=result)

        if intent.name == "help":
            return MessageResponse(
                text=(
                    "Konstance can chat, report status, run doctor diagnostics, list drafts, "
                    "plan safe upgrades, approve validated drafts, and roll back the last promotion."
                )
            )

        reply = generate_reply(self.state, context.text)
        self.memory.append(context.text, reply)
        return MessageResponse(text=reply)

