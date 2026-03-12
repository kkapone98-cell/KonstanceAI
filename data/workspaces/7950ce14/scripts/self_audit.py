import json, pathlib, re

ROOT = pathlib.Path(r"C:\Users\Thinkpad\Desktop\KonstanceAI")
BOT = ROOT / "bot.py"
SCRIPTS = ROOT / "scripts"
DATA = ROOT / "data"


def read_text(path):
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def exists(path):
    return path.exists()


def detect_commands(bot_src):
    cmds = sorted(set(re.findall(r'CommandHandler\("([a-zA-Z0-9_]+)"', bot_src)))
    return cmds


def build_audit():
    bot_src = read_text(BOT)
    cmds = detect_commands(bot_src)

    caps = []
    notes = []
    risks = []

    # Core capabilities by command presence
    if "improve" in cmds and "approve_latest" in cmds and "rollback_latest" in cmds:
        caps.append("self-improvement loop (draft/approve/rollback)")
    if "addtask" in cmds and "today" in cmds and "done" in cmds:
        caps.append("task management")
    if "agents" in cmds and "create_agent" in cmds and "run_agent" in cmds:
        caps.append("sub-agent runtime")
    if "scripts" in cmds and "create_script" in cmds and "run_script" in cmds:
        caps.append("script factory")
    if "do" in cmds and "jobs" in cmds:
        caps.append("action runner + job queue")
    if "goal" in cmds and "autoplan" in cmds:
        caps.append("goal auto-planning")
    if "health" in cmds:
        caps.append("health monitoring")
    if "purpose" in cmds or "northstar" in cmds:
        caps.append("mission awareness commands")

    # File checks
    checks = {
        "bot.py": exists(BOT),
        "scripts/agent_runtime.py": exists(SCRIPTS / "agent_runtime.py"),
        "scripts/script_factory.py": exists(SCRIPTS / "script_factory.py"),
        "scripts/action_runner.py": exists(SCRIPTS / "action_runner.py"),
        "scripts/autoplan_engine.py": exists(SCRIPTS / "autoplan_engine.py"),
        "data/mission.json": exists(DATA / "mission.json"),
        "data/router.json": exists(DATA / "router.json"),
        "data/action_policy.json": exists(DATA / "action_policy.json"),
        "data/jobs.json": exists(DATA / "jobs.json"),
        "data/tasks.json": exists(DATA / "tasks.json"),
    }

    missing = [k for k, v in checks.items() if not v]
    if missing:
        risks.append("missing critical files: " + ", ".join(missing[:6]))

    if not exists(DATA / "mission.json"):
        notes.append("mission file missing; purpose steering may be weak")
    if not exists(DATA / "action_policy.json"):
        notes.append("action policy missing; automation safety unclear")

    out = {
        "status": "ok" if not missing else "partial",
        "commands_detected": cmds,
        "capabilities": caps,
        "notes": notes,
        "risks": risks,
        "file_checks": checks
    }
    return out


def format_report(a):
    lines = []
    lines.append("Self Audit")
    lines.append(f"status: {a.get('status')}")
    lines.append("")
    lines.append("Capabilities:")
    if a.get("capabilities"):
        lines.extend([f"- {x}" for x in a["capabilities"]])
    else:
        lines.append("- none detected")
    lines.append("")
    lines.append("Risks:")
    if a.get("risks"):
        lines.extend([f"- {x}" for x in a["risks"]])
    else:
        lines.append("- none")
    lines.append("")
    lines.append("Notes:")
    if a.get("notes"):
        lines.extend([f"- {x}" for x in a["notes"]])
    else:
        lines.append("- none")
    lines.append("")
    lines.append("Top commands detected:")
    lines.append(", ".join(a.get("commands_detected", [])[:25]))
    return "\n".join(lines)


if __name__ == "__main__":
    a = build_audit()
    print(format_report(a))
