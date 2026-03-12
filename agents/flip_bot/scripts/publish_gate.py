import json, pathlib, time, argparse

ROOT = pathlib.Path(r"C:\Users\Thinkpad\Desktop\KonstanceAI\agents\flip_bot")
DRAFTS = ROOT / "output" / "listing_drafts.json"
QUEUE = ROOT / "data" / "publish_queue.json"


def load(path, default):
    try:
        raw = path.read_text(encoding="utf-8-sig") if path.exists() else ""
        return json.loads(raw) if raw.strip() else default
    except Exception:
        return default


def save(path, obj):
    path.write_text(json.dumps(obj, indent=2), encoding="utf-8")


def enqueue_all(min_score=55):
    drafts = load(DRAFTS, {"items": []}).get("items", [])
    q = load(QUEUE, {"items": []})
    added = 0
    for d in drafts:
        if int(d.get("score", 0)) < min_score:
            continue
        row = {
            "id": f"pub_{int(time.time())}_{added}",
            "status": "pending_approval",
            "created_at": int(time.time()),
            "listing": d
        }
        q["items"].append(row)
        added += 1
    save(QUEUE, q)
    return added


def list_queue(status=None):
    items = load(QUEUE, {"items": []}).get("items", [])
    if status:
        items = [x for x in items if x.get("status") == status]
    return items


def approve(item_id):
    q = load(QUEUE, {"items": []})
    for x in q.get("items", []):
        if x.get("id") == item_id and x.get("status") == "pending_approval":
            x["status"] = "approved"
            x["approved_at"] = int(time.time())
            save(QUEUE, q)
            return True
    return False


def mark_published(item_id):
    q = load(QUEUE, {"items": []})
    for x in q.get("items", []):
        if x.get("id") == item_id and x.get("status") in ["approved", "pending_approval"]:
            x["status"] = "published"
            x["published_at"] = int(time.time())
            save(QUEUE, q)
            return True
    return False


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd")

    e = sub.add_parser("enqueue")
    e.add_argument("--min_score", type=int, default=55)

    l = sub.add_parser("list")
    l.add_argument("--status", default="")

    a = sub.add_parser("approve")
    a.add_argument("id")

    p = sub.add_parser("publish")
    p.add_argument("id")

    args = ap.parse_args()
    if args.cmd == "enqueue":
        print(f"queued={enqueue_all(args.min_score)}")
    elif args.cmd == "list":
        print(json.dumps(list_queue(args.status or None), indent=2))
    elif args.cmd == "approve":
        print("ok" if approve(args.id) else "not_found")
    elif args.cmd == "publish":
        print("ok" if mark_published(args.id) else "not_found")
    else:
        ap.print_help()
