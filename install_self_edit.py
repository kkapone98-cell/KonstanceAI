"""
KONSTANCE SELF-EDIT INSTALLER
Run this once from your project root:

    cd C:/Users/Thinkpad/Desktop/KonstanceAI
    python install_self_edit.py

That's it. It will:
  - Write code_editor.py and intent_router.py into scripts/modules/
  - Create data/pending_edits.json
  - Patch bot.py with the new commands and intent routing
  - Compile-check everything
  - Print what to test in Telegram
"""

import os, sys, shutil, time, py_compile, tempfile, re
from pathlib import Path

ROOT = Path(__file__).parent
TS   = int(time.time())

# ─── Helpers ─────────────────────────────────────────────────────────────────

def backup(path):
    if path.exists():
        bak = Path(f"{path}.bak.{TS}")
        shutil.copy2(path, bak)
        print(f"  backed up → {bak.name}")

def check(path):
    try:
        py_compile.compile(str(path), doraise=True)
        print(f"  compile OK ✓  {path}")
        return True
    except py_compile.PyCompileError as e:
        print(f"  COMPILE FAILED ✗  {path}\n  {e}")
        return False

def write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    backup(path)
    path.write_text(content, encoding="utf-8")
    return check(path)

# ─── File contents ────────────────────────────────────────────────────────────

CODE_EDITOR = '''"""scripts/modules/code_editor.py — KonstanceAI safe edit engine"""
import os, shutil, time, py_compile, tempfile, glob
from pathlib import Path

HIGH_RISK = {"bot.py", "launcher.py", "main.py"}

def risk_level(path):
    name = Path(path).name
    if name in HIGH_RISK: return "high"
    if "scripts" in Path(path).parts: return "low"
    return "high"

def backup_file(path):
    path = Path(path)
    if not path.exists(): raise FileNotFoundError(f"Not found: {path}")
    bak = Path(f"{path}.bak.{int(time.time())}")
    shutil.copy2(path, bak)
    return bak

def list_backups(path):
    return sorted([Path(b) for b in glob.glob(str(path) + ".bak.*")], reverse=True)

def compile_check(path):
    try:
        py_compile.compile(str(path), doraise=True)
        return (True, "")
    except py_compile.PyCompileError as e:
        return (False, str(e))

def compile_check_string(code):
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
            f.write(code); tmp = f.name
        return compile_check(Path(tmp))
    finally:
        if tmp and os.path.exists(tmp): os.unlink(tmp)

def apply_patch(path, new_content):
    path = Path(path)
    result = {"success": False, "backup_path": None, "error": None, "stage": "init"}
    result["stage"] = "pre_compile"
    ok, err = compile_check_string(new_content)
    if not ok:
        result["error"] = f"Pre-compile failed: {err}"; return result
    result["stage"] = "backup"
    try:
        if path.exists():
            bak = backup_file(path); result["backup_path"] = str(bak)
    except Exception as e:
        result["error"] = f"Backup failed: {e}"; return result
    result["stage"] = "write"
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(new_content, encoding="utf-8")
    except Exception as e:
        result["error"] = f"Write failed: {e}"
        if result["backup_path"]: shutil.copy2(result["backup_path"], path)
        return result
    result["stage"] = "post_compile"
    ok, err = compile_check(path)
    if not ok:
        result["error"] = f"Post-compile failed: {err}"
        if result["backup_path"]:
            shutil.copy2(result["backup_path"], path)
            result["error"] += " — rolled back."
        return result
    result["success"] = True; result["stage"] = "done"
    return result

def rollback(path):
    path = Path(path)
    backups = list_backups(path)
    if not backups: return {"success": False, "restored_from": None, "error": f"No backups for {path.name}"}
    try:
        shutil.copy2(backups[0], path)
        return {"success": True, "restored_from": str(backups[0]), "error": None}
    except Exception as e:
        return {"success": False, "restored_from": None, "error": str(e)}
'''

