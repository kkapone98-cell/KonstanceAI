import subprocess, shlex, pathlib

ROOT = pathlib.Path(r"C:\Users\Thinkpad\Desktop\KonstanceAI")
RUNTIME = ROOT / "scripts" / "agent_runtime.py"


def run_runtime(args):
    cmd = ["python", str(RUNTIME)] + args
    p = subprocess.run(cmd, capture_output=True, text=True)
    out = (p.stdout or "").strip()
    err = (p.stderr or "").strip()
    msg = out if out else err
    return p.returncode, (msg or "(no output)")


def create_agent(name, purpose):
    return run_runtime(["create", name, purpose])


def list_agents():
    return run_runtime(["list"])


def run_agent(name, task):
    return run_runtime(["run", name, task])
