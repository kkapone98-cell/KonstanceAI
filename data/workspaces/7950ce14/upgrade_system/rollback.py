"""Rollback support for promoted upgrade batches."""

from __future__ import annotations

import shutil
import time
from pathlib import Path

from core.config import AppConfig
from core.state import read_json, write_json


def rollback_last_promotion(config: AppConfig) -> dict[str, object]:
    ledger = read_json(config.data_dir / "upgrade_history" / "ledger.json", {"changes": []})
    if not ledger.get("changes"):
        return {"success": False, "error": "No promotions found."}

    change = ledger["changes"][-1]
    backup_root = Path(change["backup_root"])
    if not backup_root.exists():
        return {"success": False, "error": "Backup set missing."}

    restored: list[str] = []
    for backup in backup_root.rglob("*"):
        if backup.is_dir():
            continue
        target = config.root / backup.relative_to(backup_root)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(backup, target)
        restored.append(str(target.relative_to(config.root)).replace("\\", "/"))

    memory_path = config.data_dir / "memory" / "upgrades.json"
    memory = read_json(memory_path, {"upgrades": [], "knowledge": [], "fixes": []})
    memory.setdefault("upgrades", []).append(
        {
            "ts": int(time.time()),
            "event": "rolled_back",
            "plan_id": change.get("plan_id"),
            "restored_files": restored,
        }
    )
    memory["upgrades"] = memory["upgrades"][-200:]
    write_json(memory_path, memory)
    return {"success": True, "restored_files": restored, "plan_id": change.get("plan_id")}

