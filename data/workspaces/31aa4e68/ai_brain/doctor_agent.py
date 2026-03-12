"""Doctor workflow entrypoints."""

from __future__ import annotations

from core.state import RuntimeState
from doctor.analyzer import analyze_runtime
from doctor.recovery import persist_report


def run_doctor(state: RuntimeState) -> str:
    report = analyze_runtime(state)
    persist_report(state, report)
    lines = [report.summary]
    if report.findings:
        lines.append("")
        lines.extend(f"- {item}" for item in report.findings)
    if report.suggested_actions:
        lines.append("")
        lines.append("Suggested actions:")
        lines.extend(f"- {item}" for item in report.suggested_actions)
    return "\n".join(lines)

