import subprocess, pathlib

ROOT = pathlib.Path(r"C:\Users\Thinkpad\Desktop\KonstanceAI")
MM = ROOT / "scripts" / "money_memory.py"


def run_mm(args):
    p = subprocess.run(["python", str(MM)] + args, capture_output=True, text=True)
    out = (p.stdout or "").strip()
    err = (p.stderr or "").strip()
    return p.returncode, (out if out else err if err else "(no output)")


def money_menu():
    return run_mm(["summary"])


def best_next_play():
    return run_mm(["best"])


def add_play(name, lane, roi, effort="medium", notes=""):
    args = ["add", name, lane, str(roi), effort]
    if notes:
        args.append(notes)
    return run_mm(args)


def log_outcome(play_id, pnl, notes=""):
    args = ["outcome", play_id, str(pnl)]
    if notes:
        args.append(notes)
    return run_mm(args)