INTENT_ROUTER = '''"""scripts/modules/intent_router.py — plain language → code action mapper"""
import json, logging, re
logger = logging.getLogger(__name__)

INTENT_SYSTEM = """Classify if a message is a request to edit KonstanceAI source code.
Return ONLY raw JSON (no markdown):
{"is_code_request":bool,"action":"add_feature|fix_bug|improve|rollback|show_drafts|none","target_hint":"bot.py|scripts/modules/|launcher.py|unknown","description":"one sentence","risk":"high|low|unknown"}
Risk: bot.py/launcher.py=high, scripts/modules/*=low, unknown=high.
Examples:
"add rate limiting" -> {"is_code_request":true,"action":"add_feature","target_hint":"bot.py","description":"Add per-user rate limiting","risk":"high"}
"what time is it" -> {"is_code_request":false,"action":"none","target_hint":"unknown","description":"","risk":"unknown"}
"rollback bot.py" -> {"is_code_request":true,"action":"rollback","target_hint":"bot.py","description":"Rollback bot.py to last backup","risk":"high"}"""

_KEYWORDS = [r"\\badd\\b.*(command|feature|handler|limit|filter)",r"\\bfix\\b",r"\\bimprove\\b",r"\\brollback\\b",r"\\bdraft",r"\\bpending\\b",r"\\brate.?limit",r"\\bcommand\\b.*\\/"]

def _keyword_hit(text):
    lower = text.lower()
    return any(re.search(p, lower) for p in _KEYWORDS)

def _extract_json(raw):
    raw = re.sub(r"^```(?:json)?\\s*","",raw.strip()); raw = re.sub(r"\\s*```$","",raw)
    try: return json.loads(raw)
    except Exception:
        m = re.search(r"\\{.*\\}", raw, re.DOTALL)
        if m:
            try: return json.loads(m.group(0))
            except: pass
    return None

def _call_llm(text):
    msgs = [{"role":"user","content":text}]
    for fn_name in ["_try_openclaw","_try_ollama"]:
        try:
            from scripts.modules.smart_reply_engine import _try_openclaw, _try_ollama
            fn = _try_openclaw if fn_name == "_try_openclaw" else _try_ollama
            r = fn(messages=msgs, system_override=INTENT_SYSTEM)
            if r: return r
        except Exception as e:
            logger.debug(f"{fn_name} failed: {e}")
    return ""

def parse_code_request(text, history=None):
    lower = text.lower().strip()
    if len(text) < 5: return {"is_code_request":False,"action":"none","target_hint":"unknown","description":"","risk":"unknown"}
    if re.search(r"\\b(rollback|revert|restore)\\b", lower):
        m = re.search(r"([\\w_]+\\.py)", lower)
        t = m.group(1) if m else "unknown"
        return {"is_code_request":True,"action":"rollback","target_hint":t,"description":f"Rollback {t}","risk":"high"}
    if re.search(r"\\b(draft|pending|approval)\\b", lower):
        return {"is_code_request":True,"action":"show_drafts","target_hint":"unknown","description":"List pending drafts","risk":"low"}
    if not _keyword_hit(text):
        return {"is_code_request":False,"action":"none","target_hint":"unknown","description":"","risk":"unknown"}
    try:
        raw = _call_llm(text)
        if raw:
            p = _extract_json(raw)
            if p and "is_code_request" in p:
                return {"is_code_request":bool(p.get("is_code_request")),"action":p.get("action","none"),"target_hint":p.get("target_hint","unknown"),"description":p.get("description",""),"risk":p.get("risk","high")}
    except Exception as e:
        logger.warning(f"Intent LLM error: {e}")
    return {"is_code_request":True,"action":"add_feature","target_hint":"unknown","description":text[:200],"risk":"high"}
'''

