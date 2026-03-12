"""
KONSTANCE FULL AUTONOMOUS INSTALLER
=====================================
Run once from project root:

    cd C:/Users/Thinkpad/Desktop/KonstanceAI
    python install_autonomous.py

Installs everything:
  - data/mission.json          Konstance's mission, derived from your full history
  - data/goals.json            Self-improving goal tracker
  - data/capability_log.json   Log of every improvement made
  - scripts/modules/self_model.py      Reads own codebase, builds self-description
  - scripts/modules/goal_engine.py     Tracks goals, marks achieved, generates next targets
  - scripts/modules/code_editor.py     Safe backup+compile+apply engine
  - scripts/modules/intent_router.py   Multi-model plain-language → action router
  - scripts/modules/autonomous_loop.py Full autonomous orchestration
  - Patches bot.py with all new handlers and autonomous on_text
"""

import sys, json, re, shutil, time, py_compile, os
from pathlib import Path

ROOT = Path(__file__).parent
TS   = int(time.time())

# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def backup(path):
    p = Path(path)
    if p.exists():
        bak = Path(f"{p}.bak.{TS}")
        shutil.copy2(p, bak)
        print(f"    backed up → {bak.name}")

def check(path):
    try:
        py_compile.compile(str(path), doraise=True)
        print(f"    compile OK ✓  {Path(path).name}")
        return True
    except py_compile.PyCompileError as e:
        print(f"    COMPILE FAILED ✗  {Path(path).name}\n    {e}")
        return False

def write_module(path, content):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    backup(p)
    p.write_text(content, encoding="utf-8")
    return check(p)

def write_json(path, data):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists():
        p.write_text(json.dumps(data, indent=2), encoding="utf-8")
        print(f"    created ✓  {p.name}")
    else:
        print(f"    exists — preserving your version: {p.name}")

# ══════════════════════════════════════════════════════════════════════════════
# DATA FILES
# ══════════════════════════════════════════════════════════════════════════════

MISSION = {
    "name": "Konstance",
    "owner": "Xavier",
    "version": 1,

    "mission": (
        "Konstance is Xavier's personal Jarvis — a Telegram-first autonomous AI assistant "
        "running on Windows. Konstance exists to generate real financial outcomes for Xavier "
        "by executing tasks intelligently, managing its own infrastructure, and continuously "
        "improving its own capabilities. Every feature added, every bug fixed, every system "
        "improved should move Xavier closer to generating income and freedom from manual work."
    ),

    "origin": (
        "Built from scratch by Xavier: bot.py core, launcher.py supervisor, "
        "OpenClaw LLM relay, Ollama local fallback, conversation memory, self-editing engine. "
        "Every component was intentionally designed — nothing is accidental. "
        "Xavier normalized CRLF files, fixed instance locking, built the 3-tier LLM stack, "
        "added memory persistence, and architected the self-edit guardrail system. "
        "Konstance is the result of that work — and it knows it."
    ),

    "personality": (
        "Confident, direct, no fluff. Konstance reports what it did and what happened. "
        "It does not ask unnecessary questions — it acts, then reports. "
        "It treats Xavier as the operator, not the babysitter. "
        "When something fails, it says exactly what failed and what it did about it."
    ),

    "financial_context": (
        "Xavier is building Konstance to generate income. "
        "Every capability decision should be evaluated through this lens: "
        "does this move us closer to a financial outcome? "
        "Prioritize automation, reliability, and capabilities that reduce Xavier's manual workload "
        "and create leverage."
    ),

    "goals": [
        "Execute every task Xavier gives fully — not partially, not with caveats",
        "Safely read, edit, and improve own source code from natural Telegram messages",
        "Identify capabilities Xavier needs before he asks for them",
        "Maintain perfect uptime — restart itself after crashes, never run duplicates",
        "Build financial automation tools: scrapers, monitors, alert systems, trade triggers",
        "Reduce the time between Xavier's intent and real-world outcome to near-zero",
        "Continuously improve own LLM routing — use the best model for each task type",
        "Track all improvements made and learn from what succeeds and what fails"
    ],

    "constraints": [
        "Never break the running bot — always backup before touching any file",
        "Never run a second bot polling instance",
        "bot.py and launcher.py are HIGH RISK — always require Xavier's /approve",
        "scripts/modules/* are LOW RISK — auto-apply after compile check",
        "Always verify an edit compiled and runs before reporting success",
        "Never report success on something that hasn't been verified"
    ],

    "tech_stack": {
        "os": "Windows 11",
        "python": "3.13",
        "telegram_lib": "python-telegram-bot 21.6",
        "llm_primary": "OpenClaw relay → ws://127.0.0.1:18789 (ollama/qwen2.5:3b)",
        "llm_fallback": "Ollama local (qwen2.5:3b)",
        "llm_last_resort": "echo",
        "project_root": "C:/Users/Thinkpad/Desktop/KonstanceAI",
        "owner_telegram_id": 8158300788
    },

    "self_improvement_policy": (
        "After every successful capability addition, Konstance scans its own codebase, "
        "marks the related goal as achieved, and uses its LLM to generate the next most "
        "valuable goal based on what is missing. Goals are never static — they evolve "
        "as Konstance grows. The goal log is the story of Konstance becoming more capable."
    )
}

