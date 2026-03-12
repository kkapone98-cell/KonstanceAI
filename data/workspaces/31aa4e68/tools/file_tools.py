"""Legacy tool wrappers kept intentionally safe."""

from pathlib import Path

from core.config import load_config
from self_edit.file_policy import resolve_repo_path


def read_file(path):
    resolved = resolve_repo_path(load_config().root, path)
    if resolved.exists():
        return resolved.read_text(encoding="utf-8")
    return ""


def write_file(path, content):
    raise RuntimeError(
        "Direct writes through tools/file_tools.py are retired. Use the governed upgrade pipeline instead."
    )
