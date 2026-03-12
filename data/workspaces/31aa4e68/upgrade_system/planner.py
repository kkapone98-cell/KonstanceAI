"""Structured upgrade planning for self-improvement requests."""

from __future__ import annotations

import time
import uuid
from pathlib import Path

from core.contracts import IntentResult, UpgradePlan
from core.state import read_json, write_json


def create_plan(plans_path: Path, intent: IntentResult, user_id: int, description: str, target_hint: str | None = None) -> UpgradePlan:
    plan = UpgradePlan(
        plan_id=str(uuid.uuid4())[:8],
        description=description.strip(),
        requested_by=user_id,
        intent_name=intent.name,
        target_hint=target_hint,
        metadata={"created_at": int(time.time())},
    )
    payload = read_json(plans_path, {"plans": []})
    payload.setdefault("plans", []).append(
        {
            "plan_id": plan.plan_id,
            "description": plan.description,
            "requested_by": plan.requested_by,
            "intent_name": plan.intent_name,
            "target_hint": plan.target_hint,
            "validation_required": plan.validation_required,
            "approval_required": plan.approval_required,
            "status": plan.status,
            "metadata": plan.metadata,
        }
    )
    write_json(plans_path, payload)
    return plan

