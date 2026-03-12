import subprocess, pathlib

ROOT = pathlib.Path(r"C:\Users\Thinkpad\Desktop\KonstanceAI")
FACTORY = ROOT / "scripts" / "script_factory.py"


def run_factory(args):
    p = subprocess.run(["python", str(FACTORY)] + args, capture_output=True, text=True)
    out = (p.stdout or "").strip()
    err = (p.stderr or "").strip()
    return p.returncode, (out if out else err if err else "(no output)")


def create_script(name, purpose):
    return run_factory(["create", name, purpose])


def list_scripts():
    return run_factory(["list"])


def run_script(name, input_text=""):
    args = ["run", name]
    if input_text.strip():
        args.append(input_text.strip())
    return run_factory(args)
