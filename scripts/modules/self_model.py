"""
scripts/modules/self_model.py
Konstance self-awareness engine.
Scans own codebase, reads mission and goals, builds system prompt block.
"""
import json, re, time
from pathlib import Path

ROOT         = Path(__file__).parent.parent.parent
CTX_DIR      = ROOT / ".konstance_context"
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
    for p in (CTX_DIR / "goals.json", GOALS_PATH):
        try:
            if p.exists():
                return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
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

    name = m.get("name") or m.get("identity", "Konstance")
    mission = m.get("mission") or m.get("primary_goal") or m.get("role", "")
    personality = m.get("personality") or m.get("role", "")
    financial = m.get("financial_context") or "\n".join(m.get("pillars", []))
    self_improve = m.get("self_improvement_policy") or "Add capabilities in scripts/modules/. Keep bot.py thin. Backup before every write."

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
  I am {name}, built by and for {m.get('owner','Xavier')}.
  {mission}

ORIGIN
  {m.get('origin','')}

PERSONALITY
  {personality}

FINANCIAL CONTEXT
  {financial}

CURRENT GOALS  ({achieved} achieved so far)
{active_goals}

SELF-IMPROVEMENT POLICY
  {self_improve}

MY CODEBASE
{files_txt}

MY TELEGRAM COMMANDS
  {cmds}

SELF-EDIT RULES
  LOW RISK  (scripts/modules/) → auto-apply after compile check
  HIGH RISK (bot.py, launcher.py) → stage draft, reply yes/approve to apply
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
