import json
import os
from pathlib import Path
from typing import Any, Dict
from urllib import request as urllib_request
from urllib.error import URLError, HTTPError

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)


def _relay_http_url() -> str:
    url = (os.getenv("OPENCLAW_RELAY_URL") or "").strip()
    if not url:
        return ""
    if url.startswith("ws://"):
        return "http://" + url[5:]
    if url.startswith("wss://"):
        return "https://" + url[6:]
    return url


def _read_llm_cfg() -> Dict[str, Any]:
    cfg_path = DATA_DIR / "llm.json"
    if not cfg_path.exists():
        return {"fallback": "qwen2.5:3b"}
    try:
        return json.loads(cfg_path.read_text(encoding="utf-8"))
    except Exception:
        return {"fallback": "qwen2.5:3b"}


def _fallback_model() -> str:
    cfg = _read_llm_cfg()
    model = (cfg.get("fallback") or cfg.get("primary") or "qwen2.5:3b").strip()
    if model.endswith(":cloud"):
        return "qwen2.5:3b"
    return model


def relay_available(timeout_sec: int = 5) -> bool:
    return bool(_relay_ping(timeout_sec=timeout_sec))


def _relay_ping(timeout_sec: int = 5) -> bool:
    url = _relay_http_url()
    if not url:
        return False
    headers = {"Content-Type": "application/json"}
    token = (os.getenv("OPENCLAW_RELAY_TOKEN") or "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps({"message": "ping", "context": {"probe": True}}).encode("utf-8")
    try:
        req = urllib_request.Request(url, data=body, headers=headers, method="POST")
        with urllib_request.urlopen(req, timeout=timeout_sec) as resp:
            return 200 <= getattr(resp, "status", 200) < 300
    except Exception:
        return False


def openclaw_generate(user_text: str, prefs: Dict[str, Any], profile: Dict[str, Any], timeout_sec: int = 45) -> str:
    url = _relay_http_url()
    if not url:
        return ""
    headers = {"Content-Type": "application/json"}
    token = (os.getenv("OPENCLAW_RELAY_TOKEN") or "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"

    payload = {
        "message": user_text,
        "context": {
            "prefs": prefs or {},
            "profile": profile or {},
            "source": "konstance",
        },
    }

    try:
        req = urllib_request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib_request.urlopen(req, timeout=timeout_sec) as resp:
            raw = resp.read().decode("utf-8", errors="ignore")
    except (URLError, HTTPError, TimeoutError, OSError):
        return ""

    if not raw.strip():
        return ""

    try:
        obj = json.loads(raw)
        if isinstance(obj, dict):
            return (
                str(obj.get("response") or obj.get("output") or obj.get("message") or "").strip()
            )
    except Exception:
        pass

    return raw.strip()


def ollama_fallback_available(timeout_sec: int = 5) -> bool:
    try:
        _ = _ollama_generate("Reply with exactly: OK", timeout_sec=timeout_sec)
        return True
    except Exception:
        return False


def _ollama_generate(prompt: str, timeout_sec: int = 60) -> str:
    model = _fallback_model()
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.3, "num_predict": 250},
    }
    req = urllib_request.Request(
        "http://127.0.0.1:11434/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib_request.urlopen(req, timeout=timeout_sec) as resp:
        raw = resp.read().decode("utf-8", errors="ignore")
    obj = json.loads(raw)
    return str(obj.get("response") or "").strip()


def style_text(text: str, prefs: Dict[str, Any]) -> str:
    out = (text or "").strip() or "..."
    verbosity = ((prefs or {}).get("verbosity") or "medium").lower()
    if verbosity == "short" and len(out) > 900:
        return out[:900].rstrip() + "…"
    if verbosity == "long":
        return out
    if len(out) > 2400:
        return out[:2400].rstrip() + "…"
    return out


def smart_reply(user_text: str, prefs: Dict[str, Any], profile: Dict[str, Any]) -> str:
    cloud = openclaw_generate(user_text, prefs, profile, timeout_sec=45)
    if cloud:
        return style_text(cloud, prefs)
    try:
        local = _ollama_generate(user_text, timeout_sec=90)
        if local:
            return style_text(local, prefs)
    except Exception:
        pass
    return style_text(f"I heard: {user_text}", prefs)