BOT_HANDLERS = '''
# ════════════════════════════════════════════════════════════
# SELF-EDIT FEATURE — auto-added by install_self_edit.py
# ════════════════════════════════════════════════════════════
import json, uuid, re as _re
from pathlib import Path as _Path
from scripts.modules.code_editor import (
    apply_patch, rollback, list_backups, backup_file, compile_check_string
)
from scripts.modules.intent_router import parse_code_request

_PENDING = _Path("data/pending_edits.json")

def _load_drafts():
    try:
        if _PENDING.exists(): return json.loads(_PENDING.read_text(encoding="utf-8"))
    except Exception: pass
    return {"drafts": {}}

def _save_drafts(d):
    _PENDING.parent.mkdir(parents=True, exist_ok=True)
    _PENDING.write_text(json.dumps(d, indent=2), encoding="utf-8")

def _store_draft(uid, target, content, desc, bak):
    d = _load_drafts()
    did = str(uuid.uuid4())[:8]
    d["drafts"][did] = {"user_id":uid,"target":target,"new_content":content,
                        "description":desc,"created_at":int(__import__("time").time()),"backup_path":bak}
    _save_drafts(d); return did

async def cmd_drafts(update, context):
    if update.effective_user.id != OWNER_ID: return
    d = _load_drafts()["drafts"]
    if not d: await update.message.reply_text("📋 No pending drafts."); return
    lines = ["📋 *Pending Drafts:*\\n"]
    for did, v in d.items():
        lines.append(f"• `{did}` — `{v[\'target\']}` — _{v[\'description\']}_\\n  /approve {did}  |  /reject {did}")
    await update.message.reply_text("\\n".join(lines), parse_mode="Markdown")

async def cmd_approve(update, context):
    if update.effective_user.id != OWNER_ID: return
    if not context.args: await update.message.reply_text("Usage: /approve <id>"); return
    did = context.args[0]; d = _load_drafts()
    draft = d["drafts"].get(did)
    if not draft: await update.message.reply_text(f"❌ Draft `{did}` not found.", parse_mode="Markdown"); return
    await update.message.reply_text(f"⚙️ Applying `{did}`...", parse_mode="Markdown")
    r = apply_patch(_Path(draft["target"]), draft["new_content"])
    if r["success"]:
        del d["drafts"][did]; _save_drafts(d)
        bak = _Path(r["backup_path"]).name if r["backup_path"] else "none"
        await update.message.reply_text(f"✅ Applied!\\nBackup: `{bak}`", parse_mode="Markdown")
    else:
        await update.message.reply_text(f"❌ Failed at `{r[\'stage\']}`: {r[\'error\']}", parse_mode="Markdown")

async def cmd_reject(update, context):
    if update.effective_user.id != OWNER_ID: return
    if not context.args: await update.message.reply_text("Usage: /reject <id>"); return
    did = context.args[0]; d = _load_drafts()
    if did not in d["drafts"]: await update.message.reply_text(f"❌ Draft `{did}` not found.", parse_mode="Markdown"); return
    desc = d["drafts"][did]["description"]; del d["drafts"][did]; _save_drafts(d)
    await update.message.reply_text(f"🗑️ Draft `{did}` rejected.\\n_{desc}_", parse_mode="Markdown")

async def cmd_rollback_file(update, context):
    if update.effective_user.id != OWNER_ID: return
    if not context.args: await update.message.reply_text("Usage: /rollback <filename>"); return
    fname = context.args[0]
    for p in [_Path(fname), _Path("scripts/modules") / fname]:
        if p.exists() or list_backups(p):
            r = rollback(p)
            if r["success"]: await update.message.reply_text(f"✅ Rolled back `{fname}` from `{_Path(r[\'restored_from\']).name}`", parse_mode="Markdown")
            else: await update.message.reply_text(f"❌ Rollback failed: {r[\'error\']}")
            return
    await update.message.reply_text(f"❌ No backups found for `{fname}`", parse_mode="Markdown")

# SELF-EDIT FEATURE END
# ════════════════════════════════════════════════════════════
'''

ON_TEXT_ADDITION = '''
    # ── Intent routing (self-edit) ──
    try:
        intent = parse_code_request(user_text)
        if intent["is_code_request"]:
            action = intent["action"]; target = intent["target_hint"]
            desc = intent["description"]; risk = intent["risk"]
            if action == "show_drafts":
                await cmd_drafts(update, context); return
            if action == "rollback":
                context.args = [target] if target != "unknown" else []
                await cmd_rollback_file(update, context); return
            await update.message.reply_text(
                f"🔍 Code request — *{action}* on `{target}` (risk: {risk})\\n_{desc}_\\n\\n⚙️ Generating...",
                parse_mode="Markdown")
            target_path = _Path(target)
            current = target_path.read_text(encoding="utf-8") if target_path.exists() else ""
            from scripts.modules.smart_reply_engine import smart_reply
            new_code = await smart_reply(
                f"Edit KonstanceAI source. Task: {desc}\\nFile: {target}\\n"
                f"Output ONLY raw Python, no markdown fences.\\n\\nCURRENT FILE:\\n{current}")
            new_code = _re.sub(r"^```(?:python)?\\s*","",new_code.strip())
            new_code = _re.sub(r"\\s*```$","",new_code)
            ok, err = compile_check_string(new_code)
            if not ok:
                await update.message.reply_text(f"❌ Compile failed:\\n`{err}`\\nAborted.", parse_mode="Markdown"); return
            if risk == "low":
                r = apply_patch(target_path, new_code)
                if r["success"]:
                    bak = _Path(r["backup_path"]).name if r["backup_path"] else "none"
                    await update.message.reply_text(f"✅ Applied to `{target}`\\nBackup: `{bak}`\\nTest it now.", parse_mode="Markdown")
                else:
                    await update.message.reply_text(f"❌ Failed: {r[\'error\']}", parse_mode="Markdown")
            else:
                bak_path = ""
                if target_path.exists():
                    try: bak_path = str(backup_file(target_path))
                    except Exception: pass
                did = _store_draft(update.effective_user.id, str(target_path), new_code, desc, bak_path)
                await update.message.reply_text(
                    f"📋 Staged as draft `{did}`\\n`{target}` — _{desc}_\\nCompile: ✓\\n\\n/approve {did} to apply | /reject {did} to cancel",
                    parse_mode="Markdown")
    except Exception as _e:
        logger.error(f"Intent routing error: {_e}", exc_info=True)
    # ── End intent routing ──
'''

