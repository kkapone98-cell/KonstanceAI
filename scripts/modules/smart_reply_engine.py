import json
import os
import time
from pathlib import Path
from typing import Any, Dict
from urllib import request as urllib_request
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DEBUG_LOG_PATH = ROOT / "debug-2cefd0.log"
DEBUG_SESSION_ID = "2cefd0"


def _debug_log(run_id: str, hypothesis_id: str, location: str, message: str, data: Dict[str, Any]) -> None:
    payload = {
        "sessionId": DEBUG_SESSION_ID,
        "runId": run_id,
        "hypothesisId": hypothesis_id,
        "location": location,
        "message": message,
        "data": data,
        "timestamp": int(time.time() * 1000),
    }
    try:
        with DEBUG_LOG_PATH.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(payload, ensure_ascii=True) + "\n")
    except Exception:
        pass


def _relay_http_url() -> str:
    url = (os.getenv("OPENCLAW_RELAY_URL") or "ws://127.0.0.1:18789").strip()
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


def _headers() -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    token = (os.getenv("OPENCLAW_RELAY_TOKEN") or "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _parse_response(raw: str) -> str:
    if not raw.strip():
        return ""
    try:
        obj = json.loads(raw)
    except Exception:
        return raw.strip()
    if isinstance(obj, dict):
        return str(obj.get("response") or obj.get("output") or obj.get("message") or "").strip()
    return raw.strip()


def _messages_to_prompt(messages: list[dict[str, str]], system_override: str = "") -> str:
    parts: list[str] = []
    if system_override:
        parts.append(f"System:\n{system_override.strip()}\n")
    for item in messages:
        role = item.get("role", "user").capitalize()
        content = item.get("content", "").strip()
        if not content:
            continue
        parts.append(f"{role}:\n{content}\n")
    return "\n".join(parts).strip()


def relay_available(timeout_sec: int = 5) -> bool:
    url = _relay_http_url().rstrip("/")
    # region agent log
    _debug_log(
        run_id="pre-fix",
        hypothesis_id="H2",
        location="scripts/modules/smart_reply_engine.py:relay_available",
        message="relay_probe_started",
        data={"url": url, "timeout_sec": timeout_sec, "has_env_url": bool((os.getenv("OPENCLAW_RELAY_URL") or "").strip())},
    )
    # endregion
    try:
        with urllib_request.urlopen(f"{url}/health", timeout=timeout_sec):
            # region agent log
            _debug_log(
                run_id="pre-fix",
                hypothesis_id="H2",
                location="scripts/modules/smart_reply_engine.py:relay_available",
                message="relay_health_probe_ok",
                data={"url": f"{url}/health"},
            )
            # endregion
            return True
    except Exception as exc:
        # region agent log
        _debug_log(
            run_id="pre-fix",
            hypothesis_id="H2",
            location="scripts/modules/smart_reply_engine.py:relay_available",
            message="relay_health_probe_failed",
            data={"error_type": type(exc).__name__},
        )
        # endregion
    try:
        req = urllib_request.Request(
            url,
            data=json.dumps({"message": "ping", "context": {"probe": True}}).encode("utf-8"),
            headers=_headers(),
            method="POST",
        )
        with urllib_request.urlopen(req, timeout=timeout_sec) as resp:
            ok = 200 <= getattr(resp, "status", 200) < 300
            # region agent log
            _debug_log(
                run_id="pre-fix",
                hypothesis_id="H2",
                location="scripts/modules/smart_reply_engine.py:relay_available",
                message="relay_post_probe_finished",
                data={"status": getattr(resp, "status", 200), "ok": ok},
            )
            # endregion
            return ok
    except Exception as exc:
        # region agent log
        _debug_log(
            run_id="pre-fix",
            hypothesis_id="H2",
            location="scripts/modules/smart_reply_engine.py:relay_available",
            message="relay_post_probe_failed",
            data={"error_type": type(exc).__name__},
        )
        # endregion
        return False


def openclaw_generate(
    user_text: str,
    prefs: Dict[str, Any],
    profile: Dict[str, Any],
    timeout_sec: int = 45,
    history: list[dict[str, Any]] | None = None,
    self_context: str | None = None,
) -> str:
    url = _relay_http_url()
    headers = _headers()
    payload = {
        "message": user_text,
        "context": {
            "prefs": prefs or {},
            "profile": profile or {},
            "history": history or [],
            "self_context": self_context or "",
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
        return _parse_response(raw)
    except (URLError, HTTPError, TimeoutError, OSError):
        return ""


def ollama_fallback_available(timeout_sec: int = 5) -> bool:
    try:
        with urllib_request.urlopen("http://127.0.0.1:11434/api/tags", timeout=timeout_sec):
            return True
    except Exception:
        return False


def _ollama_generate(prompt: str, timeout_sec: int = 60) -> str:
    payload = {
        "model": _fallback_model(),
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.2, "num_predict": 700},
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


def _try_openclaw(messages: list[dict[str, str]], system_override: str = "") -> str:
    # region agent log
    _debug_log(
        run_id="pre-fix",
        hypothesis_id="H1",
        location="scripts/modules/smart_reply_engine.py:_try_openclaw",
        message="_try_openclaw_invoked",
        data={"messages_count": len(messages), "has_system_override": bool(system_override)},
    )
    # endregion
    prompt = _messages_to_prompt(messages, system_override=system_override)
    return openclaw_generate(prompt, {}, {}, timeout_sec=45)


def _try_ollama(messages: list[dict[str, str]], system_override: str = "") -> str:
    # region agent log
    _debug_log(
        run_id="pre-fix",
        hypothesis_id="H1",
        location="scripts/modules/smart_reply_engine.py:_try_ollama",
        message="_try_ollama_invoked",
        data={"messages_count": len(messages), "has_system_override": bool(system_override)},
    )
    # endregion
    prompt = _messages_to_prompt(messages, system_override=system_override)
    return _ollama_generate(prompt, timeout_sec=90)


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


def smart_reply(
    user_text: str,
    prefs: Dict[str, Any],
    profile: Dict[str, Any],
    history: list[dict[str, Any]] | None = None,
    self_context: str | None = None,
) -> str:
    # region agent log
    _debug_log(
        run_id="pre-fix",
        hypothesis_id="H2",
        location="scripts/modules/smart_reply_engine.py:smart_reply",
        message="smart_reply_invoked",
        data={"has_history": history is not None, "history_len": len(history or []), "has_self_context": bool(self_context)},
    )
    # endregion
    cloud = openclaw_generate(
        user_text,
        prefs,
        profile,
        timeout_sec=45,
        history=history,
        self_context=self_context,
    )
    if cloud:
        return style_text(cloud, prefs)

    prompt_parts = []
    if self_context:
        prompt_parts.append(self_context.strip())
    if history:
        prompt_parts.append("Recent conversation:")
        for item in history[-6:]:
            prompt_parts.append(f"User: {item.get('user', '')}")
            prompt_parts.append(f"Assistant: {item.get('bot', '')}")
    prompt_parts.append(f"User: {user_text}")
    prompt_parts.append("Assistant:")
    prompt = "\n".join(prompt_parts)

    for attempt, timeout_sec in enumerate((45, 60), start=1):
        try:
            # region agent log
            _debug_log(
                run_id="post-fix",
                hypothesis_id="H3",
                location="scripts/modules/smart_reply_engine.py:smart_reply",
                message="ollama_attempt",
                data={"attempt": attempt, "timeout_sec": timeout_sec},
            )
            # endregion
            local = _ollama_generate(prompt, timeout_sec=timeout_sec)
            if local:
                return style_text(local, prefs)
        except Exception as exc:
            # region agent log
            _debug_log(
                run_id="post-fix",
                hypothesis_id="H3",
                location="scripts/modules/smart_reply_engine.py:smart_reply",
                message="ollama_attempt_failed",
                data={"attempt": attempt, "error_type": type(exc).__name__},
            )
            # endregion
            continue
    return style_text("LLM service unavailable. Make sure Ollama is running: ollama serve", prefs)


def generate_file_update(description: str, target_path: str, current_text: str, self_context: str = "") -> str:
    prompt = (
        "You are updating a Windows Python project named KonstanceAI.\n"
        "Return only the complete file contents.\n"
        "Do not include markdown fences or explanations.\n"
        f"Target file: {target_path}\n"
        f"Requested change: {description}\n\n"
        "Preserve existing behavior unless the request requires a change.\n"
        "Keep the file syntactically valid.\n"
    )
    if self_context:
        prompt += f"\nProject context:\n{self_context[:6000]}\n"
    if current_text:
        prompt += f"\nCurrent file:\n{current_text}\n"

    messages = [{"role": "user", "content": prompt}]
    for helper in (_try_openclaw, _try_ollama):
        try:
            result = helper(messages)
        except Exception:
            result = ""
        if result and len(result.strip()) > 20:
            cleaned = result.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[-1]
            if cleaned.endswith("```"):
                cleaned = cleaned.rsplit("```", 1)[0]
            return cleaned.strip()
    return ""
