"""Restricted system command helper for non-destructive diagnostics only."""

import subprocess


ALLOWED_PREFIXES = ("python --version", "ollama --version", "where python", "where ollama")


def run_command(cmd):
    normalized = (cmd or "").strip()
    if not any(normalized.startswith(prefix) for prefix in ALLOWED_PREFIXES):
        raise RuntimeError("Unsafe command blocked. Use the launcher or doctor workflows instead.")
    result = subprocess.run(normalized, shell=True, capture_output=True, text=True)
    return {"returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr}