# ─── Install ──────────────────────────────────────────────────────────────────

def install():
    print("\n╔═══════════════════════════════════════╗")
    print("║  KonstanceAI Self-Edit Installer      ║")
    print("╚═══════════════════════════════════════╝\n")

    ok = True

    # 1. code_editor.py
    print("[1/4] Writing scripts/modules/code_editor.py")
    ok &= write(ROOT / "scripts/modules/code_editor.py", CODE_EDITOR)

    # 2. intent_router.py
    print("\n[2/4] Writing scripts/modules/intent_router.py")
    ok &= write(ROOT / "scripts/modules/intent_router.py", INTENT_ROUTER)

    # 3. pending_edits.json
    print("\n[3/4] Creating data/pending_edits.json")
    pf = ROOT / "data/pending_edits.json"
    if not pf.exists():
        pf.parent.mkdir(parents=True, exist_ok=True)
        pf.write_text('{"drafts": {}}', encoding="utf-8")
        print(f"  created ✓  {pf}")
    else:
        print(f"  already exists, skipping")

    # 4. Patch bot.py
    print("\n[4/4] Patching bot.py")
    bot = ROOT / "bot.py"
    if not bot.exists():
        print("  ERROR: bot.py not found — are you in the right directory?")
        sys.exit(1)

    src = bot.read_text(encoding="utf-8")

    # Check if already patched
    if "SELF-EDIT FEATURE" in src:
        print("  Already patched — skipping handler injection")
    else:
        backup(bot)
        # Inject handlers block right before the last def main() or if __name__ block
        inject_point = None
        for marker in ["def main():", "if __name__"]:
            idx = src.rfind(marker)
            if idx != -1:
                inject_point = idx
                break
        if inject_point is None:
            print("  WARNING: Could not find main() — appending handlers to end of file")
            src += "\n" + BOT_HANDLERS
        else:
            src = src[:inject_point] + BOT_HANDLERS + "\n" + src[inject_point:]

        # Register handlers inside main()
        if "CommandHandler" in src and "cmd_drafts" not in src:
            # Find add_handler block and append after last add_handler call
            last_handler = src.rfind("application.add_handler(")
            if last_handler != -1:
                eol = src.find("\n", last_handler)
                registration = (
                    "\n    application.add_handler(CommandHandler('drafts', cmd_drafts))"
                    "\n    application.add_handler(CommandHandler('approve', cmd_approve))"
                    "\n    application.add_handler(CommandHandler('reject', cmd_reject))"
                    "\n    application.add_handler(CommandHandler('rollback', cmd_rollback_file))"
                )
                src = src[:eol] + registration + src[eol:]

        # Inject intent routing into on_text — after the reply is sent
        # Look for the pattern where a reply is sent in on_text
        on_text_reply = re.search(r"(await update\.message\.reply_text\(reply\))", src)
        if on_text_reply and "Intent routing" not in src:
            end = on_text_reply.end()
            src = src[:end] + "\n" + ON_TEXT_ADDITION + src[end:]

        bot.write_text(src, encoding="utf-8")
        ok &= check(bot)

    if ok:
        print("\n✅ All done!\n")
        print("Restart Konstance:  python launcher.py")
        print("\nTest in Telegram:")
        print("  /drafts")
        print("  add a /ping command that replies with pong")
        print("  rollback bot.py")
    else:
        print("\n❌ One or more steps failed — check errors above.")
        print("Backups of original files are in the project root (.bak.*)")
        sys.exit(1)

if __name__ == "__main__":
    install()
