import json, time, pathlib, traceback
from scripts.action_runner import execute_action

ROOT = pathlib.Path(r"C:\Users\Thinkpad\Desktop\KonstanceAI")
JOBS = ROOT / "data" / "jobs.json"
LOG = ROOT / "logs" / "job-worker.log"
SLEEP_SEC = 4


def log(msg):
    line = f"[{int(time.time())}] {msg}\n"
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line)


def load_jobs():
    try:
        raw = JOBS.read_text(encoding="utf-8-sig") if JOBS.exists() else ""
        return json.loads(raw) if raw.strip() else {"jobs": []}
    except Exception:
        return {"jobs": []}


def save_jobs(db):
    JOBS.write_text(json.dumps(db, indent=2), encoding="utf-8")


def process_once():
    db = load_jobs()
    jobs = db.get("jobs", [])
    changed = 0

    for j in jobs:
        if j.get("status") != "queued":
            continue

        action = j.get("action", "")
        payload = j.get("payload", "")
        log(f"processing {j.get('id')} action={action}")

        try:
            ok, msg = execute_action(action, payload)
            j["status"] = "completed" if ok else "failed"
            j["result"] = (msg or "")[:4000]
            j["completed_at"] = int(time.time())
            changed += 1
        except Exception as e:
            j["status"] = "failed"
            j["result"] = f"worker exception: {e}"[:4000]
            j["completed_at"] = int(time.time())
            changed += 1
            log(traceback.format_exc())

    if changed:
        save_jobs(db)
        log(f"updated {changed} job(s)")


def main():
    log("worker start")
    while True:
        process_once()
        time.sleep(SLEEP_SEC)


if __name__ == "__main__":
    main()
