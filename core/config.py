"""Configuration loading and path resolution for KonstanceAI."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


def _default_root() -> Path:
    env_root = (os.getenv("KONSTANCE_ROOT") or "").strip()
    if env_root:
        return Path(env_root).resolve()
    return Path(__file__).resolve().parents[1]


def _pick_python(root: Path) -> str:
    venv_python = root / ".venv" / "Scripts" / "python.exe"
    if venv_python.exists():
        return str(venv_python)
    return sys.executable


def _normalize_optional_path(raw: str, root: Path) -> str:
    value = (raw or "").strip().strip('"').strip("'")
    if not value:
        return ""
    path = Path(os.path.expandvars(os.path.expanduser(value)))
    if not path.is_absolute():
        path = (root / path).resolve()
    return str(path)


@dataclass(slots=True)
class AppConfig:
    root: Path
    data_dir: Path
    logs_dir: Path
    token: str
    owner_id: int
    python_executable: str
    openclaw_relay_url: str
    openclaw_relay_token: str
    openclaw_cmd: str
    openclaw_cwd: str
    ollama_model: str
    local_llm_model: str

    def ensure_runtime_dirs(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        (self.data_dir / "workspaces").mkdir(parents=True, exist_ok=True)
        (self.data_dir / "doctor").mkdir(parents=True, exist_ok=True)
        (self.data_dir / "memory").mkdir(parents=True, exist_ok=True)
        (self.data_dir / "upgrade_history").mkdir(parents=True, exist_ok=True)
        (self.root / "openclaw").mkdir(parents=True, exist_ok=True)

    @property
    def has_owner(self) -> bool:
        return self.owner_id > 0


def load_config(root: str | Path | None = None) -> AppConfig:
    project_root = Path(root).resolve() if root else _default_root()
    load_dotenv(project_root / ".env")

    token = (os.getenv("TELEGRAM_BOT_TOKEN") or "").strip()
    if not token:
        token_file = project_root / "telegram_token.txt"
        if token_file.exists():
            token = token_file.read_text(encoding="utf-8").strip()

    llm_cfg = project_root / "data" / "llm.json"
    model = "qwen2.5:3b"
    if llm_cfg.exists():
        try:
            import json

            payload = json.loads(llm_cfg.read_text(encoding="utf-8"))
            model = str(payload.get("fallback") or payload.get("primary") or model).strip() or model
        except Exception:
            pass

    config = AppConfig(
        root=project_root,
        data_dir=project_root / "data",
        logs_dir=project_root / "logs",
        token=token,
        owner_id=int((os.getenv("OWNER_ID") or "0").strip() or "0"),
        python_executable=_pick_python(project_root),
        openclaw_relay_url=(os.getenv("OPENCLAW_RELAY_URL") or "").strip(),
        openclaw_relay_token=(os.getenv("OPENCLAW_RELAY_TOKEN") or "").strip(),
        openclaw_cmd=(os.getenv("OPENCLAW_CMD") or "").strip(),
        openclaw_cwd=_normalize_optional_path((os.getenv("OPENCLAW_CWD") or "").strip(), project_root),
        ollama_model=model,
        local_llm_model=(os.getenv("LOCAL_LLM_MODEL") or model or "qwen2.5").strip(),
    )
    config.ensure_runtime_dirs()
    return config

