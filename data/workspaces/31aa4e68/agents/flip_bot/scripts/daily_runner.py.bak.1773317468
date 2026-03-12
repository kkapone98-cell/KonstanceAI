import pathlib, subprocess, json, time

ROOT = pathlib.Path(r"C:\Users\Thinkpad\Desktop\KonstanceAI\agents\flip_bot")
S = ROOT / "scripts"
OUT = ROOT / "output"
LOG = ROOT / "logs" / f"daily-run-{int(time.time())}.log"
REPORT = OUT / "daily_report.json"


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, (p.stdout or ""), (p.stderr or "")


def load(path, default):
    try:
        raw = path.read_text(encoding="utf-8-sig") if path.exists() else ""
        return json.loads(raw) if raw.strip() else default
    except Exception:
        return default


def main():
    steps = []

    cmds = [
        ["python", str(S / "collector.py")],
        ["python", str(S / "scorer.py")],
        ["python", str(S / "listing_draft.py"), "--top", "8", "--min_score", "55"],
        ["python", str(S / "publish_gate.py"), "enqueue", "--min_score", "55"],
    ]

    for c in cmds:
        rc, out, err = run(c)
        steps.append({"cmd": " ".join(c), "rc": rc, "stdout": out[-1500:], "stderr": err[-1500:]})
        if rc != 0:
            break

    drafts = load(ROOT / "output" / "listing_drafts.json", {"items": []}).get("items", [])
    queue = load(ROOT / "data" / "publish_queue.json", {"items": []}).get("items", [])
    pending = [x for x in queue if x.get("status") == "pending_approval"]

    report = {
        "ts": int(time.time()),
        "steps": steps,
        "draft_count": len(drafts),
        "pending_approval": len(pending),
        "top_titles": [x.get("title", "") for x in drafts[:5]]
    }

    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")

    with open(LOG, "w", encoding="utf-8") as f:
        f.write(json.dumps(report, indent=2))

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
