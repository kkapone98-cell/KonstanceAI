mport subprocess, pathlib

ROOT = pathlib.Path(r"C:\Users\Thinkpad\Desktop\KonstanceAI\agents\flip_bot")
S = ROOT / "scripts"


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    print((p.stdout or "").strip())
    if p.returncode != 0:
        print((p.stderr or "").strip())
        raise SystemExit(p.returncode)


def main():
    run(["python", str(S / "collector.py")])
    run(["python", str(S / "scorer.py")])
    run(["python", str(S / "listing_draft.py"), "--top", "5", "--min_score", "55"])
    print("flip_bot pipeline complete")


if __name__ == "__main__":
    main()
