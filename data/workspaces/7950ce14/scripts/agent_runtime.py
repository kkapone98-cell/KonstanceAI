import os, json, time, pathlib
from urllib import request

ROOT = pathlib.Path(r"C:\Users\Thinkpad\Desktop\KonstanceAI")
AGENTS_DIR = ROOT / "agents"
DB = ROOT / "data" / "agents.json"


def load_db():
    try:
        raw = DB.read_text(encoding="utf-8-sig") if DB.exists() else ""
        return json.loads(raw) if raw.strip() else {"agents": []}
    except Exception:
        return {"agents": []}


def save_db(db):
    DB.write_text(json.dumps(db, indent=2), encoding="utf-8")


def now_ts():
    return int(time.time())


def ensure_agent_fs(name):
    base = AGENTS_DIR / name
    (base / "runs").mkdir(parents=True, exist_ok=True)
    (base / "memory").mkdir(parents=True, exist_ok=True)
    cfg = base / "config.json"
    if not cfg.exists():
        cfg.write_text(json.dumps({"name": name}, indent=2), encoding="utf-8")
    return base


def create_agent(name, purpose, model="qwen2.5:3b"):
    db = load_db()
    for a in db["agents"]:
        if a["name"].lower() == name.lower():
            return False, "Agent already exists"

    ensure_agent_fs(name)
    item = {
        "name": name,
        "purpose": purpose,
        "model": model,
        "created_at": now_ts(),
        "last_run_at": None,
        "runs": 0,
        "enabled": True
    }
    db["agents"].append(item)
    save_db(db)
    return True, f"Agent created: {name}"


def list_agents():
    db = load_db()
    return db.get("agents", [])


def get_agent(name):
    db = load_db()
    for a in db.get("agents", []):
        if a["name"].lower() == name.lower():
            return db, a
    return db, None


def ollama_generate(model, prompt, timeout=90):
    payload = {"model": model, "prompt": prompt, "stream": False}
    req = request.Request(
        "http://127.0.0.1:11434/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with request.urlopen(req, timeout=timeout) as resp:
        obj = json.loads(resp.read().decode("utf-8", errors="ignore"))
        return (obj.get("response") or "").strip()


def run_agent(name, task):
    db, agent = get_agent(name)
    if not agent:
        return False, f"Agent not found: {name}"
    if not agent.get("enabled", True):
        return False, f"Agent disabled: {name}"

    base = ensure_agent_fs(agent["name"])
    memory_file = base / "memory" / "notes.txt"
    memory = memory_file.read_text(encoding="utf-8", errors="ignore") if memory_file.exists() else ""

    prompt = (
        f"You are sub-agent '{agent['name']}'. Purpose: {agent['purpose']}.\n"
        f"Task: {task}\n"
        f"Known memory:\n{memory[-2000:]}\n\n"
        "Return:\n"
        "1) concise result\n"
        "2) next actions\n"
        "3) any files/scripts to create"
    )

    try:
        out = ollama_generate(agent.get("model", "qwen2.5:3b"), prompt, timeout=120)
    except Exception as e:
        return False, f"Run failed: {e}"

    ts = now_ts()
    run_file = base / "runs" / f"run-{ts}.md"
    run_file.write_text(f"# Task\n{task}\n\n# Output\n{out}\n", encoding="utf-8")

    memory_append = f"\n[{ts}] Task: {task}\n{out[:1200]}\n"
    memory_file.write_text((memory + memory_append), encoding="utf-8")

    agent["last_run_at"] = ts
    agent["runs"] = int(agent.get("runs", 0)) + 1
    save_db(db)

    return True, str(run_file)


def usage():
    print("Usage:")
    print("  python scripts/agent_runtime.py create <name> <purpose>")
    print("  python scripts/agent_runtime.py list")
    print("  python scripts/agent_runtime.py run <name> <task>")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        usage(); raise SystemExit(1)

    cmd = sys.argv[1].lower()

    if cmd == "create":
        if len(sys.argv) < 4:
            usage(); raise SystemExit(1)
        name = sys.argv[2]
        purpose = " ".join(sys.argv[3:]).strip()
        ok, msg = create_agent(name, purpose)
        print(msg)
        raise SystemExit(0 if ok else 2)

    if cmd == "list":
        items = list_agents()
        if not items:
            print("No agents yet.")
        else:
            for a in items:
                print(f"- {a['name']} | model={a.get('model')} | runs={a.get('runs',0)} | enabled={a.get('enabled',True)}")
        raise SystemExit(0)

    if cmd == "run":
        if len(sys.argv) < 4:
            usage(); raise SystemExit(1)
        name = sys.argv[2]
        task = " ".join(sys.argv[3:]).strip()
        ok, msg = run_agent(name, task)
        print(msg)
        raise SystemExit(0 if ok else 3)

    usage(); raise SystemExit(1)
