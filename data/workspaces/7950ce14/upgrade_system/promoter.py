"""Promote validated workspace changes to the live repository."""

from __future__ import annotations

import filecmp
import shutil
import time
from pathlib import Path

from core.config import AppConfig
from core.state import read_json, write_json
from self_edit.file_policy import is_upgrade_allowed, resolve_repo_path


def _iter_changed_files(live_root: Path, workspace: Path) -> list[tuple[Path, Path]]:
    changed: list[tuple[Path, Path]] = []
    for source in workspace.rglob("*"):
        if source.is_dir():
            continue
        rel = source.relative_to(workspace)
        target = live_root / rel
        if not target.exists() or not filecmp.cmp(source, target, shallow=False):
            changed.append((source, target))
    return changed


def promote_workspace(config: AppConfig, workspace: Path, plan_id: str) -> dict[str, object]:
    changed = []
    backup_root = config.root / "backups" / "promotions" / f"{plan_id}_{int(time.time())}"
    backup_root.mkdir(parents=True, exist_ok=True)

    for source, target in _iter_changed_files(config.root, workspace):
        if not is_upgrade_allowed(config.root, target):
            continue
        target = resolve_repo_path(config.root, target)
        if target.exists():
            backup_path = backup_root / target.relative_to(config.root)
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, backup_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        changed.append(str(target.relative_to(config.root)).replace("\\", "/"))

    ledger = read_json(config.data_dir / "upgrade_history" / "ledger.json", {"changes": []})
    ledger.setdefault("changes", []).append(
        {
            "plan_id": plan_id,
            "changed_files": changed,
            "backup_root": str(backup_root),
            "promoted_at": int(time.time()),
        }
    )
    write_json(config.data_dir / "upgrade_history" / "ledger.json", ledger)
    memory_path = config.data_dir / "memory" / "upgrades.json"
    memory = read_json(memory_path, {"upgrades": [], "knowledge": [], "fixes": []})
    memory.setdefault("upgrades", []).append(
        {
            "ts": int(time.time()),
            "event": "promoted",
            "plan_id": plan_id,
            "changed_files": changed,
        }
    )
    memory["upgrades"] = memory["upgrades"][-200:]
    write_json(memory_path, memory)
    return {"success": True, "changed_files": changed, "backup_root": str(backup_root)}

