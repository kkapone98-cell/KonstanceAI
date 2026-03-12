import subprocess, pathlib

ROOT = pathlib.Path(r"C:\Users\Thinkpad\Desktop\KonstanceAI")
RUNNER = ROOT / "scripts" / "action_runner.py"


def run_runner(args):
    p = subprocess.run(["python", str(RUNNER)] + args, capture_output=True, text=True)
    out = (p.stdout or "").strip()
    err = (p.stderr or "").strip()
    return p.returncode, (out if out else err if err else "(no output)")


def do_action(action, payload):
    return run_runner(["do", action, payload])


def list_jobs():
    return run_runner(["list"])


def approve_job(job_id):
    return run_runner(["approve", job_id])
