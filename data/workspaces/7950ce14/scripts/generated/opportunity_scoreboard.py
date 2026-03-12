"""
opportunity_scoreboard.py
Purpose: daily snapshot of opportunities and pipeline activity.
"""
import json, pathlib, time

ROOT = pathlib.Path(r"C:\Users\Thinkpad\Desktop\KonstanceAI")
OPP = ROOT / "data" / "opportunities.json"
FBA = ROOT / "data" / "fba_deals.json"
CNT = ROOT / "data" / "content_queue.json"
OUT = ROOT / "data" / "scoreboard.json"


def load(path):
    raw = path.read_text(encoding="utf-8-sig") if path.exists() else ""
    return json.loads(raw) if raw.strip() else {"items": []}


def run():
    opp = load(OPP).get("items", [])
    fba = load(FBA).get("items", [])
    cnt = load(CNT).get("items", [])

    snap = {
        "ts": int(time.time()),
        "flip_count": len(opp),
        "flip_avg_score": (sum([x.get("score",0) for x in opp]) / len(opp)) if opp else 0,
        "fba_count": len(fba),
        "fba_avg_score": (sum([x.get("score",0) for x in fba]) / len(fba)) if fba else 0,
        "content_queued": len([x for x in cnt if x.get("status") == "queued"])
    }

    raw = OUT.read_text(encoding="utf-8-sig") if OUT.exists() else ""
    db = json.loads(raw) if raw.strip() else {"daily": []}
    db["daily"].append(snap)
    OUT.write_text(json.dumps(db, indent=2), encoding="utf-8")
    print(json.dumps(snap, indent=2))


if __name__ == "__main__":
    run()
