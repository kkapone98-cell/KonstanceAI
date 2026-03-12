"""Doctor report persistence and simple recovery actions."""

from __future__ import annotations

import time

from core.contracts import DoctorReport
from core.state import RuntimeState, read_json, write_json
from doctor.monitor import clear_quarantine


def persist_report(state: RuntimeState, report: DoctorReport) -> None:
    payload = read_json(state.doctor_reports_path, {"reports": []})
    payload.setdefault("reports", []).append(
        {
            "created_at": int(time.time()),
            "ok": report.ok,
            "summary": report.summary,
            "findings": report.findings,
            "suggested_actions": report.suggested_actions,
            "metadata": report.metadata,
        }
    )
    write_json(state.doctor_reports_path, payload)


def attempt_recovery(state: RuntimeState, action: str) -> str:
    normalized = (action or "").strip().lower()
    if normalized in {"clear quarantine", "clear_quarantine", "unquarantine"}:
        clear_quarantine(state)
        return "Restart quarantine cleared."
    return "No automatic recovery action was executed."

