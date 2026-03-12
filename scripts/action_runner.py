import json, time, pathlib, subprocess

ROOT = pathlib.Path(r"C:\Users\Thinkpad\Desktop\KonstanceAI")
DATA = ROOT / "data"
POLICY = DATA / "action_policy.json"
JOBS = DATA / "jobs.json"
LOGS = ROOT / "logs"

SCRIPT_FACTORY = ROOT / "scripts" / "script_factory.py"
AGENT_RUNTIME = ROOT / "scripts" / "agent_runtime.py"

LOGS.mkdir(parents=True, exist_ok=True)


def now_ts():
    return int(time.time())


def loadj(path, default):
    try:
        raw = path.read_text(encoding="utf-8-sig") if path.exists() else ""
        return json.loads(raw) if raw.strip() else default
    except Exception:
        return default


def savej(path, obj):
    path.write_text(json.dumps(obj, indent=2), encoding="utf-8")


def load_policy():
    return loadj(POLICY, {"auto_allow": [], "confirm_required": [], "deny": []})


def load_jobs():
    return loadj(JOBS, {"jobs": []})


def save_jobs(db):
    savej(JOBS, db)


def classify_action(action):
    p = load_policy()
    a = (action or "").strip()
    if a in p.get("deny", []):
        return "deny"
    if a in p.get("confirm_required", []):
        return "confirm_required"
    if a in p.get("auto_allow", []):
        return "auto_allow"
    return "deny"


def run_cmd(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    out = (p.stdout or "").strip()
    err = (p.stderr or "").strip()
    return p.returncode, out, err


def execute_action(action, payload):
    action = (action or "").strip()
    payload = (payload or "").strip()

    # expected payload formats:
    # create_script: name|purpose
    # run_script: name|input
    # create_agent: name|purpose
    # run_agent: name|task
    # write_note: free text

    if action == "create_script":
        if "|" not in payload: return False, "Payload format: <name>|<purpose>"
        name, purpose = [x.strip() for x in payload.split("|", 1)]
        c, out, err = run_cmd(["python", str(SCRIPT_FACTORY), "create", name, purpose])
        return c == 0, out or err

    if action == "run_script":
        if "|" not in payload: return False, "Payload format: <name>|<input>"
        name, inp = [x.strip() for x in payload.split("|", 1)]
        c, out, err = run_cmd(["python", str(SCRIPT_FACTORY), "run", name, inp])
        return c == 0, out or err

    if action == "create_agent":
        if "|" not in payload: return False, "Payload format: <name>|<purpose>"
        name, purpose = [x.strip() for x in payload.split("|", 1)]
        c, out, err = run_cmd(["python", str(AGENT_RUNTIME), "create", name, purpose])
        return c == 0, out or err

    if action == "run_agent":
        if "|" not in payload: return False, "Payload format: <name>|<task>"
        name, task = [x.strip() for x in payload.split("|", 1)]
        c, out, err = run_cmd(["python", str(AGENT_RUNTIME), "run", name, task])
        return c == 0, out or err

    if action == "write_note":
        notes = DATA / "notes.md"
        line = f"- [{now_ts()}] {payload}\n"
        with open(notes, "a", encoding="utf-8") as f:
            f.write(line)
        return True, "Note written"

    return False, f"Unsupported action: {action}"


def enqueue(action, payload, requested_by=""):
    tier = classify_action(action)
    db = load_jobs()
    job = {
        "id": f"job_{now_ts()}",
        "created_at": now_ts(),
        "action": action,
        "payload": payload,
        "requested_by": str(requested_by),
        "tier": tier,
        "status": "queued" if tier == "auto_allow" else ("pending_approval" if tier == "confirm_required" else "denied"),
        "result": "",
        "completed_at": None
    }
    db["jobs"].append(job)
    save_jobs(db)

    if tier == "deny":
        job["result"] = "Denied by policy"
        save_jobs(db)
        return False, f"Denied by policy: {action}", job["id"]

    if tier == "auto_allow":
        ok, msg = execute_action(action, payload)
        job["status"] = "completed" if ok else "failed"
        job["result"] = msg[:4000]
        job["completed_at"] = now_ts()
        save_jobs(db)
        return ok, msg, job["id"]

    return True, f"Queued for approval: {job['id']}", job["id"]


def approve(job_id):
    db = load_jobs()
    for j in db.get("jobs", []):
        if j.get("id") == job_id:
            if j.get("status") != "pending_approval":
                return False, f"Job not pending approval: {job_id}"
            ok, msg = execute_action(j.get("action", ""), j.get("payload", ""))
            j["status"] = "completed" if ok else "failed"
            j["result"] = msg[:4000]
            j["completed_at"] = now_ts()
            save_jobs(db)
            return ok, msg
    return False, f"Job not found: {job_id}"


def list_jobs(limit=10):
    db = load_jobs()
    items = db.get("jobs", [])[-limit:]
    if not items:
        return "No jobs yet."
    lines = []
    for j in reversed(items):
        lines.append(f"{j['id']} | {j['action']} | {j['status']} | {j['tier']}")
    return "\n".join(lines)


def usage():
    print("Usage:")
    print("  python scripts/action_runner.py do <action> <payload>")
    print("  python scripts/action_runner.py list")
    print("  python scripts/action_runner.py approve <job_id>")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        usage(); raise SystemExit(1)

    cmd = sys.argv[1].lower()
    if cmd == "do":
        if len(sys.argv) < 4:
            usage(); raise SystemExit(1)
        action = sys.argv[2]
        payload = " ".join(sys.argv[3:]).strip()
        ok, msg, job_id = enqueue(action, payload)
        print(f"{job_id}: {msg}")
        raise SystemExit(0 if ok else 2)

    if cmd == "list":
        print(list_jobs(15)); raise SystemExit(0)

    if cmd == "approve":
        if len(sys.argv) < 3:
            usage(); raise SystemExit(1)
        ok, msg = approve(sys.argv[2])
        print(msg)
        raise SystemExit(0 if ok else 3)

    usage(); raise SystemExit(1)
