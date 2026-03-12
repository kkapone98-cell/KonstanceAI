import subprocess
import pathlib

ROOT = pathlib.Path(r"C:\Users\Thinkpad\Desktop\KonstanceAI")
SCRIPT = ROOT / "scripts" / "improve_proposer.py"


def run_improve_proposer(goal: str = "improve workflows"):
    """
    Runs improve_proposer and returns (code, message).
    """
    if not SCRIPT.exists():
        return 2, f"improve_proposer missing: {SCRIPT}"
    goal = (goal or "improve workflows").strip()
    p = subprocess.run(["python", str(SCRIPT), goal], capture_output=True, text=True)
    out = (p.stdout or "").strip()
    err = (p.stderr or "").strip()
    msg = out if out else err if err else "(no output)"
    return p.returncode, msg