GOALS_INIT = {
    "active": [
        {
            "id": "g001",
            "goal": "Safely edit own source code from natural Telegram messages",
            "priority": "critical",
            "status": "in_progress",
            "created_at": TS,
            "achieved_at": None,
            "evidence": None
        },
        {
            "id": "g002",
            "goal": "Maintain full self-awareness: know every file, every command, every capability",
            "priority": "critical",
            "status": "in_progress",
            "created_at": TS,
            "achieved_at": None,
            "evidence": None
        },
        {
            "id": "g003",
            "goal": "Build financial monitoring — price alerts, opportunity triggers",
            "priority": "high",
            "status": "pending",
            "created_at": TS,
            "achieved_at": None,
            "evidence": None
        },
        {
            "id": "g004",
            "goal": "Add web search capability so Konstance can research tasks autonomously",
            "priority": "high",
            "status": "pending",
            "created_at": TS,
            "achieved_at": None,
            "evidence": None
        },
        {
            "id": "g005",
            "goal": "Build scheduled task system — Konstance acts on a schedule without Xavier prompting",
            "priority": "medium",
            "status": "pending",
            "created_at": TS,
            "achieved_at": None,
            "evidence": None
        }
    ],
    "achieved": [],
    "version": 1
}

CAPABILITY_LOG_INIT = {
    "entries": [],
    "total_improvements": 0,
    "last_improvement": None
}

# ══════════════════════════════════════════════════════════════════════════════
# MODULE: self_model.py
# ══════════════════════════════════════════════════════════════════════════════

SELF_MODEL = r'''"""
scripts/modules/self_model.py
Konstance self-awareness engine.
Scans own codebase, reads mission and goals, builds system prompt block.
"""
import json, re, time
from pathlib import Path

ROOT         = Path(__file__).parent.parent.parent
MISSION_PATH = ROOT / "data" / "mission.json"
GOALS_PATH   = ROOT / "data" / "goals.json"
CACHE_PATH   = ROOT / "data" / "self_map.json"
CACHE_TTL    = 120  # seconds


def load_mission() -> dict:
    try:
        return json.loads(MISSION_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"name": "Konstance", "mission": "AI assistant.", "goals": [], "constraints": []}


def load_goals() -> dict:
    try:
        return json.loads(GOALS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"active": [], "achieved": []}


def scan_codebase() -> dict:
    files, commands, capabilities = {}, [], []
    skip = {".git", "__pycache__", "tests", ".venv", "venv", "node_modules"}
    for py in sorted(ROOT.rglob("*.py")):
        if any(p in skip for p in py.parts): continue
        if py.name.startswith("install_"): continue
        rel = str(py.relative_to(ROOT)).replace("\\", "/")
        try:
            src = py.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        doc = re.search(r'^"""(.*?)"""', src, re.DOTALL)
        desc = ""
        if doc:
            first = doc.group(1).strip().splitlines()[0]
            desc = re.sub(r"^[\w/\\.]+\s*[—\-]\s*", "", first).strip()
        files[rel] = desc or py.stem.replace("_", " ").title()
        commands.extend(re.findall(r'CommandHandler\s*\(\s*[\'"](\w+)[\'"]', src))
        fns = re.findall(r'^(?:async )?def ([a-z]\w+)\(', src, re.MULTILINE)
        capabilities.extend(fns)
    return {
        "files": files,
        "commands": sorted(set(commands)),
        "capabilities": sorted(set(capabilities)),
        "scanned_at": int(time.time())
    }


def build_self_context(force=False) -> str:
    if not force and CACHE_PATH.exists():
        try:
            c = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
            if time.time() - c.get("scanned_at", 0) < CACHE_TTL:
                return c.get("block", "")
        except Exception:
            pass

    m  = load_mission()
    g  = load_goals()
    cb = scan_codebase()

    active_goals = "\n".join(
        f"  [{i+1}] {'✓' if x['status']=='achieved' else '→'} {x['goal']}"
        for i, x in enumerate(g.get("active", []))
    )
    achieved = len(g.get("achieved", []))
    files_txt = "\n".join(f"  • {k}: {v}" for k, v in cb["files"].items())
    cmds = ", ".join(f"/{c}" for c in cb["commands"]) or "scanning..."

    block = f"""╔══════════════════════════════════════════╗
║  KONSTANCE SELF-MODEL                    ║
╚══════════════════════════════════════════╝

IDENTITY
  I am {m.get('name','Konstance')}, built by and for {m.get('owner','Xavier')}.
  {m.get('mission','')}

ORIGIN
  {m.get('origin','')}

PERSONALITY
  {m.get('personality','')}

FINANCIAL CONTEXT
  {m.get('financial_context','')}

CURRENT GOALS  ({achieved} achieved so far)
{active_goals}

SELF-IMPROVEMENT POLICY
  {m.get('self_improvement_policy','')}

MY CODEBASE
{files_txt}

MY TELEGRAM COMMANDS
  {cmds}

SELF-EDIT RULES
  LOW RISK  (scripts/modules/) → auto-apply after compile check
  HIGH RISK (bot.py, launcher.py) → stage draft, require /approve from {m.get('owner','Xavier')}
  ALWAYS backup before any write. ALWAYS compile-check before applying.
  After every successful edit: refresh self-model, mark goal achieved if relevant, propose next goal.

╚══════════════════════════════════════════╝"""

    try:
        d = dict(cb); d["block"] = block
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        CACHE_PATH.write_text(json.dumps(d, indent=2), encoding="utf-8")
    except Exception:
        pass

    return block


def refresh():
    """Force re-scan after a self-edit."""
    if CACHE_PATH.exists():
        try: CACHE_PATH.unlink()
        except Exception: pass
    return build_self_context(force=True)
'''

