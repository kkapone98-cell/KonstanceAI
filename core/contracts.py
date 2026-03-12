"""Structured contracts shared across transport, cognition, and upgrades."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class IntentResult:
    name: str
    confidence: float = 1.0
    entities: dict[str, Any] = field(default_factory=dict)
    requires_owner: bool = False


@dataclass(slots=True)
class MessageContext:
    user_id: int
    text: str
    channel: str = "telegram"
    is_owner: bool = False


@dataclass(slots=True)
class MessageResponse:
    text: str
    followups: list[str] = field(default_factory=list)
    pending_action_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class UpgradePlan:
    plan_id: str
    description: str
    requested_by: int
    intent_name: str
    target_hint: str | None = None
    workspace: Path | None = None
    validation_required: bool = True
    approval_required: bool = True
    status: str = "planned"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ValidationReport:
    ok: bool
    summary: str
    steps: list[dict[str, Any]] = field(default_factory=list)
    workspace: Path | None = None


@dataclass(slots=True)
class DoctorReport:
    ok: bool
    summary: str
    findings: list[str] = field(default_factory=list)
    suggested_actions: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

