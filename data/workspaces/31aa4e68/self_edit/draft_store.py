"""Storage for pending upgrade drafts and approval records."""

from __future__ import annotations

import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from core.state import read_json, write_json


@dataclass(slots=True)
class DraftRecord:
    draft_id: str
    user_id: int
    description: str
    workspace: str
    target_hint: str
    diff_summary: str
    created_at: int = field(default_factory=lambda: int(time.time()))
    status: str = "pending"
    metadata: dict[str, Any] = field(default_factory=dict)


class DraftStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        if not self.path.exists():
            write_json(self.path, {"drafts": {}})

    def list(self) -> dict[str, dict[str, Any]]:
        return read_json(self.path, {"drafts": {}}).get("drafts", {})

    def get(self, draft_id: str) -> dict[str, Any] | None:
        return self.list().get(draft_id)

    def create(self, user_id: int, description: str, workspace: Path, target_hint: str, diff_summary: str, metadata: dict[str, Any] | None = None) -> DraftRecord:
        draft = DraftRecord(
            draft_id=str(uuid.uuid4())[:8],
            user_id=user_id,
            description=description,
            workspace=str(workspace),
            target_hint=target_hint,
            diff_summary=diff_summary,
            metadata=metadata or {},
        )
        payload = read_json(self.path, {"drafts": {}})
        payload.setdefault("drafts", {})[draft.draft_id] = asdict(draft)
        write_json(self.path, payload)
        return draft

    def delete(self, draft_id: str) -> None:
        payload = read_json(self.path, {"drafts": {}})
        payload.setdefault("drafts", {}).pop(draft_id, None)
        write_json(self.path, payload)

