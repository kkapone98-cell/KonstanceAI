"""
scripts/modules/code_editor.py
Konstance safe self-edit engine. Backup + compile + apply + rollback.
"""
import os, shutil, time, py_compile, tempfile, glob
from pathlib import Path

HIGH_RISK = {"bot.py", "launcher.py", "main.py"}


def risk_level(path) -> str:
    name = Path(path).name
    if name in HIGH_RISK: return "high"
    if "scripts" in Path(path).parts: return "low"
    return "high"


def backup_file(path) -> Path:
    path = Path(path)
    if not path.exists(): raise FileNotFoundError(f"Not found: {path}")
    bak = Path(f"{path}.bak.{int(time.time())}")
    shutil.copy2(path, bak)
    return bak


def list_backups(path) -> list:
    return sorted([Path(b) for b in glob.glob(str(path) + ".bak.*")], reverse=True)


def compile_check(path) -> tuple:
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
    path = Path(path)
    r = {"success": False, "backup_path": None, "error": None, "stage": "init"}
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
    path = Path(path)
    backups = list_backups(path)
    if not backups:
        return {"success": False, "restored_from": None, "error": f"No backups for {path.name}"}
    try:
        shutil.copy2(backups[0], path)
        return {"success": True, "restored_from": str(backups[0]), "error": None}
    except Exception as e:
        return {"success": False, "restored_from": None, "error": str(e)}
