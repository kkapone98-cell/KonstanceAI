import subprocess, pathlib

ROOT = pathlib.Path(r"C:\Users\Thinkpad\Desktop\KonstanceAI")
AUDIT = ROOT / "scripts" / "self_audit.py"


def run_self_audit():
    p = subprocess.run(["python", str(AUDIT)], capture_output=True, text=True)
    out = (p.stdout or "").strip()
    err = (p.stderr or "").strip()
    return p.returncode, (out if out else err if err else "(no output)")
