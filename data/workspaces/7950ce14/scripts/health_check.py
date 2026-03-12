import json, pathlib, subprocess, time

ROOT = pathlib.Path(r"C:\Users\Thinkpad\Desktop\KonstanceAI")
OUT = ROOT / "logs" / f"health-check-{int(time.time())}.json"


def exists(p):
    return p.exists()


def ps_count_contains(token):
    cmd = ["powershell", "-NoProfile", "-Command", f"(Get-CimInstance Win32_Process | Where-Object {{$_.Name -eq 'python.exe' -and $_.CommandLine -match '{token}'}} | Measure-Object).Count"]
    p = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return int((p.stdout or "0").strip().splitlines()[-1])
    except Exception:
        return 0


def main():
    status = {
        "ts": int(time.time()),
        "files": {
            "bot.py": exists(ROOT / "bot.py"),
            "RUNBOOK.md": exists(ROOT / "RUNBOOK.md"),
            "autonomy_queue.json": exists(ROOT / "data" / "autonomy_queue.json"),
            "jobs.json": exists(ROOT / "data" / "jobs.json")
        },
        "process": {
            "bot_instances": ps_count_contains("bot.py"),
            "dispatcher_instances": ps_count_contains("autonomy_dispatcher.py")
        }
    }

    warnings = []
    if status["process"]["bot_instances"] > 1:
        warnings.append("Multiple bot instances detected (Telegram conflict risk)")
    if status["process"]["dispatcher_instances"] > 1:
        warnings.append("Multiple dispatcher instances detected")

    status["warnings"] = warnings
    status["ok"] = len(warnings) == 0 and all(status["files"].values())

    OUT.write_text(json.dumps(status, indent=2), encoding="utf-8")
    print(json.dumps(status, indent=2))


if __name__ == "__main__":
    main()
