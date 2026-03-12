import json, pathlib

ROOT = pathlib.Path(r"C:\Users\Thinkpad\Desktop\KonstanceAI\agents\flip_bot")
NORM = ROOT / "data" / "leads_normalized.json"
SCORED = ROOT / "data" / "leads_scored.json"


def load(path, default):
    try:
        raw = path.read_text(encoding="utf-8-sig") if path.exists() else ""
        return json.loads(raw) if raw.strip() else default
    except Exception:
        return default


def estimate_resale(title, price):
    t = title.lower()
    mult = 1.8
    if any(k in t for k in ["bike", "bicycle", "dewalt", "milwaukee", "monitor", "mini fridge", "tool"]):
        mult = 2.8
    if any(k in t for k in ["broken", "parts", "as-is"]):
        mult = 1.2
    return round(float(price) * mult, 2)


def score(price, resale, title):
    if price <= 0:
        return 5
    margin = resale - price
    roi = margin / price
    pts = 0
    if roi >= 1.5: pts += 45
    elif roi >= 1.0: pts += 35
    elif roi >= 0.6: pts += 25
    elif roi >= 0.3: pts += 10

    if margin >= 100: pts += 30
    elif margin >= 60: pts += 20
    elif margin >= 30: pts += 10

    t = title.lower()
    if any(k in t for k in ["pickup today", "moving", "must go", "free"]): pts += 15
    if any(k in t for k in ["broken", "parts"]): pts -= 12

    return max(0, min(100, pts))


def main():
    db = load(NORM, {"items": []})
    out = []
    for x in db.get("items", []):
        p = float(x.get("price", 0) or 0)
        r = estimate_resale(x.get("title", ""), p)
        s = score(p, r, x.get("title", ""))
        y = dict(x)
        y["resale_est"] = r
        y["score"] = s
        y["margin_est"] = round(r - p, 2)
        out.append(y)

    out = sorted(out, key=lambda z: z.get("score", 0), reverse=True)
    SCORED.write_text(json.dumps({"items": out}, indent=2), encoding="utf-8")
    print(f"scored={len(out)} top={(out[0]['title'] if out else 'none')} file={SCORED}")


if __name__ == "__main__":
    main()
