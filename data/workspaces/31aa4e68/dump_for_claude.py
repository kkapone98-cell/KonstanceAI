"""
dump_for_claude.py  —  drop in project root, run it, upload the output
python dump_for_claude.py
"""

from pathlib import Path
import time

ROOT     = Path(__file__).parent
SKIP_DIRS  = {".git", "__pycache__", ".venv", "venv", "node_modules", "logs"}
SKIP_FILES = {"bot.lock", "claude_context.txt", "dump_for_claude.py"}
SKIP_EXT   = {".pyc", ".pyo", ".log", ".lock", ".bak"}
MAX_FILE_KB = 100  # skip files larger than this

out = []
out.append("=" * 70)
out.append("KONSTANCE AI — FULL PROJECT DUMP FOR CLAUDE")
out.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
out.append(f"Root: {ROOT}")
out.append("=" * 70)

included, skipped = [], []

for path in sorted(ROOT.rglob("*")):
    if not path.is_file():
        continue
    if any(skip in path.parts for skip in SKIP_DIRS):
        continue
    if path.name in SKIP_FILES:
        continue
    if path.suffix in SKIP_EXT:
        continue
    if path.stat().st_size > MAX_FILE_KB * 1024:
        skipped.append(str(path.relative_to(ROOT)))
        continue

    rel = str(path.relative_to(ROOT)).replace("\\", "/")
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        skipped.append(rel)
        continue

    out.append(f"\n{'━'*60}")
    out.append(f"FILE: {rel}")
    out.append(f"{'━'*60}")
    out.append(content)
    included.append(rel)

out.append(f"\n{'='*70}")
out.append(f"INCLUDED {len(included)} files | SKIPPED {len(skipped)} files")
if skipped:
    out.append("Skipped: " + ", ".join(skipped))
out.append("=" * 70)

result = "\n".join(out)
out_path = ROOT / "claude_context.txt"
out_path.write_text(result, encoding="utf-8")
kb = len(result) / 1024
print(f"\nDone: claude_context.txt  ({kb:.1f} KB)  -  {len(included)} files included")
print(f"  Upload this file to Claude.ai\n")
