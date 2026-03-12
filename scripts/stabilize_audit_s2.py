import pathlib, subprocess, json, time

ROOT = pathlib.Path(r"C:\Users\Thinkpad\Desktop\KonstanceAI")
REPORT = ROOT / "logs" / f"stabilize-audit-s2-{int(time.time())}.json"

targets = [ROOT / "bot.py"]
for p in (ROOT / "scripts").rglob("*.py"):
    if "backups" in p.parts:
        continue
    targets.append(p)

results = []
for f in targets:
    p = subprocess.run(["python", "-m", "py_compile", str(f)], capture_output=True, text=True)
    results.append({"file": str(f), "ok": p.returncode == 0, "stderr": (p.stderr or "").strip()[:1200]})

bad = [r for r in results if not r["ok"]]
out = {"total_files": len(results), "failed_files": len(bad), "failed": bad}
REPORT.write_text(json.dumps(out, indent=2), encoding="utf-8")
print(str(REPORT))
print(f"total={len(results)} failed={len(bad)}")
if bad:
    print("first_failed:", bad[0]["file"])
