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
    for intent, vals in aliases.items():
        if n == intent:
            return intent
        if isinstance(vals, list) and n in [str(x).lower() for x in vals]:
            return intent
    return None
