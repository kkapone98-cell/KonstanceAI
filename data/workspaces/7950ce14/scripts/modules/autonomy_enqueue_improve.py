import json, pathlib, time, sys
ROOT = pathlib.Path(r"C:\Users\Thinkpad\Desktop\KonstanceAI")
Q = ROOT / "data" / "autonomy_queue.json"

def load(path, default):
    try:
        raw = path.read_text(encoding="utf-8-sig") if path.exists() else ""
        return json.loads(raw) if raw.strip() else default
    except Exception:
        return default

def save(path, obj):
    path.write_text(json.dumps(obj, indent=2), encoding="utf-8")

payload = " ".join(sys.argv[1:]).strip() or "improve workflows"
db = load(Q, {"items": []})
row = {"id": f"auto_{int(time.time())}", "kind": "improve", "payload": payload, "status": "queued", "ts": int(time.time())}
db["items"].append(row)
save(Q, db)
print(json.dumps(row, indent=2))
