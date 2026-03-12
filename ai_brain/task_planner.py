"""Map parsed intents to executable workflows."""

from __future__ import annotations

from core.contracts import IntentResult


def select_workflow(intent: IntentResult) -> str:
    if intent.name in {"status", "report", "show_drafts", "approve_upgrade", "reject_upgrade", "rollback_upgrade"}:
        return "operations"
    if intent.name in {"run_local_command", "install_dependency", "restart_runtime", "start_clean", "self_upgrade_test"}:
        return "operations"
    if intent.name in {"doctor"}:
        return "doctor"
    if intent.name in {"plan_upgrade"}:
        return "upgrade"
    if intent.name in {"show_goals", "analyze_system"}:
        return "analysis"
    if intent.name in {"set_verbosity"}:
        return "preferences"
    return "chat"

