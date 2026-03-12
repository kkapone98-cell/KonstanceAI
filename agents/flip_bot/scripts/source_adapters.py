mport json, pathlib, time, argparse
from urllib import request
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(r"C:\Users\Thinkpad\Desktop\KonstanceAI\agents\flip_bot")
RAW = ROOT / "data" / "raw_leads.json"
IMPORTS = ROOT / "imports"


def load(path, default):
    try:
        raw = path.read_text(encoding="utf-8-sig") if path.exists() else ""
        return json.loads(raw) if raw.strip() else default
    except Exception:
        return default


def save(path, obj):
    path.write_text(json.dumps(obj, indent=2), encoding="utf-8")


def add_items(items):
    db = load(RAW, {"items": []})
    existing = {(x.get("title",""), x.get("source",""), x.get("url","")) for x in db.get("items", [])}
    added = 0
    for x in items:
        key = (x.get("title",""), x.get("source",""), x.get("url",""))
        if key in existing:
            continue
        db["items"].append(x)
        existing.add(key)
        added += 1
    save(RAW, db)
    return added, len(db.get("items", []))


def from_manual(title, price, category="unknown", location="local", source="manual"):
    return [{
        "id": f"m_{int(time.time())}",
        "title": title,
        "source": source,
        "price": float(price),
        "url": "",
        "category": category,
        "location": location,
        "notes": ""
    }]


def from_json_import(path):
    p = pathlib.Path(path)
    data = load(p, [])
    arr = data.get("items", []) if isinstance(data, dict) else data
    out = []
    for i, x in enumerate(arr):
        out.append({
            "id": x.get("id") or f"j_{int(time.time())}_{i}",
            "title": x.get("title", ""),
            "source": x.get("source", "import"),
            "price": float(x.get("price", 0) or 0),
            "url": x.get("url", ""),
            "category": x.get("category", "unknown"),
            "location": x.get("location", ""),
            "notes": x.get("notes", "")
        })
    return out


def from_rss(url, max_items=30):
    req = request.Request(url, headers={"User-Agent": "KonstanceFlipBot/1.0"})
    with request.urlopen(req, timeout=20) as r:
        xml = r.read()
    root = ET.fromstring(xml)

    out = []
    # basic RSS parsing
    for item in root.findall('.//item')[:max_items]:
        title = (item.findtext('title') or '').strip()
        link = (item.findtext('link') or '').strip()
        if not title:
            continue
        out.append({
            "id": f"rss_{int(time.time())}_{len(out)}",
            "title": title,
            "source": "rss",
            "price": 0.0,
            "url": link,
            "category": "unknown",
            "location": "",
            "notes": "rss ingest"
        })
    return out


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd")

    m = sub.add_parser("manual")
    m.add_argument("title")
    m.add_argument("price", type=float)
    m.add_argument("--category", default="unknown")
    m.add_argument("--location", default="local")

    j = sub.add_parser("import_json")
    j.add_argument("path")

    r = sub.add_parser("rss")
    r.add_argument("url")
    r.add_argument("--max", type=int, default=30)

    args = ap.parse_args()
    items = []

    if args.cmd == "manual":
        items = from_manual(args.title, args.price, args.category, args.location)
    elif args.cmd == "import_json":
        items = from_json_import(args.path)
    elif args.cmd == "rss":
        items = from_rss(args.url, args.max)
    else:
        ap.print_help(); return

    added, total = add_items(items)
    print(f"added={added} total={total} file={RAW}")


if __name__ == "__main__":
    main()
