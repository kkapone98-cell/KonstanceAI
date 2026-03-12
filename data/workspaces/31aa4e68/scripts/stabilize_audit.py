import pathlib, subprocess, json, time

ROOT = pathlib.Path(r"C:\Users\Thinkpad\Desktop\KonstanceAI")
REPORT = ROOT / "logs" / f"stabilize-audit-{int(time.time())}.json"

files = [p for p in ROOT.rglob("*.py") if "backups" not in p.parts and "venv" not in p.parts and ".venv" not in p.parts]
results = []

for f in files:
    p = subprocess.run(["python", "-m", "py_compile", str(f)], capture_output=True, text=True)
    results.append({
        "file": str(f),
        "ok": p.returncode == 0,
        "stderr": (p.stderr or "").strip()[:1000]
    })

bad = [r for r in results if not r["ok"]]
out = {
    "total_files": len(results),
    "failed_files": len(bad),
    "failed": bad,
}
REPORT.write_text(json.dumps(out, indent=2), encoding="utf-8")
print(str(REPORT))
print(f"total={len(results)} failed={len(bad)}")
if bad:
    print("first_failed:", bad[0]["file"])