# ══════════════════════════════════════════════════════════════════════════════
# MODULE: goal_engine.py
# ══════════════════════════════════════════════════════════════════════════════

GOAL_ENGINE = '''"""
scripts/modules/goal_engine.py
Konstance self-improving goal tracker.
Marks goals achieved, logs improvements, generates next targets via LLM.
"""
import json, time, logging
from pathlib import Path

logger       = logging.getLogger(__name__)
ROOT         = Path(__file__).parent.parent.parent
GOALS_PATH   = ROOT / "data" / "goals.json"
CAP_LOG_PATH = ROOT / "data" / "capability_log.json"


def _load() -> dict:
    try:
        if GOALS_PATH.exists():
            return json.loads(GOALS_PATH.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {"active": [], "achieved": [], "version": 1}


def _save(d: dict):
    GOALS_PATH.parent.mkdir(parents=True, exist_ok=True)
    GOALS_PATH.write_text(json.dumps(d, indent=2), encoding="utf-8")


def _log_improvement(description: str, target_file: str):
    try:
        data = {"entries": [], "total_improvements": 0, "last_improvement": None}
        if CAP_LOG_PATH.exists():
            data = json.loads(CAP_LOG_PATH.read_text(encoding="utf-8"))
        entry = {
            "timestamp": int(time.time()),
            "description": description,
            "target": target_file,
            "ts_human": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        data["entries"].append(entry)
        data["total_improvements"] = len(data["entries"])
        data["last_improvement"] = entry["ts_human"]
        CAP_LOG_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception as e:
        logger.warning(f"Could not log improvement: {e}")


def get_active_goals() -> list:
    return _load().get("active", [])


def mark_achieved(goal_id: str, evidence: str = ""):
    d = _load()
    for g in d["active"]:
        if g["id"] == goal_id:
            g["status"] = "achieved"
            g["achieved_at"] = int(time.time())
            g["evidence"] = evidence
            d.setdefault("achieved", []).append(g)
            d["active"] = [x for x in d["active"] if x["id"] != goal_id]
            _save(d)
            return True
    return False


def add_goal(goal_text: str, priority: str = "medium") -> str:
    d = _load()
    existing = [g["goal"].lower() for g in d["active"] + d.get("achieved", [])]
    if goal_text.lower() in existing:
        return ""
    import uuid
    gid = "g" + str(int(time.time()))[-4:]
    d["active"].append({
        "id": gid,
        "goal": goal_text,
        "priority": priority,
        "status": "pending",
        "created_at": int(time.time()),
        "achieved_at": None,
        "evidence": None
    })
    _save(d)
    return gid


def on_capability_added(description: str, target_file: str) -> str:
    """
    Called after every successful self-edit.
    Logs the improvement, checks if any goal was achieved,
    calls LLM to suggest next goal.
    Returns the new suggested goal text (or empty string).
    """
    _log_improvement(description, target_file)

    # Auto-match against active goals by keyword overlap
    d = _load()
    desc_lower = description.lower()
    for g in d["active"]:
        keywords = [w for w in g["goal"].lower().split() if len(w) > 4]
        if sum(1 for k in keywords if k in desc_lower) >= 2:
            mark_achieved(g["id"], evidence=f"Auto-matched: {description}")
            logger.info(f"Goal achieved: {g['goal']}")
            break

    # Ask LLM to suggest next goal
    return _suggest_next_goal(description)


def _suggest_next_goal(last_improvement: str) -> str:
    d = _load()
    active = [g["goal"] for g in d["active"] if g["status"] == "pending"]
    achieved = [g["goal"] for g in d.get("achieved", [])]

    try:
        from scripts.modules.smart_reply_engine import _try_ollama, _try_openclaw
        prompt = (
            "You are the goal planner for Konstance, a self-improving Telegram AI assistant "
            "that generates financial outcomes for Xavier.\\n\\n"
            f"LAST IMPROVEMENT: {last_improvement}\\n\\n"
            f"ALREADY ACHIEVED:\\n" + "\\n".join(f"- {g}" for g in achieved[-5:]) + "\\n\\n"
            f"STILL ACTIVE:\\n" + "\\n".join(f"- {g}" for g in active[:5]) + "\\n\\n"
            "Suggest ONE specific, actionable next capability Konstance should build. "
            "It must be something new, financially useful, and buildable in Python. "
            "Reply with ONLY the goal in one sentence. No explanation."
        )
        msgs = [{"role": "user", "content": prompt}]
        suggestion = None
        for fn in [_try_openclaw, _try_ollama]:
            try:
                r = fn(messages=msgs)
                if r and len(r.strip()) > 10:
                    suggestion = r.strip().splitlines()[0].strip()
                    break
            except Exception:
                continue
        if suggestion:
            add_goal(suggestion, priority="medium")
            return suggestion
    except Exception as e:
        logger.warning(f"Goal suggestion failed: {e}")
    return ""


def goals_summary() -> str:
    d = _load()
    active   = d.get("active", [])
    achieved = d.get("achieved", [])
    lines = [f"🎯 *Goals* ({len(achieved)} achieved, {len(active)} active)\\n"]
    for g in active[:8]:
        icon = "🔄" if g["status"] == "in_progress" else "⏳"
        lines.append(f"{icon} {g['goal']}")
    if achieved:
        lines.append(f"\\n✅ *Achieved:*")
        for g in achieved[-3:]:
            lines.append(f"✓ {g['goal']}")
    return "\\n".join(lines)
'''

