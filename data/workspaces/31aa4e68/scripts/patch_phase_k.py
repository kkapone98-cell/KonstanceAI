from pathlib import Path
import shutil, time

ROOT = Path(r"C:\Users\Thinkpad\Desktop\KonstanceAI")
BOT = ROOT / "bot.py"
BACKUP = ROOT / "backups" / f"bot_pre_k_{int(time.time())}.py"

src = BOT.read_text(encoding="utf-8")
shutil.copyfile(BOT, BACKUP)

if "import subprocess" not in src:
    src = src.replace("import os, json, time, pathlib, shutil", "import os, json, time, pathlib, shutil, subprocess")

if 'AUTOPLAN = DATA / "autoplan.json"' not in src:
    anchor = 'MISSION = DATA / "mission.json"'
    if anchor in src:
        src = src.replace(anchor, anchor + '\nAUTOPLAN = DATA / "autoplan.json"')
    else:
        src = src.replace('ROUTER = DATA / "router.json"', 'ROUTER = DATA / "router.json"\nAUTOPLAN = DATA / "autoplan.json"')

if 'def run_autoplan_goal(' not in src:
    helper = '''

def run_autoplan_goal(goal_text: str):
    engine = ROOT / "scripts" / "autoplan_engine.py"
    p = subprocess.run(["python", str(engine), "goal", goal_text], capture_output=True, text=True)
    out = (p.stdout or "").strip()
    err = (p.stderr or "").strip()
    return p.returncode, (out if out else err if err else "(no output)")
'''
    insert_anchor = 'def llm_reply(user_text,prefs,profile,force_cloud=False):'
    idx = src.find(insert_anchor)
    if idx != -1:
        src = src[:idx] + helper + '\n' + src[idx:]
    else:
        src += helper

handlers = '''

async def autoplan_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cfg = loadj(AUTOPLAN, {"enabled": True, "cloud_escalation": True, "max_tasks_per_goal": 5})
    await update.message.reply_text(json.dumps(cfg, indent=2))


async def goal_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not owner_required(update, "approve_latest"):
        await update.message.reply_text("Not authorized for this action.")
        return
    goal = " ".join(context.args).strip() if context.args else ""
    if not goal:
        await update.message.reply_text("Usage: /goal <objective>")
        return
    code, msg = run_autoplan_goal(goal)
    await update.message.reply_text(msg)
'''

if 'async def goal_cmd(update: Update' not in src:
    anchor = 'async def do_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):'
    if anchor in src:
        src = src.replace(anchor, handlers + '\n' + anchor)
    else:
        src += handlers

if 'CommandHandler("goal",goal_cmd)' not in src:
    reg_anchor = 'app.add_handler(CommandHandler("do",do_cmd))'
    if reg_anchor in src:
        src = src.replace(reg_anchor, reg_anchor + '\n    app.add_handler(CommandHandler("goal",goal_cmd))\n    app.add_handler(CommandHandler("autoplan",autoplan_cmd))')

if 'if n.startswith("goal "):' not in src:
    nl_anchor = '    # natural tasks\n'
    nl_block = '''    if n.startswith("goal "):
        if not owner_required(update, "approve_latest"):
            await update.message.reply_text("Not authorized for this action.")
            return
        g = text[len("goal "):].strip()
        code, msg = run_autoplan_goal(g)
        await update.message.reply_text(msg)
        return

'''
    if nl_anchor in src:
        src = src.replace(nl_anchor, nl_block + nl_anchor)

BOT.write_text(src, encoding="utf-8")
print(f"Patched bot.py. Backup: {BACKUP}")
