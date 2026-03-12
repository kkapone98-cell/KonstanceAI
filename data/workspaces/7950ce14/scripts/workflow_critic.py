"""
workflow_critic.py
- Reads generated module outputs + logs
- Produces findings and candidate improvements
"""
import json, pathlib, time, re

ROOT = pathlib.Path(r"C:\Users\Thinkpad\Desktop\KonstanceAI")
DATA = ROOT / "data"
LOGS = ROOT / "logs"
OUT = DATA / "workflow_findings.json"

MODULES = [
    ROOT / "scripts" / "generated" / "flip_scout.py",
    ROOT / "scripts" / "generated" / "content_shorts_factory.py",
    ROOT / "scripts" / "generated" / "fba_deal_screener.py",
    ROOT / "scripts" / "generated" / "opportunity_scoreboard.py",
]


def read(path):
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def find_issues(path):
    txt = read(path)
    issues = []
    if not txt:
        issues.append("file missing or unreadable")
        return issues
    if "TODO:" in txt:
        issues.append("contains TODO markers")
    if "except Exception" in txt and "pass" in txt:
        issues.append("broad exception handling may hide errors")
    if "print(" in txt and "logging" not in txt:
        issues.append("uses print-only output (consider structured logs)")
    if len(txt) < 250:
        issues.append("very small module; likely scaffold only")
    return issues


def parse_recent_failures():
    fails = []
    for log in sorted(LOGS.glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True)[:30]:
        t = read(log)
        if "Traceback" in t or "failed" in t.lower() or "error" in t.lower():
            fails.append({"file": str(log), "snippet": t[:300]})
    return fails


def main():
    findings = {
        "ts": int(time.time()),
        "modules": [],
        "recent_failures": parse_recent_failures(),
        "recommendations": []
    }

    for m in MODULES:
        findings["modules"].append({
            "module": str(m),
            "exists": m.exists(),
            "issues": find_issues(m)
        })

    # generic recommendations
    findings["recommendations"].append("add structured JSON logs for each generated module run")
    findings["recommendations"].append("add unit smoke tests for generated modules")
    findings["recommendations"].append("add schema validation for data/*.json stores")

    OUT.write_text(json.dumps(findings, indent=2), encoding="utf-8")
    print(str(OUT))
    print("recommendations:", len(findings["recommendations"]))


if __name__ == "__main__":
    main()
