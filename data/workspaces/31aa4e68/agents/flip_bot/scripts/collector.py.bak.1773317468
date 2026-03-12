import json, pathlib, time, argparse

ROOT = pathlib.Path(r"C:\Users\Thinkpad\Desktop\KonstanceAI\agents\flip_bot")
DATA = ROOT / "data"
RAW = DATA / "raw_leads.json"
NORM = DATA / "leads_normalized.json"


def load_json(path, default):
    try:
        raw = path.read_text(encoding="utf-8-sig") if path.exists() else ""
        return json.loads(raw) if raw.strip() else default
    except Exception:
        return default


def normalize(items):
    out = []
    for i, x in enumerate(items):
        title = (x.get("title") or "").strip()
        if not title:
            continue
        out.append({
            "id": x.get("id") or f"lead_{int(time.time())}_{i}",
            "title": title,
            "source": x.get("source", "manual"),
            "url": x.get("url", ""),
            "price": float(x.get("price", 0) or 0),
            "category": x.get("category", "unknown"),
            "location": x.get("location", ""),
            "notes": x.get("notes", ""),
            "ts": int(time.time())
        })
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default=str(RAW), help="raw leads JSON path")
    args = ap.parse_args()

    src = pathlib.Path(args.input)
    data = load_json(src, [])
    items = data.get("items", []) if isinstance(data, dict) else data

    norm = normalize(items)
    NORM.write_text(json.dumps({"items": norm}, indent=2), encoding="utf-8")
    print(f"normalized={len(norm)} file={NORM}")


if __name__ == "__main__":
    main()
