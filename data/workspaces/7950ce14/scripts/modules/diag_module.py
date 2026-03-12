import json, pathlib, time
ROOT = pathlib.Path(r"C:\Users\Thinkpad\Desktop\KonstanceAI")
DATA = ROOT / "data"
OUT = DATA / "diag_last.json"

def exists(p): return p.exists()

def main():
    d = {
      "ts": int(time.time()),
      "bot": exists(ROOT/"bot.py"),
      "jobs": exists(DATA/"jobs.json"),
      "tasks": exists(DATA/"tasks.json"),
      "money": exists(DATA/"money_memory.json"),
      "router": exists(DATA/"router.json"),
      "policy": exists(DATA/"action_policy.json")
    }
    OUT.write_text(json.dumps(d, indent=2), encoding="utf-8")
    print(json.dumps(d, indent=2))

if __name__ == "__main__":
    main()
