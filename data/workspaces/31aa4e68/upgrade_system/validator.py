"""Validation pipeline for sandboxed upgrades."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from core.config import AppConfig
from core.contracts import ValidationReport


def _run_step(command: list[str], cwd: Path, env: dict[str, str], label: str) -> dict[str, object]:
    proc = subprocess.run(command, cwd=str(cwd), env=env, capture_output=True, text=True)
    output = ((proc.stdout or "") + "\n" + (proc.stderr or "")).strip()
    return {
        "label": label,
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "output": output[:12000],
    }


def validate_workspace(config: AppConfig, workspace: Path) -> ValidationReport:
    env = os.environ.copy()
    env["KONSTANCE_ROOT"] = str(workspace)
    compile_targets = [
        "bot.py",
        "main.py",
        "launcher.py",
        "agents",
        "ai_brain",
        "core",
        "doctor",
        "konstance_telegram",
        "launcher",
        "scripts/modules",
        "scripts/__init__.py",
        "self_edit",
        "tests",
        "tools",
        "upgrade_system",
    ]

    steps = [
        _run_step(
            [config.python_executable, "-m", "compileall", "-q", *compile_targets],
            workspace,
            env,
            "syntax",
        ),
        _run_step(
            [config.python_executable, "-c", "import bot; print('BOT_IMPORT_OK')"],
            workspace,
            env,
            "import-smoke",
        ),
        _run_step(
            [
                config.python_executable,
                "-c",
                "from core.config import load_config; from konstance_telegram.adapter import build_application; cfg=load_config(); app=build_application(cfg); print(type(app).__name__)",
            ],
            workspace,
            env,
            "telegram-build",
        ),
        _run_step(
            [config.python_executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
            workspace,
            env,
            "tests",
        ),
    ]

    ok = all(step["ok"] for step in steps)
    summary = "Validation passed." if ok else "Validation failed."
    return ValidationReport(ok=ok, summary=summary, steps=steps, workspace=workspace)

