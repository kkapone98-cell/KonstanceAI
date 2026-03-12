"""Safe self-upgrade planning, validation, approval, and promotion."""

from __future__ import annotations

import shutil
import time
from pathlib import Path

from core.contracts import IntentResult
from core.state import RuntimeState, read_json
from self_edit.diff_engine import unified_diff
from self_edit.draft_store import DraftStore
from self_edit.file_policy import is_upgrade_allowed, resolve_repo_path, risk_level
from scripts.modules.self_model import build_self_context, refresh as refresh_self_model
from scripts.modules.smart_reply_engine import generate_file_update
from upgrade_system.planner import create_plan
from upgrade_system.promoter import promote_workspace
from upgrade_system.rollback import rollback_last_promotion
from upgrade_system.sandbox import create_workspace
from upgrade_system.validator import validate_workspace


def _draft_store(state: RuntimeState) -> DraftStore:
    return DraftStore(state.drafts_path)


def _resolve_target(root: Path, target_hint: str | None) -> Path | None:
    if not target_hint:
        return None
    return resolve_repo_path(root, target_hint)


def list_drafts(state: RuntimeState) -> str:
    drafts = _draft_store(state).list()
    if not drafts:
        return "No pending upgrade drafts."
    lines = ["Pending upgrade drafts:"]
    for draft_id, draft in drafts.items():
        lines.append(f"- {draft_id}: {draft.get('description', '')} [{draft.get('target_hint', 'unknown')}]")
    return "\n".join(lines)


def plan_upgrade_request(state: RuntimeState, user_id: int, description: str, target_hint: str | None) -> str:
    target_path = _resolve_target(state.config.root, target_hint)
    if not target_path:
        return "I need a target file to modify. Example: `fix bot.py` or `improve scripts/modules/smart_reply_engine.py`."
    if not is_upgrade_allowed(state.config.root, target_path):
        return "That target is outside the governed upgrade allowlist."

    intent = IntentResult(name="plan_upgrade", requires_owner=True, entities={"target": target_hint})
    plan = create_plan(state.upgrade_plans_path, intent, user_id, description, target_hint=target_hint)
    workspace = create_workspace(state.config, plan)
    plan.workspace = workspace

    workspace_target = workspace / target_path.relative_to(state.config.root)
    current_text = ""
    if workspace_target.exists():
        current_text = workspace_target.read_text(encoding="utf-8")

    new_text = generate_file_update(
        description=description,
        target_path=str(target_path.relative_to(state.config.root)).replace("\\", "/"),
        current_text=current_text,
        self_context=build_self_context(),
    )
    if not new_text.strip():
        return "Code generation failed before the sandbox draft could be created."

    workspace_target.parent.mkdir(parents=True, exist_ok=True)
    workspace_target.write_text(new_text, encoding="utf-8")
    report = validate_workspace(state.config, workspace)
    if not report.ok:
        state.log_upgrade_event(
            {
                "ts": int(time.time()),
                "event": "validation_failed",
                "plan_id": plan.plan_id,
                "target": str(target_path.relative_to(state.config.root)).replace("\\", "/"),
                "description": description,
                "failed_steps": [step["label"] for step in report.steps if not step["ok"]],
            }
        )
        return "\n".join(
            [
                "Sandbox validation failed. Live code was left untouched.",
                *[
                    f"- {step['label']}: {step['output'][:400]}"
                    for step in report.steps
                    if not step["ok"]
                ],
            ]
        )

    diff = unified_diff(
        current_text,
        new_text,
        fromfile=str(target_path.relative_to(state.config.root)).replace("\\", "/"),
        tofile=str(target_path.relative_to(state.config.root)).replace("\\", "/"),
    )
    draft = _draft_store(state).create(
        user_id=user_id,
        description=description,
        workspace=workspace,
        target_hint=str(target_path.relative_to(state.config.root)).replace("\\", "/"),
        diff_summary=diff[:8000],
        metadata={"plan_id": plan.plan_id, "risk": risk_level(state.config.root, target_path), "validation": report.summary},
    )
    state.log_upgrade_event(
        {
            "ts": int(time.time()),
            "event": "draft_validated",
            "plan_id": plan.plan_id,
            "draft_id": draft.draft_id,
            "target": draft.target_hint,
            "description": description,
        }
    )
    return (
        f"Validated upgrade draft `{draft.draft_id}` is ready for review.\n"
        f"Target: `{draft.target_hint}`\n"
        f"Risk: {draft.metadata.get('risk', 'high')}\n"
        f"Say `approve {draft.draft_id}` to promote it or `reject {draft.draft_id}` to discard it."
    )


def approve_upgrade(state: RuntimeState, draft_id: str | None) -> str:
    store = _draft_store(state)
    drafts = store.list()
    if not drafts:
        return "No pending upgrade drafts."

    if not draft_id:
        if len(drafts) != 1:
            return "Multiple drafts are pending. Please specify the draft id."
        draft_id = next(iter(drafts))

    draft = store.get(draft_id)
    if not draft:
        return f"Draft `{draft_id}` was not found."

    workspace = Path(draft["workspace"])
    result = promote_workspace(state.config, workspace, draft["metadata"]["plan_id"])
    store.delete(draft_id)
    refresh_self_model()
    return (
        f"Draft `{draft_id}` promoted successfully.\n"
        f"Changed files: {', '.join(result['changed_files']) or 'none'}\n"
        f"Backup set: {result['backup_root']}"
    )


def reject_upgrade(state: RuntimeState, draft_id: str | None) -> str:
    store = _draft_store(state)
    drafts = store.list()
    if not drafts:
        return "No pending upgrade drafts."

    if not draft_id:
        if len(drafts) != 1:
            return "Multiple drafts are pending. Please specify the draft id."
        draft_id = next(iter(drafts))

    draft = store.get(draft_id)
    if not draft:
        return f"Draft `{draft_id}` was not found."

    workspace = Path(draft["workspace"])
    if workspace.exists():
        shutil.rmtree(workspace, ignore_errors=True)
    store.delete(draft_id)
    return f"Draft `{draft_id}` was discarded."


def rollback_upgrade(state: RuntimeState) -> str:
    result = rollback_last_promotion(state.config)
    if not result.get("success"):
        return result.get("error", "Rollback failed.")
    return f"Rolled back promotion `{result['plan_id']}` for files: {', '.join(result['restored_files'])}"


def latest_diff(state: RuntimeState, draft_id: str | None = None) -> str:
    store = _draft_store(state)
    drafts = store.list()
    if not drafts:
        return "No pending upgrade drafts."
    if not draft_id:
        draft_id = next(iter(drafts))
    draft = drafts.get(draft_id)
    if not draft:
        return f"Draft `{draft_id}` was not found."
    return draft.get("diff_summary", "")[:3500] or "No diff summary recorded."


def summarize_upgrade_history(state: RuntimeState) -> str:
    ledger = read_json(state.change_ledger_path, {"changes": []}).get("changes", [])
    if not ledger:
        return "No promotions recorded yet."
    last = ledger[-1]
    files = ", ".join(last.get("changed_files", [])) or "none"
    return f"Last promoted plan `{last.get('plan_id')}` changed: {files}"

