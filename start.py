"""Entry point for KonstanceAI. Prints startup message and runs the launcher."""

from __future__ import annotations

import os
import runpy
import sys
from pathlib import Path

# Ensure project root is on sys.path
_root = Path(__file__).resolve().parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))
os.chdir(_root)

if __name__ == "__main__":
    print("Konstance started.")
    runpy.run_path(str(_root / "launcher.py"), run_name="__main__")
