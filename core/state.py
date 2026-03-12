"""Persistent JSON-backed state helpers."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from core.config import AppConfig


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


@dataclass(slots=True)
class RuntimeState:
    config: AppConfig

    @property
    def prefs_path(self) -> Path:
        return self.config.data_dir / "prefs.json"

    @property
    def profile_path(self) -> Path:
        return self.config.data_dir / "profile.json"

    @property
    def memory_path(self) -> Path:
        return self.config.data_dir / "memory.json"

    @property
    def health_path(self) -> Path:
        return self.config.data_dir / "health.json"

    @property
    def drafts_path(self) -> Path:
        return self.config.data_dir / "pending_edits.json"

    @property
    def upgrade_plans_path(self) -> Path:
        return self.config.data_dir / "upgrade_history" / "plans.json"

    @property
    def change_ledger_path(self) -> Path:
        return self.config.data_dir / "upgrade_history" / "ledger.json"

    @property
    def doctor_reports_path(self) -> Path:
        return self.config.data_dir / "doctor" / "reports.json"

    @property
    def restart_state_path(self) -> Path:
        return self.config.data_dir / "doctor" / "restart_state.json"

    @property
    def upgrades_memory_path(self) -> Path:
        return self.config.data_dir / "memory" / "upgrades.json"

    def ensure(self) -> None:
        defaults = {
            self.prefs_path: {"verbosity": "medium"},
            self.profile_path: {"name": "Konstance"},
            self.memory_path: {"conversations": []},
            self.health_path: {
                "last_start": 0,
                "last_message": 0,
                "relay_available": False,
                "ollama_available": False,
                "restart_count": 0,
            },
            self.drafts_path: {"drafts": {}},
            self.upgrade_plans_path: {"plans": []},
            self.change_ledger_path: {"changes": []},
            self.doctor_reports_path: {"reports": []},
            self.restart_state_path: {"window_started_at": 0, "recent_restart_times": [], "quarantined": False},
            self.upgrades_memory_path: {"upgrades": [], "knowledge": [], "fixes": []},
        }
        for path, payload in defaults.items():
            if not path.exists():
                write_json(path, payload)

    def load_memory(self) -> list[dict[str, Any]]:
        return read_json(self.memory_path, {"conversations": []}).get("conversations", [])

    def save_memory(self, conversations: list[dict[str, Any]], max_items: int = 30) -> None:
        write_json(self.memory_path, {"conversations": conversations[-max_items:]})

    def load_prefs(self) -> dict[str, Any]:
        return read_json(self.prefs_path, {"verbosity": "medium"})

    def save_prefs(self, prefs: dict[str, Any]) -> None:
        write_json(self.prefs_path, prefs)

    def load_profile(self) -> dict[str, Any]:
        return read_json(self.profile_path, {"name": "Konstance"})

    def load_health(self) -> dict[str, Any]:
        return read_json(
            self.health_path,
            {"last_start": 0, "last_message": 0, "relay_available": False, "ollama_available": False},
        )

    def update_health(self, **updates: Any) -> dict[str, Any]:
        payload = self.load_health()
        payload.update(updates)
        payload["updated_at"] = int(time.time())
        write_json(self.health_path, payload)
        return payload

    def load_upgrade_memory(self) -> dict[str, Any]:
        return read_json(self.upgrades_memory_path, {"upgrades": [], "knowledge": [], "fixes": []})

    def log_upgrade_event(self, event: dict[str, Any]) -> None:
        payload = self.load_upgrade_memory()
        payload.setdefault("upgrades", []).append(event)
        payload["upgrades"] = payload["upgrades"][-200:]
        write_json(self.upgrades_memory_path, payload)

