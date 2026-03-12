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
    run_self_upgrade_smoke,
    summarize_upgrade_history,
)
from ai_brain.task_planner import select_workflow
from ai_brain.memory_manager import MemoryManager
from core.config import AppConfig
from core.contracts import MessageContext, MessageResponse
from core.state import RuntimeState
from scripts.modules.goal_engine import goals_summary
from scripts.modules.smart_reply_engine import ollama_fallback_available, relay_available
from scripts.modules.safe_executor import execute_owner_command, install_dependency


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
        relay_detail = "Relay reachable."
        if not health.get("relay_available"):
            if self.config.openclaw_cmd:
                relay_detail = "Relay unavailable. OPENCLAW_CMD is configured, but the relay is not responding."
            else:
                relay_detail = (
                    "Relay unavailable. OPENCLAW_CMD is not configured, so launcher cannot auto-start OpenClaw."
                )
        return "\n".join(
            [
                "Status: running",
                f"Root: {self.config.root}",
                f"Relay available: {health.get('relay_available')}",
                f"Relay detail: {relay_detail}",
                f"Ollama available: {health.get('ollama_available')}",
                f"Local model: {self.config.local_llm_model}",
                f"Restart count: {health.get('restart_count', 0)}",
                summarize_upgrade_history(self.state),
            ]
        )

    def _report_text(self) -> str:
        """Full system snapshot: launcher path, OpenClaw health, LLM, self-upgrade status, errors."""
        root = str(self.config.root)
        launcher_path = str(self.config.root / "launcher.py")
        health = self.state.update_health(
            relay_available=relay_available(),
            ollama_available=ollama_fallback_available(),
            last_message=int(time.time()),
        )
        relay_ok = health.get("relay_available", False)
        ollama_ok = health.get("ollama_available", False)
        relay_url = self.config.openclaw_relay_url or "ws://127.0.0.1:18789"
        relay_http = relay_url.replace("ws://", "http://").replace("wss://", "https://").rstrip("/")
        lines = [
            "Report - KonstanceAI",
            f"Launcher: {launcher_path}",
            f"Root: {root}",
            f"OpenClaw relay: {relay_http}/health",
            f"Relay available: {relay_ok}",
            f"Local LLM (Ollama): {ollama_ok}",
            f"Local model: {self.config.local_llm_model}",
            f"Restart count: {health.get('restart_count', 0)}",
            summarize_upgrade_history(self.state),
        ]
        return "\n".join(lines)

    def _failure_response(self, text: str) -> MessageResponse:
        return MessageResponse(
            text=text,
            metadata={
                "owner_alert": True,
                "owner_alert_text": f"Konstance operation failed: {text}",
            },
        )

    def handle_user_message(self, context: MessageContext) -> MessageResponse:
        intent = parse_intent(context.text)
        if intent.requires_owner and not context.is_owner:
            return MessageResponse(text="Not authorized for that action.")

        workflow = select_workflow(intent)
        self.state.update_health(last_message=int(time.time()))

        if workflow == "operations":
            if intent.name == "report":
                return MessageResponse(text=self._report_text())
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
            if intent.name == "run_local_command":
                result = execute_owner_command(self.config, intent.entities.get("command") or context.text)
                if not result.get("ok"):
                    return self._failure_response(f"Command failed: {result.get('error') or result.get('output')}")
                return MessageResponse(
                    text=f"Command succeeded (code {result.get('returncode', 0)}).\n{result.get('output', '')}"
                )
            if intent.name == "install_dependency":
                result = install_dependency(self.config, intent.entities.get("package"))
                if not result.get("ok"):
                    return self._failure_response(
                        f"Dependency install failed: {result.get('error') or result.get('output')}"
                    )
                return MessageResponse(text=f"Dependency install completed.\n{result.get('output', '')}")
            if intent.name == "restart_runtime":
                result = execute_owner_command(self.config, "python launcher.py --restart --once")
                if not result.get("ok"):
                    return self._failure_response(
                        f"Restart command failed: {result.get('error') or result.get('output')}"
                    )
                return MessageResponse(text="Restart command dispatched via launcher.")
            if intent.name == "start_clean":
                result = execute_owner_command(self.config, "python launcher.py --start-clean --once")
                if not result.get("ok"):
                    return self._failure_response(
                        f"Start-clean command failed: {result.get('error') or result.get('output')}"
                    )
                return MessageResponse(text="Start-clean command dispatched via launcher.")
            if intent.name == "self_upgrade_test":
                result = run_self_upgrade_smoke(self.state, context.user_id)
                if "failed" in result.lower():
                    return self._failure_response(result)
                return MessageResponse(text=result)

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
                    "Konstance can chat, /report (full system snapshot), /status, run doctor diagnostics, "
                    "list drafts, plan safe upgrades, approve validated drafts, roll back the last promotion, "
                    "run owner-safe local commands, and install dependencies."
                )
            )

        reply = generate_reply(self.state, context.text)
        self.memory.append(context.text, reply)
        return MessageResponse(text=reply)