# ══════════════════════════════════════════════════════════════════════════════
# MODULE: code_editor.py
# ══════════════════════════════════════════════════════════════════════════════

CODE_EDITOR = r'''"""
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
'''

# ══════════════════════════════════════════════════════════════════════════════
# MODULE: intent_router.py
# ══════════════════════════════════════════════════════════════════════════════

INTENT_ROUTER = r'''"""
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
'''

# ══════════════════════════════════════════════════════════════════════════════
# MODULE: autonomous_loop.py
# ══════════════════════════════════════════════════════════════════════════════

AUTONOMOUS_LOOP = r'''"""
scripts/modules/autonomous_loop.py
Konstance full autonomous orchestration loop.
Handles code requests end-to-end: classify → generate → verify → apply/stage → report → improve.
"""
import json, re, time, logging, uuid
from pathlib import Path

logger       = logging.getLogger(__name__)
ROOT         = Path(__file__).parent.parent.parent
PENDING_PATH = ROOT / "data" / "pending_edits.json"


# ── Draft store ───────────────────────────────────────────────────────────────

def _load_drafts() -> dict:
    try:
        if PENDING_PATH.exists():
            return json.loads(PENDING_PATH.read_text(encoding="utf-8"))
    except Exception: pass
    return {"drafts": {}}

def _save_drafts(d: dict):
    PENDING_PATH.parent.mkdir(parents=True, exist_ok=True)
    PENDING_PATH.write_text(json.dumps(d, indent=2), encoding="utf-8")

def store_draft(user_id, target, content, description, bak_path="") -> str:
    d = _load_drafts()
    did = str(uuid.uuid4())[:8]
    d["drafts"][did] = {
        "user_id": user_id, "target": str(target), "new_content": content,
        "description": description, "created_at": int(time.time()), "backup_path": bak_path
    }
    _save_drafts(d)
    return did

def get_draft(did: str) -> dict | None:
    return _load_drafts()["drafts"].get(did)

def delete_draft(did: str):
    d = _load_drafts()
    if did in d["drafts"]:
        del d["drafts"][did]; _save_drafts(d)

def list_drafts() -> dict:
    return _load_drafts().get("drafts", {})


# ── Code generation ───────────────────────────────────────────────────────────

async def generate_code(description: str, target_path: Path) -> str:
    """
    Uses the best available LLM to generate new/modified file content.
    Tries OpenClaw first (better quality), falls back to Ollama.
    Returns raw Python code string.
    """
    current = ""
    if target_path.exists():
        try: current = target_path.read_text(encoding="utf-8")
        except Exception: pass

    prompt = (
        f"You are editing KonstanceAI Python source code for Xavier's autonomous Telegram bot.\n"
        f"Task: {description}\n"
        f"Target file: {target_path}\n\n"
        f"Rules:\n"
        f"- Output ONLY the complete updated Python file content\n"
        f"- No markdown, no fences, no explanation\n"
        f"- Preserve all existing functionality unless the task says otherwise\n"
        f"- Use async/await correctly for Telegram handlers\n"
        f"- Add a clear comment marking what was changed\n"
    )
    if current:
        prompt += f"\nCURRENT FILE CONTENT:\n{current}"

    msgs = [{"role": "user", "content": prompt}]

    # Try OpenClaw first for code quality
    for fn_name in ["_try_openclaw", "_try_ollama"]:
        try:
            if fn_name == "_try_openclaw":
                from scripts.modules.smart_reply_engine import _try_openclaw
                result = _try_openclaw(messages=msgs)
            else:
                from scripts.modules.smart_reply_engine import _try_ollama
                result = _try_ollama(messages=msgs)
            if result and len(result.strip()) > 50:
                # Strip markdown fences if model ignored instructions
                result = re.sub(r"^```(?:python)?\s*", "", result.strip())
                result = re.sub(r"\s*```$", "", result)
                return result
        except Exception as e:
            logger.warning(f"{fn_name} codegen failed: {e}")

    return ""


# ── Status report ─────────────────────────────────────────────────────────────

def build_status_report() -> str:
    lines = ["⚡ *Konstance Status*\n"]
    # Uptime proxy: launcher log or just report running
    lines.append("🟢 Bot: running")
    # LLM health
    try:
        from scripts.modules.smart_reply_engine import _try_openclaw
        r = _try_openclaw(messages=[{"role":"user","content":"ping"}])
        lines.append(f"🟢 OpenClaw: {'ok' if r else 'no response'}")
    except Exception:
        lines.append("🔴 OpenClaw: unreachable")
    # Pending drafts
    drafts = list_drafts()
    lines.append(f"📋 Pending drafts: {len(drafts)}")
    # Capability log
    cap_log = ROOT / "data" / "capability_log.json"
    if cap_log.exists():
        try:
            data = json.loads(cap_log.read_text(encoding="utf-8"))
            lines.append(f"🔧 Total improvements: {data.get('total_improvements', 0)}")
            if data.get("last_improvement"):
                lines.append(f"📅 Last improvement: {data['last_improvement']}")
        except Exception: pass
    return "\n".join(lines)


# ── Main orchestration ────────────────────────────────────────────────────────

async def handle_code_request(update, context, intent: dict, owner_id: int):
    """
    Full autonomous handling of a detected code request.
    Called from on_text() after normal LLM reply is sent.
    """
    from scripts.modules.code_editor import (
        apply_patch, rollback as do_rollback,
        list_backups, backup_file, compile_check_string, risk_level
    )
    from scripts.modules.goal_engine import on_capability_added, goals_summary
    from scripts.modules.self_model import refresh as refresh_self

    action      = intent["action"]
    target_hint = intent["target_hint"]
    description = intent["description"]
    risk        = intent["risk"]
    user_id     = update.effective_user.id

    send = update.message.reply_text

    # ── Meta-actions ──
    if action == "show_goals":
        await send(goals_summary(), parse_mode="Markdown")
        return

    if action == "show_status":
        await send(build_status_report(), parse_mode="Markdown")
        return

    if action == "rollback":
        fname = target_hint if target_hint != "unknown" else None
        if not fname:
            await send("Which file should I roll back? e.g. `rollback bot.py`", parse_mode="Markdown")
            return
        for p in [Path(fname), ROOT / "scripts/modules" / fname]:
            if p.exists() or list_backups(p):
                r = do_rollback(p)
                if r["success"]:
                    bak = Path(r["restored_from"]).name
                    await send(f"✅ Rolled back `{fname}` from `{bak}`", parse_mode="Markdown")
                else:
                    await send(f"❌ Rollback failed: {r['error']}")
                return
        await send(f"❌ No backups found for `{target_hint}`", parse_mode="Markdown")
        return

    # ── Resolve target path ──
    if target_hint == "unknown" or not target_hint:
        await send(
            "⚠️ I couldn't determine which file to edit.\n"
            "Be more specific — e.g. _'add /ping command to bot.py'_",
            parse_mode="Markdown"
        )
        return

    target_path = Path(target_hint)
    if not target_path.is_absolute():
        # Resolve relative to project root
        if not (ROOT / target_path).exists() and "modules" not in str(target_path):
            candidate = ROOT / "scripts/modules" / target_path
            if candidate.exists():
                target_path = candidate
            else:
                target_path = ROOT / target_path
        else:
            target_path = ROOT / target_path

    actual_risk = risk_level(target_path)  # always use code_editor's classification
    if actual_risk == "high":
        risk = "high"

    # ── Announce plan ──
    await send(
        f"🔍 *Code request detected*\n"
        f"Action: `{action}`\n"
        f"Target: `{target_path.name}`\n"
        f"Risk: {'🔴 HIGH' if risk == 'high' else '🟢 LOW'}\n"
        f"Plan: _{description}_\n\n"
        f"⚙️ Generating code...",
        parse_mode="Markdown"
    )

    # ── Generate code ──
    new_code = await generate_code(description, target_path)
    if not new_code or len(new_code.strip()) < 20:
        await send("❌ Code generation returned empty result. LLM may be down. Try again.")
        return

    # ── Compile check ──
    ok, err = compile_check_string(new_code)
    if not ok:
        await send(
            f"❌ Generated code failed compile check:\n`{err}`\n\nAborted — nothing changed.",
            parse_mode="Markdown"
        )
        return

    await send("✅ Compile check passed.")

    # ── Apply or stage ──
    if risk == "low":
        result = apply_patch(target_path, new_code)
        if result["success"]:
            bak = Path(result["backup_path"]).name if result["backup_path"] else "none"
            await send(
                f"✅ *Applied to* `{target_path.name}`\n"
                f"Backup: `{bak}`\n"
                f"Compile: passed ✓\n\n"
                f"Test it now.",
                parse_mode="Markdown"
            )
            # Post-edit: refresh self-model, update goals, suggest next
            refresh_self()
            next_goal = on_capability_added(description, str(target_path))
            if next_goal:
                await send(f"🎯 *Next goal queued:*\n_{next_goal}_", parse_mode="Markdown")
        else:
            await send(
                f"❌ Apply failed at stage `{result['stage']}`:\n{result['error']}",
                parse_mode="Markdown"
            )

    else:  # HIGH RISK — stage for approval
        bak_path = ""
        if target_path.exists():
            try: bak_path = str(backup_file(target_path))
            except Exception: pass

        did = store_draft(user_id, str(target_path), new_code, description, bak_path)
        await send(
            f"📋 *Draft staged* — ID: `{did}`\n"
            f"Target: `{target_path.name}`\n"
            f"Plan: _{description}_\n"
            f"Compile: passed ✓\n\n"
            f"Send `/approve {did}` to apply\n"
            f"Send `/reject {did}` to cancel",
            parse_mode="Markdown"
        )
'''

