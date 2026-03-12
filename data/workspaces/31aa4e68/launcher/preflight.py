"""Preflight checks for the one-click launcher."""

from __future__ import annotations

import importlib
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.config import load_config


@dataclass(slots=True)
class PreflightResult:
    ok: bool
    summary: str
    details: dict


def run_preflight() -> PreflightResult:
    config = load_config()
    config.ensure_runtime_dirs()
    missing = []

    if not config.token or ":" not in config.token:
        missing.append("TELEGRAM_BOT_TOKEN")
    if not config.has_owner:
        missing.append("OWNER_ID")

    dependency_errors = []
    for module_name in ("telegram", "dotenv", "requests"):
        try:
            importlib.import_module(module_name)
        except Exception as exc:
            dependency_errors.append(f"{module_name}: {exc}")

    ok = not missing and not dependency_errors
    summary = "Preflight passed." if ok else "Preflight failed."
    details = {
        "python_executable": config.python_executable,
        "missing_settings": missing,
        "dependency_errors": dependency_errors,
        "root": str(config.root),
    }
    return PreflightResult(ok=ok, summary=summary, details=details)


if __name__ == "__main__":
    import json

    result = run_preflight()
    print(json.dumps(asdict(result), indent=2))
    raise SystemExit(0 if result.ok else 1)

