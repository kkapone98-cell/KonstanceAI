import subprocess
import pathlib

ROOT = pathlib.Path(r"C:\Users\Thinkpad\Desktop\KonstanceAI")
SCRIPT = ROOT / "scripts" / "improve_apply.py"


def run_improve_apply():
    """
    Runs improve_apply and returns (code, message).
    """
    if not SCRIPT.exists():
        return 2, f"improve_apply missing: {SCRIPT}"
    p = subprocess.run(["python", str(SCRIPT)], capture_output=True, text=True)
    out = (p.stdout or "").strip()
    err = (p.stderr or "").strip()
    msg = out if out else err if err else "(no output)"
    return p.returncode, msg

