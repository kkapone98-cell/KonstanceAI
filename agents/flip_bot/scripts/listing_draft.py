import json, pathlib, argparse

ROOT = pathlib.Path(r"C:\Users\Thinkpad\Desktop\KonstanceAI\agents\flip_bot")
SCORED = ROOT / "data" / "leads_scored.json"
OUT = ROOT / "output" / "listing_drafts.json"


def load(path, default):
    try:
        raw = path.read_text(encoding="utf-8-sig") if path.exists() else ""
        return json.loads(raw) if raw.strip() else default
    except Exception:
        return default


def draft(item):
    title = item.get("title", "")
    ask = max(1, int(round(float(item.get("resale_est", 0)) * 0.92)))
    desc = (
        f"{title}.\n"
        f"Condition: pre-owned (verify in person).\n"
        f"Local pickup preferred.\n"
        f"Price set for fast sell."
    )
    return {
        "lead_id": item.get("id"),
        "title": title[:80],
        "price": ask,
        "description": desc,
        "source": item.get("source", ""),
        "url": item.get("url", ""),
        "score": item.get("score", 0)
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=5)
    ap.add_argument("--min_score", type=int, default=55)
    args = ap.parse_args()

    db = load(SCORED, {"items": []})
    picks = [x for x in db.get("items", []) if int(x.get("score", 0)) >= args.min_score][:args.top]
    drafts = [draft(x) for x in picks]
    OUT.write_text(json.dumps({"items": drafts}, indent=2), encoding="utf-8")
    print(f"drafts={len(drafts)} file={OUT}")


if __name__ == "__main__":
    main()