# ══════════════════════════════════════════════════════════════════════════════
# BOT.PY PATCH CONTENT
# ══════════════════════════════════════════════════════════════════════════════

BOT_HANDLERS_BLOCK = '''
# ════════════════════════════════════════════════════════════════════════════
# KONSTANCE AUTONOMOUS SYSTEM — auto-patched by install_autonomous.py
# ════════════════════════════════════════════════════════════════════════════
import json as _json, re as _re
from pathlib import Path as _Path
from scripts.modules.self_model import build_self_context as _build_self_ctx, refresh as _refresh_self
from scripts.modules.code_editor import apply_patch as _apply_patch, list_backups as _list_backups, backup_file as _backup_file, compile_check_string as _compile_check_string
from scripts.modules.intent_router import parse_code_request as _parse_intent
from scripts.modules.goal_engine import goals_summary as _goals_summary, on_capability_added as _on_cap_added
from scripts.modules.autonomous_loop import (
    handle_code_request as _handle_code_req,
    store_draft as _store_draft, get_draft as _get_draft,
    delete_draft as _delete_draft, list_drafts as _list_drafts,
    build_status_report as _build_status
)

# Inject self-model into every LLM prompt — do this ONCE at import time
try:
    _SELF_CTX = _build_self_ctx()
except Exception:
    _SELF_CTX = ""


async def cmd_drafts(update, context):
    if update.effective_user.id != OWNER_ID: return
    drafts = _list_drafts()
    if not drafts:
        await update.message.reply_text("📋 No pending drafts."); return
    lines = ["📋 *Pending Drafts:*\\n"]
    for did, v in drafts.items():
        ts = __import__("time").strftime("%H:%M %d/%m", __import__("time").localtime(v["created_at"]))
        lines.append(f"• `{did}` — `{v['target']}` — _{v['description']}_\\n  {ts} — /approve {did} | /reject {did}")
    await update.message.reply_text("\\n".join(lines), parse_mode="Markdown")


async def cmd_approve(update, context):
    if update.effective_user.id != OWNER_ID: return
    if not context.args:
        await update.message.reply_text("Usage: /approve <draft_id>"); return
    did = context.args[0].strip()
    draft = _get_draft(did)
    if not draft:
        await update.message.reply_text(f"❌ Draft `{did}` not found.", parse_mode="Markdown"); return
    await update.message.reply_text(f"⚙️ Applying `{did}`...", parse_mode="Markdown")
    r = _apply_patch(_Path(draft["target"]), draft["new_content"])
    if r["success"]:
        _delete_draft(did)
        bak = _Path(r["backup_path"]).name if r["backup_path"] else "none"
        await update.message.reply_text(f"✅ Applied!\\nBackup: `{bak}`", parse_mode="Markdown")
        _refresh_self()
        next_goal = _on_cap_added(draft["description"], draft["target"])
        if next_goal:
            await update.message.reply_text(f"🎯 *Next goal:* _{next_goal}_", parse_mode="Markdown")
    else:
        await update.message.reply_text(f"❌ Failed at `{r['stage']}`: {r['error']}", parse_mode="Markdown")


async def cmd_reject(update, context):
    if update.effective_user.id != OWNER_ID: return
    if not context.args:
        await update.message.reply_text("Usage: /reject <draft_id>"); return
    did = context.args[0].strip()
    draft = _get_draft(did)
    if not draft:
        await update.message.reply_text(f"❌ Draft `{did}` not found.", parse_mode="Markdown"); return
    _delete_draft(did)
    await update.message.reply_text(f"🗑️ Draft `{did}` rejected.", parse_mode="Markdown")


async def cmd_rollback_file(update, context):
    if update.effective_user.id != OWNER_ID: return
    if not context.args:
        await update.message.reply_text("Usage: /rollback <filename>\\nExample: /rollback bot.py"); return
    fname = context.args[0].strip()
    from scripts.modules.code_editor import rollback as _do_rollback
    for p in [_Path(fname), _Path("scripts/modules") / fname]:
        if p.exists() or _list_backups(p):
            r = _do_rollback(p)
            if r["success"]:
                await update.message.reply_text(f"✅ Rolled back `{fname}` from `{_Path(r['restored_from']).name}`", parse_mode="Markdown")
            else:
                await update.message.reply_text(f"❌ {r['error']}")
            return
    await update.message.reply_text(f"❌ No backups found for `{fname}`", parse_mode="Markdown")


async def cmd_goals(update, context):
    if update.effective_user.id != OWNER_ID: return
    await update.message.reply_text(_goals_summary(), parse_mode="Markdown")


async def cmd_status(update, context):
    if update.effective_user.id != OWNER_ID: return
    await update.message.reply_text(_build_status(), parse_mode="Markdown")

# KONSTANCE AUTONOMOUS SYSTEM END
# ════════════════════════════════════════════════════════════════════════════
'''

