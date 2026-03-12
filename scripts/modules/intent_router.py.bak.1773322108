import json, pathlib
ROOT = pathlib.Path(r"C:\Users\Thinkpad\Desktop\KonstanceAI")
ALIASES = ROOT / "data" / "intent_aliases.json"

def load_aliases():
    try:
        raw = ALIASES.read_text(encoding="utf-8-sig") if ALIASES.exists() else ""
        return json.loads(raw) if raw.strip() else {}
    except Exception:
        return {}

def resolve_intent(text: str):
    n = (text or "").strip().lower()
    aliases = load_aliases()
    for k,v in aliases.items():
        if n == k: return (k, 0.99)
        if isinstance(v,list) and n in [str(x).lower() for x in v]:
            return (k, 0.95)
    if n.startswith("goal "): return ("goal", 0.9)
    if n.startswith("do action "): return ("do_action", 0.9)
    return (None, 0.0)

if __name__ == "__main__":
    import sys
    t = " ".join(sys.argv[1:])
    i,c = resolve_intent(t)
    print(json.dumps({"intent": i, "confidence": c}))
