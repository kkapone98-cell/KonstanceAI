"""
scripts/modules/goal_engine.py
Konstance self-improving goal tracker.
Marks goals achieved, logs improvements, generates next targets via LLM.
"""
import json, time, logging
from pathlib import Path

logger       = logging.getLogger(__name__)
ROOT         = Path(__file__).parent.parent.parent
GOALS_PATH   = ROOT / "data" / "goals.json"
CAP_LOG_PATH = ROOT / "data" / "capability_log.json"


def _load() -> dict:
    try:
        if GOALS_PATH.exists():
            return json.loads(GOALS_PATH.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {"active": [], "achieved": [], "version": 1}


def _save(d: dict):
    GOALS_PATH.parent.mkdir(parents=True, exist_ok=True)
    GOALS_PATH.write_text(json.dumps(d, indent=2), encoding="utf-8")


def _log_improvement(description: str, target_file: str):
    try:
        data = {"entries": [], "total_improvements": 0, "last_improvement": None}
        if CAP_LOG_PATH.exists():
            data = json.loads(CAP_LOG_PATH.read_text(encoding="utf-8"))
        entry = {
            "timestamp": int(time.time()),
            "description": description,
            "target": target_file,
            "ts_human": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        data["entries"].append(entry)
        data["total_improvements"] = len(data["entries"])
        data["last_improvement"] = entry["ts_human"]
        CAP_LOG_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception as e:
        logger.warning(f"Could not log improvement: {e}")


def get_active_goals() -> list:
    return _load().get("active", [])


def mark_achieved(goal_id: str, evidence: str = ""):
    d = _load()
    for g in d["active"]:
        if g["id"] == goal_id:
            g["status"] = "achieved"
            g["achieved_at"] = int(time.time())
            g["evidence"] = evidence
            d.setdefault("achieved", []).append(g)
            d["active"] = [x for x in d["active"] if x["id"] != goal_id]
            _save(d)
            return True
    return False


def add_goal(goal_text: str, priority: str = "medium") -> str:
    d = _load()
    existing = [g["goal"].lower() for g in d["active"] + d.get("achieved", [])]
    if goal_text.lower() in existing:
        return ""
    import uuid
    gid = "g" + str(int(time.time()))[-4:]
    d["active"].append({
        "id": gid,
        "goal": goal_text,
        "priority": priority,
        "status": "pending",
        "created_at": int(time.time()),
        "achieved_at": None,
        "evidence": None
    })
    _save(d)
    return gid


def on_capability_added(description: str, target_file: str) -> str:
    """
    Called after every successful self-edit.
    Logs the improvement, checks if any goal was achieved,
    calls LLM to suggest next goal.
    Returns the new suggested goal text (or empty string).
    """
    _log_improvement(description, target_file)

    # Auto-match against active goals by keyword overlap
    d = _load()
    desc_lower = description.lower()
    for g in d["active"]:
        keywords = [w for w in g["goal"].lower().split() if len(w) > 4]
        if sum(1 for k in keywords if k in desc_lower) >= 2:
            mark_achieved(g["id"], evidence=f"Auto-matched: {description}")
            logger.info(f"Goal achieved: {g['goal']}")
            break

    # Ask LLM to suggest next goal
    return _suggest_next_goal(description)


def _suggest_next_goal(last_improvement: str) -> str:
    d = _load()
    active = [g["goal"] for g in d["active"] if g["status"] == "pending"]
    achieved = [g["goal"] for g in d.get("achieved", [])]

    try:
        from scripts.modules.smart_reply_engine import _try_ollama, _try_openclaw
        prompt = (
            "You are the goal planner for Konstance, a self-improving Telegram AI assistant "
            "that generates financial outcomes for Xavier.\n\n"
            f"LAST IMPROVEMENT: {last_improvement}\n\n"
            f"ALREADY ACHIEVED:\n" + "\n".join(f"- {g}" for g in achieved[-5:]) + "\n\n"
            f"STILL ACTIVE:\n" + "\n".join(f"- {g}" for g in active[:5]) + "\n\n"
            "Suggest ONE specific, actionable next capability Konstance should build. "
            "It must be something new, financially useful, and buildable in Python. "
            "Reply with ONLY the goal in one sentence. No explanation."
        )
        msgs = [{"role": "user", "content": prompt}]
        suggestion = None
        for fn in [_try_openclaw, _try_ollama]:
            try:
                r = fn(messages=msgs)
                if r and len(r.strip()) > 10:
                    suggestion = r.strip().splitlines()[0].strip()
                    break
            except Exception:
                continue
        if suggestion:
            add_goal(suggestion, priority="medium")
            return suggestion
    except Exception as e:
        logger.warning(f"Goal suggestion failed: {e}")
    return ""


def goals_summary() -> str:
    d = _load()
    active   = d.get("active", [])
    achieved = d.get("achieved", [])
    lines = [f"🎯 *Goals* ({len(achieved)} achieved, {len(active)} active)\n"]
    for g in active[:8]:
        icon = "🔄" if g["status"] == "in_progress" else "⏳"
        lines.append(f"{icon} {g['goal']}")
    if achieved:
        lines.append(f"\n✅ *Achieved:*")
        for g in achieved[-3:]:
            lines.append(f"✓ {g['goal']}")
    return "\n".join(lines)
