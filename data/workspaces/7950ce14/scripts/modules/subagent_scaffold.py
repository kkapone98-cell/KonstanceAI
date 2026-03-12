import pathlib, json, time
ROOT = pathlib.Path(r"C:\Users\Thinkpad\Desktop\KonstanceAI")
AGENTS = ROOT / "agents"
AGENTS.mkdir(parents=True, exist_ok=True)

def create(name, objective):
    n = "".join([c for c in name if c.isalnum() or c in "_- "]).strip().replace(" ", "_")
    base = AGENTS / n
    (base/"plans").mkdir(parents=True, exist_ok=True)
    (base/"scripts").mkdir(parents=True, exist_ok=True)
    plan = {
      "id": f"agent_{int(time.time())}",
      "name": n,
      "objective": objective,
      "phases": ["research","plan","build","test","execute"],
      "approval_gate": True,
      "created_at": int(time.time())
    }
    (base/"plans"/"plan.json").write_text(json.dumps(plan, indent=2), encoding="utf-8")
    print(str(base))

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("usage: python scripts/modules/subagent_scaffold.py <name> <objective>")
        raise SystemExit(1)
    create(sys.argv[1], " ".join(sys.argv[2:]))
