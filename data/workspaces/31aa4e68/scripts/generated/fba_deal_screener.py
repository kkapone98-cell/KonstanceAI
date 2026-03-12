"""
fba_deal_screener.py
Purpose: score FBA deal candidates quickly.
"""
import json, pathlib, time, argparse

ROOT = pathlib.Path(r"C:\Users\Thinkpad\Desktop\KonstanceAI")
DB = ROOT / "data" / "fba_deals.json"


def load_db():
    raw = DB.read_text(encoding="utf-8-sig") if DB.exists() else ""
    return json.loads(raw) if raw.strip() else {"items": []}


def save_db(db):
    DB.write_text(json.dumps(db, indent=2), encoding="utf-8")


def score(cost, sell, rank_ok=True, gated=False):
    margin = sell - cost
    roi = (margin / cost) if cost > 0 else 0
    pts = 0
    if roi >= 0.5: pts += 40
    elif roi >= 0.3: pts += 25
    elif roi >= 0.15: pts += 10
    if margin >= 8: pts += 25
    elif margin >= 4: pts += 15
    if rank_ok: pts += 20
    if not gated: pts += 15
    return min(100, pts)


def add(title, cost, sell, rank_ok=True, gated=False, notes=""):
    db = load_db()
    item = {
        "id": f"fba_{int(time.time())}",
        "title": title,
        "cost": float(cost),
        "sell_est": float(sell),
        "rank_ok": bool(rank_ok),
        "gated": bool(gated),
        "score": score(float(cost), float(sell), bool(rank_ok), bool(gated)),
        "notes": notes,
        "created_at": int(time.time())
    }
    db["items"].append(item)
    save_db(db)
    return item


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("title")
    ap.add_argument("cost", type=float)
    ap.add_argument("sell", type=float)
    ap.add_argument("--rank_ok", action="store_true")
    ap.add_argument("--gated", action="store_true")
    ap.add_argument("--notes", default="")
    args = ap.parse_args()
    print(json.dumps(add(args.title, args.cost, args.sell, args.rank_ok, args.gated, args.notes), indent=2))
