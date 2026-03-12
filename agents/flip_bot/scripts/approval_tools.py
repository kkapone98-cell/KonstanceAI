mport json, pathlib

ROOT = pathlib.Path(r"C:\Users\Thinkpad\Desktop\KonstanceAI\agents\flip_bot")
QUEUE = ROOT / "data" / "publish_queue.json"


def load(path, default):
    try:
        raw = path.read_text(encoding="utf-8-sig") if path.exists() else ""
        return json.loads(raw) if raw.strip() else default
    except Exception:
        return default


def save(path, obj):
    path.write_text(json.dumps(obj, indent=2), encoding="utf-8")


def list_pending(limit=10):
    q = load(QUEUE, {"items": []}).get("items", [])
    p = [x for x in q if x.get("status") == "pending_approval"][:limit]
    if not p:
        print("no pending approvals")
        return
    for x in p:
        l = x.get("listing", {})
        print(f"{x.get('id')} | {l.get('title','')} | ${l.get('price','?')} | score={l.get('score','?')}")


def approve(item_id):
    db = load(QUEUE, {"items": []})
    for x in db.get("items", []):
        if x.get("id") == item_id and x.get("status") == "pending_approval":
            x["status"] = "approved"
            save(QUEUE, db)
            print("approved", item_id)
            return
    print("not_found", item_id)


def publish(item_id):
    db = load(QUEUE, {"items": []})
    for x in db.get("items", []):
        if x.get("id") == item_id and x.get("status") in ["approved", "pending_approval"]:
            x["status"] = "published"
            save(QUEUE, db)
            print("published", item_id)
            return
    print("not_found", item_id)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("usage: list|approve <id>|publish <id>")
        raise SystemExit(1)
    c = sys.argv[1].lower()
    if c == "list":
        list_pending()
    elif c == "approve" and len(sys.argv) > 2:
        approve(sys.argv[2])
    elif c == "publish" and len(sys.argv) > 2:
        publish(sys.argv[2])
    else:
        print("usage: list|approve <id>|publish <id>")
        raise SystemExit(1)
