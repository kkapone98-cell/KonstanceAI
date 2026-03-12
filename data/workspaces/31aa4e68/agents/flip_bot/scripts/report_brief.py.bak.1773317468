import json, pathlib

ROOT = pathlib.Path(r"C:\Users\Thinkpad\Desktop\KonstanceAI\agents\flip_bot")
REP = ROOT / "output" / "daily_report.json"


def load(path, default):
    try:
        raw = path.read_text(encoding="utf-8-sig") if path.exists() else ""
        return json.loads(raw) if raw.strip() else default
    except Exception:
        return default


def main():
    r = load(REP, {})
    if not r:
        print("No daily report yet. Run daily_runner first.")
        return

    print("Flip Daily Brief")
    print(f"Drafts: {r.get('draft_count',0)}")
    print(f"Pending approval: {r.get('pending_approval',0)}")
    top = r.get("top_titles", [])
    if top:
        print("Top titles:")
        for t in top[:5]:
            print(f"- {t}")


if __name__ == "__main__":
    main()
