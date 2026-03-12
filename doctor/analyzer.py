"""Runtime diagnostics derived from logs, health state, and upgrade reports."""

from __future__ import annotations

from pathlib import Path

from core.contracts import DoctorReport
from core.state import RuntimeState, read_json


def _read_tail(path: Path, limit: int = 4000) -> str:
    if not path.exists():
        return ""
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""
    return text[-limit:]


def analyze_runtime(state: RuntimeState) -> DoctorReport:
    health = state.load_health()
    findings: list[str] = []
    suggestions: list[str] = []

    if not health.get("ollama_available"):
        findings.append("Ollama fallback is currently unavailable.")
        suggestions.append("Start or repair the Ollama local service.")
    if health.get("relay_available") is False:
        findings.append("OpenClaw relay is currently unavailable.")
        suggestions.append("Verify the relay URL and relay health endpoint.")
    if health.get("quarantined"):
        findings.append("Launcher restart quarantine is active due to repeated crashes.")
        suggestions.append("Run doctor diagnostics before attempting another restart.")

    bot_log = _read_tail(state.config.logs_dir / "bot.log")
    if "Traceback" in bot_log or "ERROR" in bot_log:
        findings.append("Recent bot log contains errors or tracebacks.")
        suggestions.append("Inspect the most recent traceback and validate the affected module.")

    reports = read_json(state.doctor_reports_path, {"reports": []}).get("reports", [])
    metadata = {
        "health": health,
        "latest_log_excerpt": bot_log,
        "recent_reports": reports[-3:],
    }
    summary = "System looks healthy." if not findings else "Doctor found issues that need attention."
    return DoctorReport(ok=not findings, summary=summary, findings=findings, suggested_actions=suggestions, metadata=metadata)

