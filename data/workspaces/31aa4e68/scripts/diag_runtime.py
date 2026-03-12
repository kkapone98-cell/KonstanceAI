import json, pathlib, time

ROOT = pathlib.Path(r"C:\Users\Thinkpad\Desktop\KonstanceAI")
DATA = ROOT / "data"
OUT = DATA / "diag_last.json"


def load(path, default):
    try:
        raw = path.read_text(encoding="utf-8-sig") if path.exists() else ""
        return json.loads(raw) if raw.strip() else default
    except Exception:
        return default


def exists(p):
    return p.exists()


def main():
    status = {
        "ts": int(time.time()),
        "bot_py": exists(ROOT / "bot.py"),
        "jobs_db": exists(DATA / "jobs.json"),
        "tasks_db": exists(DATA / "tasks.json"),
        "money_memory": exists(DATA / "money_memory.json"),
        "router_cfg": exists(DATA / "router.json"),
        "control_policy": exists(DATA / "control_policy.json"),
        "cloud_cfg": bool((ROOT / ".env").exists()),
        "notes": []
    }

    if not status["jobs_db"]:
        status["notes"].append("jobs.json missing")
    if not status["tasks_db"]:
        status["notes"].append("tasks.json missing")

    OUT.write_text(json.dumps(status, indent=2), encoding="utf-8")
    print(json.dumps(status, indent=2))


if __name__ == "__main__":
    main()