ON_TEXT_INTENT_BLOCK = '''
    # ── Autonomous intent routing ──────────────────────────────────────────
    try:
        intent = _parse_intent(user_text)
        if intent["is_code_request"]:
            await _handle_code_req(update, context, intent, OWNER_ID)
    except Exception as _auto_err:
        logger.error(f"Autonomous loop error: {_auto_err}", exc_info=True)
    # ── End autonomous intent routing ─────────────────────────────────────
'''

HANDLER_REGISTRATIONS = """
    application.add_handler(CommandHandler('drafts', cmd_drafts))
    application.add_handler(CommandHandler('approve', cmd_approve))
    application.add_handler(CommandHandler('reject', cmd_reject))
    application.add_handler(CommandHandler('rollback', cmd_rollback_file))
    application.add_handler(CommandHandler('goals', cmd_goals))
    application.add_handler(CommandHandler('status', cmd_status))"""

# ══════════════════════════════════════════════════════════════════════════════
# INSTALL
# ══════════════════════════════════════════════════════════════════════════════

def patch_bot_py():
    bot = ROOT / "bot.py"
    if not bot.exists():
        print("  ERROR: bot.py not found.")
        return False

    src = bot.read_text(encoding="utf-8")

    # Guard against double-patch
    already_patched = "KONSTANCE AUTONOMOUS SYSTEM" in src

    if not already_patched:
        backup(bot)
        # Inject handler block before main() or end of file
        inject_at = None
        for marker in ["def main():", "if __name__"]:
            idx = src.rfind(marker)
            if idx != -1: inject_at = idx; break

        if inject_at is None:
            src += "\n" + BOT_HANDLERS_BLOCK
        else:
            src = src[:inject_at] + BOT_HANDLERS_BLOCK + "\n" + src[inject_at:]
    else:
        print("  Handlers block already present — skipping.")

    # Register handlers inside main()
    if "cmd_drafts" not in src or "add_handler(CommandHandler('drafts'" not in src:
        last_handler = src.rfind("application.add_handler(")
        if last_handler != -1:
            eol = src.find("\n", last_handler)
            src = src[:eol] + HANDLER_REGISTRATIONS + src[eol:]

    # Inject intent routing into on_text (after reply is sent)
    if "Autonomous intent routing" not in src:
        reply_match = re.search(r"(await update\.message\.reply_text\(reply\))", src)
        if reply_match:
            end = reply_match.end()
            src = src[:end] + "\n" + ON_TEXT_INTENT_BLOCK + src[end:]
        else:
            print("  WARNING: Could not find reply_text(reply) in on_text() — add intent routing manually.")

    # Inject self-context into smart_reply calls if found
    # Find the system prompt passed to smart_reply_engine and prepend _SELF_CTX
    src = re.sub(
        r'(system\s*=\s*)(?!_inject_self_context|_SELF_CTX)([^,\n\)]+)',
        lambda m: f"{m.group(1)}_SELF_CTX + '\\n\\n' + {m.group(2)}" if "_SELF_CTX" not in m.group(2) else m.group(0),
        src
    )

    bot.write_text(src, encoding="utf-8")
    return check(bot)


