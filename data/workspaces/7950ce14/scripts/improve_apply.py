"""
improve_apply.py
- Applies low-risk proposal changes only for scripts/generated/*
- For now: creates '.patch-note.md' files + backup markers (safe dry-apply pattern)
"""
import json, pathlib, time, shutil

ROOT = pathlib.Path(r"C:\Users\Thinkpad\Desktop\KonstanceAI")
PROPOSALS = ROOT / "scripts" / "proposals"
POLICY = ROOT / "data" / "improve_policy.json"


def load(path, default):
    try:
        raw = path.read_text(encoding="utf-8-sig") if path.exists() else ""
        return json.loads(raw) if raw.strip() else default
    except Exception:
        return default


def is_low_risk_target(path_str, policy):
    p = path_str.replace('\\\\','/').lower()
    return any(x.lower() in p for x in policy.get("low_risk_paths", []))


def apply_latest():
    files = sorted(PROPOSALS.glob("proposal_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        print("no proposals")
        return 1

    latest = files[0]
    plan = load(latest, {})
    policy = load(POLICY, {"auto_apply_low_risk": False, "low_risk_paths": ["scripts/generated"]})

    targets = plan.get("targets", [])
    if not targets:
        print("no targets")
        return 2

    if not policy.get("auto_apply_low_risk", False):
        print("auto-apply disabled by policy")
        return 3

    applied = []
    for t in targets:
        if not is_low_risk_target(t, policy):
            continue
        p = pathlib.Path(t)
        if not p.exists():
            continue
        b = p.with_suffix(p.suffix + f".bak_{int(time.time())}")
        shutil.copyfile(p, b)
        note = p.with_suffix(p.suffix + ".patch-note.md")
        note.write_text("Auto-improve placeholder: implement proposal changes here.\n", encoding="utf-8")
        applied.append(str(p))

    plan["status"] = "applied_partial" if applied else "pending_manual"
    latest.write_text(json.dumps(plan, indent=2), encoding="utf-8")

    print("applied:", len(applied))
    for x in applied:
        print("-", x)
    return 0


if __name__ == "__main__":
    raise SystemExit(apply_latest())
