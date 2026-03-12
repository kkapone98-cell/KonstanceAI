import json, pathlib, time

ROOT = pathlib.Path(r"C:\Users\Thinkpad\Desktop\KonstanceAI")
Q = ROOT / "data" / "autonomy_queue.json"


def _load():
    try:
        raw = Q.read_text(encoding="utf-8-sig") if Q.exists() else ""
        return json.loads(raw) if raw.strip() else {"items": []}
    except Exception:
        return {"items": []}


def _save(db):
    Q.write_text(json.dumps(db, indent=2), encoding="utf-8")


def enqueue_improve_request(text: str, requested_by: str = "telegram"):
    db = _load()
    row = {
        "id": f"auto_{int(time.time())}",
        "kind": "improve",
        "payload": (text or "").strip(),
        "status": "queued",
        "requested_by": requested_by,
        "ts": int(time.time())
    }
    db["items"].append(row)
    _save(db)
    return row
