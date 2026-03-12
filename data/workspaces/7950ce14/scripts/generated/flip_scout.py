"""
flip_scout.py
Purpose: track local flip opportunities with simple ROI scoring.
"""
import json, pathlib, time, argparse

ROOT = pathlib.Path(r"C:\Users\Thinkpad\Desktop\KonstanceAI")
DB = ROOT / "data" / "opportunities.json"


def load_db():
    raw = DB.read_text(encoding="utf-8-sig") if DB.exists() else ""
    return json.loads(raw) if raw.strip() else {"items": []}


def save_db(db):
    DB.write_text(json.dumps(db, indent=2), encoding="utf-8")


def score(cost, resale):
    if cost <= 0:
        return 0
    margin = resale - cost
    roi = margin / cost
    pts = 0
    if roi >= 1.0: pts += 40
    elif roi >= 0.6: pts += 30
    elif roi >= 0.3: pts += 20
    else: pts += 5
    if margin >= 100: pts += 30
    elif margin >= 50: pts += 20
    elif margin >= 20: pts += 10
    if cost <= 25: pts += 20
    elif cost <= 75: pts += 10
    return min(100, pts)


def add(title, source, cost, resale, notes=""):
    db = load_db()
    item = {
        "id": f"flip_{int(time.time())}",
        "title": title,
        "source": source,
        "cost": float(cost),
        "resale_est": float(resale),
        "score": score(float(cost), float(resale)),
        "status": "new",
        "notes": notes,
        "created_at": int(time.time())
    }
    db["items"].append(item)
    save_db(db)
    return item


def top(limit=10):
    db = load_db()
    items = sorted(db.get("items", []), key=lambda x: x.get("score", 0), reverse=True)
    return items[:limit]


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd")

    a = sub.add_parser("add")
    a.add_argument("title")
    a.add_argument("source")
    a.add_argument("cost", type=float)
    a.add_argument("resale", type=float)
    a.add_argument("--notes", default="")

    t = sub.add_parser("top")
    t.add_argument("--limit", type=int, default=10)

    args = ap.parse_args()
    if args.cmd == "add":
        x = add(args.title, args.source, args.cost, args.resale, args.notes)
        print(json.dumps(x, indent=2))
    elif args.cmd == "top":
        print(json.dumps(top(args.limit), indent=2))
    else:
        ap.print_help()
