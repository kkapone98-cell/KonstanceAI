"""Create isolated workspaces for upgrade validation."""

from __future__ import annotations

import shutil
from pathlib import Path

from core.config import AppConfig
from core.contracts import UpgradePlan


IGNORE_DIR_NAMES = {
    ".git",
    ".idea",
    ".cursor",
    ".venv",
    "__pycache__",
    "backups",
    "build",
    "dist",
    "logs",
}

IGNORE_FILE_SUFFIXES = (
    ".bak",
    ".pyc",
    ".log",
)


def _ignore(path: str, names: list[str]) -> set[str]:
    rel = Path(path).as_posix().replace("\\", "/")
    ignored: set[str] = set()
    for name in names:
        if name in IGNORE_DIR_NAMES:
            ignored.add(name)
        # Avoid recursively cloning generated workspaces into new workspaces.
        if rel.endswith("/data") and name in {"workspaces"}:
            ignored.add(name)
        if any(name.endswith(suffix) for suffix in IGNORE_FILE_SUFFIXES):
            ignored.add(name)
    return ignored


def create_workspace(config: AppConfig, plan: UpgradePlan) -> Path:
    workspaces_root = config.data_dir / "workspaces"
    workspaces_root.mkdir(parents=True, exist_ok=True)
    workspace = workspaces_root / plan.plan_id
    if workspace.exists():
        shutil.rmtree(workspace)
    shutil.copytree(config.root, workspace, ignore=_ignore)
    return workspace

