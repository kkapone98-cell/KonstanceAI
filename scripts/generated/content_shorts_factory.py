"""
content_shorts_factory.py
Purpose: queue short-form content ideas/scripts from one input topic.
"""
import json, pathlib, time, argparse

ROOT = pathlib.Path(r"C:\Users\Thinkpad\Desktop\KonstanceAI")
DB = ROOT / "data" / "content_queue.json"


def load_db():
    raw = DB.read_text(encoding="utf-8-sig") if DB.exists() else ""
    return json.loads(raw) if raw.strip() else {"items": []}


def save_db(db):
    DB.write_text(json.dumps(db, indent=2), encoding="utf-8")


def generate(topic):
    hooks = [
        f"I made $100 from {topic} with one simple trick",
        f"Stop scrolling: this {topic} method is underrated",
        f"3 mistakes people make with {topic}"
    ]
    out = []
    for h in hooks:
        out.append({
            "id": f"short_{int(time.time())}_{len(out)}",
            "topic": topic,
            "hook": h,
            "script": f"Hook: {h}\nBody: quick 3-step explanation\nCTA: follow for next play",
            "status": "queued",
            "created_at": int(time.time())
        })
    return out


def add_topic(topic):
    db = load_db()
    items = generate(topic)
    db["items"].extend(items)
    save_db(db)
    return items


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("topic")
    args = ap.parse_args()
    print(json.dumps(add_topic(args.topic), indent=2))
