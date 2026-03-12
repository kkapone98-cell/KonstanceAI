"""Canonical path safety and risk policy for file mutations."""

from __future__ import annotations

from pathlib import Path


HIGH_RISK_NAMES = {"bot.py", "launcher.py", "main.py"}
ALLOWED_ROOT_FILES = {
    "START_KONSTANCE.cmd",
    "start_konstance.bat",
    "02_verify_and_test.ps1",
    "requirements.txt",
}
ALLOWED_RELATIVE_PREFIXES = (
    "ai_brain/",
    "core/",
    "doctor/",
    "launcher/",
    "konstance_telegram/",
    "self_edit/",
    "telegram/",
    "tests/",
    "upgrade_system/",
    "scripts/",
    "scripts/modules/",
)


def resolve_repo_path(root: Path, target: str | Path) -> Path:
    candidate = Path(target)
    if not candidate.is_absolute():
        candidate = (root / candidate).resolve()
    else:
        candidate = candidate.resolve()

    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"Path escapes repository root: {target}") from exc
    return candidate


def risk_level(root: Path, target: str | Path) -> str:
    resolved = resolve_repo_path(root, target)
    rel = resolved.relative_to(root).as_posix()
    if resolved.name in HIGH_RISK_NAMES:
        return "high"
    if any(rel.startswith(prefix) for prefix in ALLOWED_RELATIVE_PREFIXES):
        return "low"
    return "high"


def is_upgrade_allowed(root: Path, target: str | Path) -> bool:
    resolved = resolve_repo_path(root, target)
    rel = resolved.relative_to(root).as_posix()
    if resolved.name in HIGH_RISK_NAMES or resolved.name in ALLOWED_ROOT_FILES:
        return True
    return any(rel.startswith(prefix) for prefix in ALLOWED_RELATIVE_PREFIXES)

