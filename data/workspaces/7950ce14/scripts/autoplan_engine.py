import json, pathlib, time, subprocess

ROOT = pathlib.Path(r"C:\Users\Thinkpad\Desktop\KonstanceAI")
DATA = ROOT / "data"
AUTOPLAN = DATA / "autoplan.json"
TASKS = DATA / "tasks.json"
JOBS = DATA / "jobs.json"


def loadj(path, default):
    try:
        raw = path.read_text(encoding="utf-8-sig") if path.exists() else ""
        return json.loads(raw) if raw.strip() else default
    except Exception:
        return default


def savej(path, obj):
    path.write_text(json.dumps(obj, indent=2), encoding="utf-8")


def now_ts():
    return int(time.time())


def add_task(text):
    db = loadj(TASKS, {"tasks": []})
    item = {"id": f"task_{now_ts()}", "text": text, "status": "open", "created_at": now_ts(), "done_at": None}
    db["tasks"].append(item)
    savej(TASKS, db)
    return item


def queue_job(action, payload, requested_by="autoplan"):
    db = loadj(JOBS, {"jobs": []})
    job = {
        "id": f"job_{now_ts()}",
        "created_at": now_ts(),
        "action": action,
        "payload": payload,
        "requested_by": requested_by,
        "tier": "auto_allow",
        "status": "queued",
        "result": "",
        "completed_at": None
    }
    db["jobs"].append(job)
    savej(JOBS, db)
    return job


def goal_to_plan(goal_text):
    # deterministic starter decomposition (safe baseline)
    g = goal_text.strip()
    tasks = [
        f"Define objective and constraints for: {g}",
        f"Create one scout agent for: {g}",
        f"Generate one starter script for: {g}",
        f"Run scout and script once for: {g}",
        f"Review outputs and pick next best action for: {g}"
    ]
    return tasks


def apply_goal(goal_text):
    cfg = loadj(AUTOPLAN, {"enabled": True, "cloud_escalation": True, "max_tasks_per_goal": 5})
    if not cfg.get("enabled", True):
        return False, "autoplan disabled"

    max_n = int(cfg.get("max_tasks_per_goal", 5))
    plan_tasks = goal_to_plan(goal_text)[:max_n]

    created = []
    for t in plan_tasks:
        created.append(add_task(t)["id"])

    # queue starter jobs
    scout_name = "scout"
    script_name = "starter"
    j1 = queue_job("create_agent", f"{scout_name}|Research opportunities for: {goal_text}")
    j2 = queue_job("create_script", f"{script_name}|Starter script for: {goal_text}")
    j3 = queue_job("run_agent", f"{scout_name}|Find 5 actionable ideas for: {goal_text}")
    j4 = queue_job("run_script", f"{script_name}|first run for: {goal_text}")

    summary = {
        "tasks_created": len(created),
        "task_ids": created,
        "jobs_queued": [j1["id"], j2["id"], j3["id"], j4["id"]]
    }
    return True, summary


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3 or sys.argv[1].lower() != "goal":
        print("Usage: python scripts/autoplan_engine.py goal <goal text>")
        raise SystemExit(1)
    goal = " ".join(sys.argv[2:]).strip()
    ok, out = apply_goal(goal)
    print(json.dumps({"ok": ok, "result": out}, indent=2))
    raise SystemExit(0 if ok else 2)
