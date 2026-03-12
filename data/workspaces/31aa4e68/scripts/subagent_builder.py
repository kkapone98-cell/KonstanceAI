import json, pathlib, time

ROOT = pathlib.Path(r"C:\Users\Thinkpad\Desktop\KonstanceAI")
AGENTS = ROOT / "agents"
AGENTS.mkdir(parents=True, exist_ok=True)


def scaffold(name: str, objective: str):
    n = "".join([c for c in name if c.isalnum() or c in "_- "]).strip().replace(" ", "_")
    base = AGENTS / n
    (base / "plans").mkdir(parents=True, exist_ok=True)
    (base / "scripts").mkdir(parents=True, exist_ok=True)
    (base / "logs").mkdir(parents=True, exist_ok=True)

    plan = {
        "id": f"agent_{int(time.time())}",
        "name": n,
        "objective": objective,
        "phases": [
            "research sources + terms",
            "design data model",
            "build collector scripts",
            "build transformer/listing formatter",
            "build execution/approval gates"
        ],
        "safety": {
            "require_human_approval_before_external_post": True,
            "respect_terms_of_service": True,
            "no credential hardcoding": True
        },
        "created_at": int(time.time())
    }

    (base / "plans" / "plan.json").write_text(json.dumps(plan, indent=2), encoding="utf-8")

    readme = f"""# {n}
Objective: {objective}

## Generated scaffold
- plans/plan.json
- scripts/collector.py
- scripts/formatter.py
- scripts/executor.py

## Notes
- External posting/scraping actions must stay behind approval gates.
"""
    (base / "README.md").write_text(readme, encoding="utf-8")

    collector = '''import json\nprint("collector scaffold")\n'''
    formatter = '''import json\nprint("formatter scaffold")\n'''
    executor = '''import json\nprint("executor scaffold - add approval gate before live actions")\n'''

    (base / "scripts" / "collector.py").write_text(collector, encoding="utf-8")
    (base / "scripts" / "formatter.py").write_text(formatter, encoding="utf-8")
    (base / "scripts" / "executor.py").write_text(executor, encoding="utf-8")

    return base


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("usage: python scripts/subagent_builder.py <name> <objective>")
        raise SystemExit(1)
    name = sys.argv[1]
    objective = " ".join(sys.argv[2:]).strip()
    out = scaffold(name, objective)
    print(str(out))
