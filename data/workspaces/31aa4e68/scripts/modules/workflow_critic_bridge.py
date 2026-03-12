import subprocess
import pathlib

ROOT = pathlib.Path(r"C:\Users\Thinkpad\Desktop\KonstanceAI")
SCRIPT = ROOT / "scripts" / "workflow_critic.py"


def run_workflow_critic():
    """
    Runs workflow critic and returns (code, message).
    """
    if not SCRIPT.exists():
        return 2, f"workflow_critic missing: {SCRIPT}"
    p = subprocess.run(["python", str(SCRIPT)], capture_output=True, text=True)
    out = (p.stdout or "").strip()
    err = (p.stderr or "").strip()
    msg = out if out else err if err else "(no output)"
    return p.returncode, msg