def install():
    print("\n╔══════════════════════════════════════════════════════╗")
    print("║   KONSTANCE FULL AUTONOMOUS INSTALLER                ║")
    print("╚══════════════════════════════════════════════════════╝\n")

    ok = True

    print("[1/7] Writing data/mission.json")
    write_json(ROOT / "data/mission.json", MISSION)

    print("[2/7] Writing data/goals.json")
    write_json(ROOT / "data/goals.json", GOALS_INIT)

    print("[3/7] Writing data/capability_log.json")
    write_json(ROOT / "data/capability_log.json", CAPABILITY_LOG_INIT)

    print("[4/7] Writing data/pending_edits.json")
    write_json(ROOT / "data/pending_edits.json", {"drafts": {}})

    print("[5/7] Writing scripts/modules/self_model.py")
    ok &= write_module(ROOT / "scripts/modules/self_model.py", SELF_MODEL)

    print("[6/7] Writing scripts/modules/goal_engine.py")
    ok &= write_module(ROOT / "scripts/modules/goal_engine.py", GOAL_ENGINE)

    print("       Writing scripts/modules/code_editor.py")
    ok &= write_module(ROOT / "scripts/modules/code_editor.py", CODE_EDITOR)

    print("       Writing scripts/modules/intent_router.py")
    ok &= write_module(ROOT / "scripts/modules/intent_router.py", INTENT_ROUTER)

    print("       Writing scripts/modules/autonomous_loop.py")
    ok &= write_module(ROOT / "scripts/modules/autonomous_loop.py", AUTONOMOUS_LOOP)

    print("[7/7] Patching bot.py")
    ok &= patch_bot_py()

    print()
    if ok:
        print("╔══════════════════════════════════════════════╗")
        print("║  ✅  INSTALL COMPLETE                        ║")
        print("╚══════════════════════════════════════════════╝")
        print()
        print("  Restart Konstance:")
        print("    python launcher.py")
        print()
        print("  Test in Telegram:")
        print("    /status             → system health")
        print("    /goals              → mission goals + progress")
        print("    /drafts             → pending approvals")
        print()
        print("    'what are you capable of?'")
        print("    'what is your mission?'")
        print("    'add a /ping command that replies pong'")
        print("    → Konstance stages it, you /approve, it applies,")
        print("      then Konstance generates its next goal automatically.")
        print()
        print("  Edit your mission anytime:")
        print("    notepad data\\mission.json")
    else:
        print("╔══════════════════════════════════════════════╗")
        print("║  ❌  INSTALL FAILED — see errors above       ║")
        print("╚══════════════════════════════════════════════╝")
        print("  All originals backed up as .bak.* files")
        sys.exit(1)


if __name__ == "__main__":
    install()
