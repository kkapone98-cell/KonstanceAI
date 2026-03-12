import json, pathlib, time

ROOT = pathlib.Path(r"C:\Users\Thinkpad\Desktop\KonstanceAI")
DB = ROOT / "data" / "money_memory.json"


def load_db():
    try:
        raw = DB.read_text(encoding="utf-8-sig") if DB.exists() else ""
        return json.loads(raw) if raw.strip() else {"plays": [], "wins": [], "losses": [], "last_review": None}
    except Exception:
        return {"plays": [], "wins": [], "losses": [], "last_review": None}


def save_db(db):
    DB.write_text(json.dumps(db, indent=2), encoding="utf-8")


def add_play(name, lane, expected_roi, effort="medium", notes=""):
    db = load_db()
    item = {
        "id": f"play_{int(time.time())}",
        "name": name,
        "lane": lane,
        "expected_roi": float(expected_roi),
        "effort": effort,
        "notes": notes,
        "status": "active",
        "created_at": int(time.time())
    }
    db["plays"].append(item)
    save_db(db)
    return item


def log_outcome(play_id, pnl, notes=""):
    db = load_db()
    row = {"play_id": play_id, "pnl": float(pnl), "notes": notes, "ts": int(time.time())}
    if float(pnl) >= 0:
        db["wins"].append(row)
    else:
        db["losses"].append(row)
    save_db(db)
    return row


def menu():
    db = load_db()
    plays = [p for p in db.get("plays", []) if p.get("status") == "active"]
    plays = sorted(plays, key=lambda x: x.get("expected_roi", 0), reverse=True)
    return plays[:10]


def best_next_play():
    plays = menu()
    if not plays:
        return None
    # simple selection: high roi + low/medium effort preferred
    def score(p):
        roi = float(p.get("expected_roi", 0))
        effort = p.get("effort", "medium")
        eff_pen = {"low": 0, "medium": 5, "high": 12}.get(effort, 7)
        return roi * 100 - eff_pen
    return sorted(plays, key=score, reverse=True)[0]


def summary_text():
    db = load_db()
    plays = menu()
    wins = db.get("wins", [])
    losses = db.get("losses", [])
    pnl = sum([float(x.get("pnl", 0)) for x in wins + losses])

    lines = []
    lines.append("Money Menu")
    lines.append(f"- Active plays: {len(plays)}")
    lines.append(f"- Wins: {len(wins)} | Losses: {len(losses)} | Net PnL: {pnl:.2f}")
    lines.append("")
    lines.append("Top plays:")
    for p in plays[:5]:
        lines.append(f"- {p.get('name')} | lane={p.get('lane')} | roi={p.get('expected_roi')} | effort={p.get('effort')}")

    b = best_next_play()
    if b:
        lines.append("")
        lines.append(f"Best next play: {b.get('name')} ({b.get('lane')})")
    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    cmd = (sys.argv[1] if len(sys.argv) > 1 else "summary").lower()
    if cmd == "add":
        # add <name> <lane> <roi> [effort] [notes]
        if len(sys.argv) < 5:
            print("usage: add <name> <lane> <roi> [effort] [notes]")
            raise SystemExit(1)
        name = sys.argv[2]
        lane = sys.argv[3]
        roi = float(sys.argv[4])
        effort = sys.argv[5] if len(sys.argv) > 5 else "medium"
        notes = " ".join(sys.argv[6:]) if len(sys.argv) > 6 else ""
        print(json.dumps(add_play(name, lane, roi, effort, notes), indent=2))
    elif cmd == "outcome":
        if len(sys.argv) < 4:
            print("usage: outcome <play_id> <pnl> [notes]")
            raise SystemExit(1)
        pid = sys.argv[2]
        pnl = float(sys.argv[3])
        notes = " ".join(sys.argv[4:]) if len(sys.argv) > 4 else ""
        print(json.dumps(log_outcome(pid, pnl, notes), indent=2))
    elif cmd == "best":
        print(json.dumps(best_next_play() or {}, indent=2))
    else:
        print(summary_text())
