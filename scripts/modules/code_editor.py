"""Legacy safe-edit helpers kept for compatibility and manual rollback."""

import glob
import os
import py_compile
import shutil
import tempfile
import time
from pathlib import Path

from self_edit.file_policy import resolve_repo_path, risk_level as governed_risk_level

ROOT = Path(__file__).resolve().parents[2]

HIGH_RISK = {"bot.py", "launcher.py", "main.py"}


def risk_level(path) -> str:
    return governed_risk_level(ROOT, path)


def backup_file(path) -> Path:
    path = Path(path)
    if not path.exists(): raise FileNotFoundError(f"Not found: {path}")
    bak = Path(f"{path}.bak.{int(time.time())}")
    shutil.copy2(path, bak)
    return bak


def list_backups(path) -> list:
    return sorted([Path(b) for b in glob.glob(str(path) + ".bak.*")], reverse=True)


def compile_check(path) -> tuple:
    if Path(path).suffix.lower() != ".py":
        return (True, "")
    try:
        py_compile.compile(str(path), doraise=True)
        return (True, "")
    except py_compile.PyCompileError as e:
        return (False, str(e))


def compile_check_string(code: str) -> tuple:
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
            f.write(code); tmp = f.name
        return compile_check(Path(tmp))
    finally:
        if tmp and os.path.exists(tmp): os.unlink(tmp)


def apply_patch(path, new_content: str) -> dict:
    path = resolve_repo_path(ROOT, path)
    r = {"success": False, "backup_path": None, "error": None, "stage": "init"}
    if path.suffix.lower() == ".py":
        r["stage"] = "pre_compile"
        ok, err = compile_check_string(new_content)
        if not ok:
            r["error"] = f"Pre-compile failed: {err}"; return r
    r["stage"] = "backup"
    try:
        if path.exists():
            bak = backup_file(path); r["backup_path"] = str(bak)
    except Exception as e:
        r["error"] = f"Backup failed: {e}"; return r
    r["stage"] = "write"
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(new_content, encoding="utf-8")
    except Exception as e:
        r["error"] = f"Write failed: {e}"
        if r["backup_path"]: shutil.copy2(r["backup_path"], path)
        return r
    if path.suffix.lower() == ".py":
        r["stage"] = "post_compile"
        ok, err = compile_check(path)
        if not ok:
            r["error"] = f"Post-compile failed: {err}"
            if r["backup_path"]:
                shutil.copy2(r["backup_path"], path)
                r["error"] += " — auto-rolled back."
            return r
    r["success"] = True; r["stage"] = "done"
    return r


def rollback(path) -> dict:
    path = resolve_repo_path(ROOT, path)
    backups = list_backups(path)
    if not backups:
        return {"success": False, "restored_from": None, "error": f"No backups for {path.name}"}
    try:
        shutil.copy2(backups[0], path)
        return {"success": True, "restored_from": str(backups[0]), "error": None}
    except Exception as e:
        return {"success": False, "restored_from": None, "error": str(e)}
