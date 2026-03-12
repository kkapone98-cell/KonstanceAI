"""
improve_proposer.py
- Converts findings + user goal into concrete patch proposals
- Writes proposal files into scripts/proposals/
"""
import json, pathlib, time

ROOT = pathlib.Path(r"C:\Users\Thinkpad\Desktop\KonstanceAI")
DATA = ROOT / "data"
PROPOSALS = ROOT / "scripts" / "proposals"
FINDINGS = DATA / "workflow_findings.json"
QUEUE = DATA / "improve_queue.json"


def load(path, default):
    try:
        raw = path.read_text(encoding="utf-8-sig") if path.exists() else ""
        return json.loads(raw) if raw.strip() else default
    except Exception:
        return default


def save(path, obj):
    path.write_text(json.dumps(obj, indent=2), encoding="utf-8")


def make_proposal(goal_text):
    f = load(FINDINGS, {})
    ts = int(time.time())
    pid = f"proposal_{ts}"

    targets = []
    for m in f.get("modules", []):
        if m.get("issues"):
            targets.append(m["module"])

    plan = {
        "id": pid,
        "goal": goal_text,
        "created_at": ts,
        "targets": targets[:5],
        "changes": [
            "replace TODO scaffold body with concrete logic",
            "add validation for input arguments",
            "append structured logging to logs/module-name.log",
            "return deterministic JSON output for downstream jobs"
        ],
        "risk": "low" if all("scripts/generated" in t.replace('\\\\','/') for t in targets[:5]) else "medium",
        "status": "proposed"
    }

    out_file = PROPOSALS / f"{pid}.json"
    out_file.write_text(json.dumps(plan, indent=2), encoding="utf-8")

    q = load(QUEUE, {"items": []})
    q["items"].append(plan)
    save(QUEUE, q)

    return out_file, plan


if __name__ == "__main__":
    import sys
    goal = " ".join(sys.argv[1:]).strip() if len(sys.argv) > 1 else "improve workflows"
    f, p = make_proposal(goal)
    print(str(f))
    print("risk=", p["risk"])
