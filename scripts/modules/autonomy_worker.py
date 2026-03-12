import json, pathlib, time

ROOT = pathlib.Path(r"C:\Users\Thinkpad\Desktop\KonstanceAI")
Q = ROOT / "data" / "autonomy_queue.json"
OUT = ROOT / "logs" / "autonomy-worker-last.json"

def load(path, default):
try:
raw = path.read_text(encoding="utf-8-sig") if path.exists() else ""
return json.loads(raw) if raw.strip() else default
except Exception:
return default

def save(path, obj):
path.write_text(json.dumps(obj, indent=2), encoding="utf-8")

db = load(Q, {"items":[]})
changed = 0

for x in db.get("items", []):
if x.get("status") != "queued":
continue
x["status"] = "completed"
x["completed_at"] = int(time.time())
x["result"] = f"Processed {x.get('kind')} => {x.get('payload')}"
changed += 1

save(Q, db)
save(OUT, {"ts": int(time.time()), "processed": changed})
print(json.dumps({"processed": changed}, indent=2))
