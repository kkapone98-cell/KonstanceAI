"""
scripts/modules/intent_router.py
Multi-model intent router — classifies plain-language messages as code requests.
Uses Ollama for fast keyword-triggered classification, OpenClaw for complex cases.
"""
import json, logging, re
logger = logging.getLogger(__name__)

INTENT_SYSTEM = """You classify messages sent to Konstance, a self-modifying Telegram AI assistant.
Return ONLY raw JSON, no markdown:
{"is_code_request":bool,"action":"add_feature|fix_bug|improve|rollback|show_drafts|show_goals|show_status|none","target_hint":"bot.py|scripts/modules/|launcher.py|unknown","description":"one clear sentence of what to change","risk":"high|low|unknown"}
Risk: bot.py/launcher.py=high, scripts/modules/*=low, unknown target=high.
action=show_goals if user asks about goals/progress. action=show_status if asking about health/uptime.
Examples:
"add rate limiting" -> {"is_code_request":true,"action":"add_feature","target_hint":"bot.py","description":"Add per-user rate limiting of 1 message per 3 seconds","risk":"high"}
"what's the weather" -> {"is_code_request":false,"action":"none","target_hint":"unknown","description":"","risk":"unknown"}
"what are your goals" -> {"is_code_request":true,"action":"show_goals","target_hint":"unknown","description":"Show current goals and progress","risk":"low"}
"add a /ping command" -> {"is_code_request":true,"action":"add_feature","target_hint":"bot.py","description":"Add /ping command that replies pong","risk":"high"}"""

_CODE_RE = [
    r"\badd\b.*(command|feature|handler|limit|filter|monitor|alert|scraper)",
    r"\bfix\b.*(bug|error|crash|issue|broken)",
    r"\bimprove\b", r"\bupgrade\b", r"\boptimize\b",
    r"\brollback\b", r"\brevert\b", r"\brestore\b",
    r"\bdraft", r"\bpending\b",
    r"\brate.?limit", r"\bschedul",
    r"\bgoal", r"\bprogress\b", r"\bstatus\b",
    r"\/[\w]+ *(command|handler)",
]


def _keyword_hit(text: str) -> bool:
    lower = text.lower()
    return any(re.search(p, lower) for p in _CODE_RE)


def _extract_json(raw: str) -> dict | None:
    raw = re.sub(r"^```(?:json)?\s*", "", raw.strip())
    raw = re.sub(r"\s*```$", "", raw)
    try: return json.loads(raw)
    except Exception:
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            try: return json.loads(m.group(0))
            except Exception: pass
    return None


def _call_llm(text: str) -> str:
    msgs = [{"role": "user", "content": text}]
    # Try fast Ollama first for speed, then OpenClaw
    for fn_name in ["_try_ollama", "_try_openclaw"]:
        try:
            if fn_name == "_try_ollama":
                from scripts.modules.smart_reply_engine import _try_ollama
                r = _try_ollama(messages=msgs, system_override=INTENT_SYSTEM)
            else:
                from scripts.modules.smart_reply_engine import _try_openclaw
                r = _try_openclaw(messages=msgs, system_override=INTENT_SYSTEM)
            if r: return r
        except Exception as e:
            logger.debug(f"{fn_name} intent failed: {e}")
    return ""


def parse_code_request(text: str, history: list = None) -> dict:
    lower = text.lower().strip()
    if len(text) < 4:
        return {"is_code_request": False, "action": "none", "target_hint": "unknown", "description": "", "risk": "unknown"}

    # Fast-path: rollback
    if re.search(r"\b(rollback|revert|restore)\b", lower):
        m = re.search(r"([\w_]+\.py)", lower)
        t = m.group(1) if m else "unknown"
        return {"is_code_request": True, "action": "rollback", "target_hint": t, "description": f"Rollback {t}", "risk": "high"}

    # Fast-path: drafts
    if re.search(r"\b(draft|pending|approval)\b", lower):
        return {"is_code_request": True, "action": "show_drafts", "target_hint": "unknown", "description": "Show pending drafts", "risk": "low"}

    # Fast-path: goals
    if re.search(r"\b(goal|goals|mission|progress|what can you do|capabilities)\b", lower):
        return {"is_code_request": True, "action": "show_goals", "target_hint": "unknown", "description": "Show goals and capabilities", "risk": "low"}

    # Fast-path: status
    if re.search(r"\b(status|health|uptime|running|alive)\b", lower):
        return {"is_code_request": True, "action": "show_status", "target_hint": "unknown", "description": "Show system status", "risk": "low"}

    if not _keyword_hit(text):
        return {"is_code_request": False, "action": "none", "target_hint": "unknown", "description": "", "risk": "unknown"}

    # LLM classification
    try:
        raw = _call_llm(text)
        if raw:
            p = _extract_json(raw)
            if p and "is_code_request" in p:
                return {
                    "is_code_request": bool(p.get("is_code_request")),
                    "action": p.get("action", "none"),
                    "target_hint": p.get("target_hint", "unknown"),
                    "description": p.get("description", ""),
                    "risk": p.get("risk", "high"),
                }
    except Exception as e:
        logger.warning(f"Intent LLM error: {e}")

    # Fallback — keyword matched, LLM failed → treat as high-risk code request
    return {"is_code_request": True, "action": "add_feature", "target_hint": "unknown", "description": text[:200], "risk": "high"}
