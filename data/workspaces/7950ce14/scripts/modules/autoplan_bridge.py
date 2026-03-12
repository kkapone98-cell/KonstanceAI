import json
import pathlib

ROOT = pathlib.Path(r"C:\Users\Thinkpad\Desktop\KonstanceAI")


def run_autoplan_goal(goal_text: str):
    """
    Applies an autoplan goal and returns (code, message).
    Wraps scripts/autoplan_engine.py logic to keep bot import paths stable.
    """
    goal_text = (goal_text or "").strip()
    if not goal_text:
        return 2, "Missing goal text"
    try:
        from scripts.autoplan_engine import apply_goal
    except Exception as e:
        return 3, f"autoplan_engine import failed: {e}"
    ok, result = apply_goal(goal_text)
    return (0 if ok else 2), json.dumps({"ok": ok, "result": result}, indent=2)

