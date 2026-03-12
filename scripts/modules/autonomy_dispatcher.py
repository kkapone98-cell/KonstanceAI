import json, pathlib, time, subprocess

from core.config import load_config

ROOT = load_config().root
Q = ROOT / "data" / "autonomy_queue.json"
LOG = ROOT / "logs" / "autonomy-dispatcher.log"

PROPOSER = ROOT / "scripts" / "improve_proposer.py"
APPLIER = ROOT / "scripts" / "improve_apply.py"
PYTHON = load_config().python_executable


def log(msg):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"[{int(time.time())}] {msg}\n")


def load(path, default):
    try:
        raw = path.read_text(encoding="utf-8-sig") if path.exists() else ""
        return json.loads(raw) if raw.strip() else default
    except Exception:
        return default


def save(path, obj):
    path.write_text(json.dumps(obj, indent=2), encoding="utf-8")


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    out = (p.stdout or "").strip()
    err = (p.stderr or "").strip()
    return p.returncode, (out if out else err if err else "(no output)")


def process_item(x):
    kind = (x.get("kind") or "").lower()
    payload = (x.get("payload") or "").strip()

    if kind == "improve":
        rc1, msg1 = run([PYTHON, str(PROPOSER), payload or "improve workflows"])
        if rc1 != 0:
            return False, f"proposer failed: {msg1[:1200]}"

        # Keep the autonomous loop proposal-only; promotion happens through the upgrade pipeline.
        rc2, msg2 = run([PYTHON, str(APPLIER)])
        if rc2 != 0:
            return True, f"proposal created; awaiting governed promotion: {msg2[:1200]}"
        return True, f"proposal created; review through Telegram before promotion: {msg2[:1200]}"

    return True, f"no-op for kind={kind}"


def process_once():
    db = load(Q, {"items": []})
    changed = 0
    for x in db.get("items", []):
        if x.get("status") != "queued":
            continue
        ok, msg = process_item(x)
        x["status"] = "completed" if ok else "failed"
        x["completed_at"] = int(time.time())
        x["result"] = msg
        changed += 1
        log(f"{x.get('id')} -> {x.get('status')}")

    if changed:
        save(Q, db)


def main():
    log("dispatcher start")
    while True:
        process_once()
        time.sleep(5)


if __name__ == "__main__":
    main()
