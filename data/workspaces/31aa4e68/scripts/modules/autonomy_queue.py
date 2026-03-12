import json, pathlib, time
ROOT = pathlib.Path(r"C:\Users\Thinkpad\Desktop\KonstanceAI")
DATA = ROOT / "data"
Q = DATA / "autonomy_queue.json"

def load(path, default):
    try:
        raw = path.read_text(encoding="utf-8-sig") if path.exists() else ""
        return json.loads(raw) if raw.strip() else default
    except Exception:
        return default

def save(path, obj):
    path.write_text(json.dumps(obj, indent=2), encoding="utf-8")

def enqueue(kind, payload):
    db = load(Q, {"items": []})
    row = {"id": f"auto_{int(time.time())}", "kind": kind, "payload": payload, "status": "queued", "ts": int(time.time())}
    db["items"].append(row)
    save(Q, db)
    return row

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("usage: python scripts/modules/autonomy_queue.py <kind> <payload>")
        raise SystemExit(1)
    row = enqueue(sys.argv[1], " ".join(sys.argv[2:]))
    print(json.dumps(row, indent=2))
