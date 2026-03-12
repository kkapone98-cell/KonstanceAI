"""Natural-language intent parsing for Telegram-first control."""

from __future__ import annotations

import re

from core.contracts import IntentResult


def _extract_target(text: str) -> str | None:
    match = re.search(r"([\w./\\-]+\.(?:py|ps1|cmd|bat|json|txt|md))", text, re.IGNORECASE)
    return match.group(1) if match else None


def parse_intent(text: str) -> IntentResult:
    raw = (text or "").strip()
    lower = raw.lower()
    target = _extract_target(raw)

    if re.search(r"^/(start|help)$", lower):
        return IntentResult(name="help")
    if re.search(r"^/(status|health)\b", lower) or re.search(r"\b(status|health|alive|running)\b", lower):
        return IntentResult(name="status", requires_owner=False)
    if re.search(r"^/(drafts)\b", lower) or "show drafts" in lower or "pending drafts" in lower:
        return IntentResult(name="show_drafts", requires_owner=True)
    if re.search(r"^/(approve)\b", lower) or re.search(r"\b(approve|apply|go ahead|ship it)\b", lower):
        draft_match = re.search(r"\b([a-f0-9]{8})\b", lower)
        return IntentResult(
            name="approve_upgrade",
            requires_owner=True,
            entities={"draft_id": draft_match.group(1) if draft_match else None},
        )
    if re.search(r"^/(reject)\b", lower) or re.search(r"\b(reject|discard|cancel draft)\b", lower):
        draft_match = re.search(r"\b([a-f0-9]{8})\b", lower)
        return IntentResult(
            name="reject_upgrade",
            requires_owner=True,
            entities={"draft_id": draft_match.group(1) if draft_match else None},
        )
    if re.search(r"^/(rollback)\b", lower) or re.search(r"\brollback\b", lower):
        return IntentResult(name="rollback_upgrade", requires_owner=True, entities={"target": target})
    if re.search(r"^/(goals)\b", lower) or re.search(r"\b(goals|mission|capabilities|what can you do)\b", lower):
        return IntentResult(name="show_goals", requires_owner=False)
    if re.search(r"^/run\b", lower) or re.search(r"\b(run|execute)\b.*\b(command|script)\b", lower):
        cmd = re.sub(r"^/run\s*", "", raw, flags=re.IGNORECASE).strip()
        return IntentResult(name="run_local_command", requires_owner=True, entities={"command": cmd})
    if re.search(r"\b(install|upgrade|fix)\b.*\b(dependenc|package|module|pip)\b", lower):
        pkg_match = re.search(r"\b([A-Za-z0-9_.\-]+)\b(?:\s*)$", raw)
        package = pkg_match.group(1) if pkg_match and pkg_match.group(1).lower() not in {"dependencies", "dependency"} else None
        return IntentResult(name="install_dependency", requires_owner=True, entities={"package": package})
    if re.search(r"^/startclean\b", lower) or re.search(r"\b(startclean|start clean|start-clean|safe start)\b", lower):
        return IntentResult(name="start_clean", requires_owner=True)
    if re.search(r"\brestart\b.*\b(bot|launcher|konstance)\b", lower):
        return IntentResult(name="restart_runtime", requires_owner=True)
    if re.search(r"\btest\b.*\bself[- ]?upgrade\b", lower):
        return IntentResult(name="self_upgrade_test", requires_owner=True)
    if re.search(r"\bdoctor\b", lower) or re.search(r"\bdiagnos(e|is)|repair\b", lower):
        return IntentResult(name="doctor", requires_owner=True)
    if re.search(r"^/setverbosity\b", lower) or re.search(r"\bverbosity\b", lower):
        level_match = re.search(r"\b(short|medium|long)\b", lower)
        return IntentResult(
            name="set_verbosity",
            requires_owner=True,
            entities={"verbosity": level_match.group(1) if level_match else None},
        )
    if re.search(r"\b(analyze|inspect|review)\b.*\b(codebase|system|project)\b", lower):
        return IntentResult(name="analyze_system", requires_owner=True)

    code_request = (
        re.search(r"\b(add|create|build|implement|fix|improve|upgrade|refactor|repair)\b", lower)
        or "self-improv" in lower
        or "modify" in lower
    )
    if code_request:
        return IntentResult(
            name="plan_upgrade",
            requires_owner=True,
            entities={"target": target, "description": raw},
        )

    return IntentResult(name="chat", requires_owner=False)

