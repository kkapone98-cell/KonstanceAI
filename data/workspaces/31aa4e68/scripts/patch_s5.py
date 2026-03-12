from pathlib import Path
import shutil, time

ROOT = Path(r"C:\Users\Thinkpad\Desktop\KonstanceAI")
BOT = ROOT / "bot.py"
BACKUP = ROOT / "backups" / f"bot_pre_s5_{int(time.time())}.py"

src = BOT.read_text(encoding="utf-8")
shutil.copyfile(BOT, BACKUP)

if "import subprocess" not in src:
    src = src.replace("import os, json, time, pathlib, shutil", "import os, json, time, pathlib, shutil, subprocess")

helpers = '''

def run_script_file(path, args=None):
    args = args or []
    p = subprocess.run(["python", str(path)] + args, capture_output=True, text=True)
    out = (p.stdout or "").strip()
    err = (p.stderr or "").strip()
    return p.returncode, (out if out else err if err else "(no output)")


def run_workflow_critic():
    return run_script_file(ROOT / "scripts" / "workflow_critic.py", [])


def run_improve_proposer(goal_text):
    return run_script_file(ROOT / "scripts" / "improve_proposer.py", [goal_text])


def run_improve_apply():
    return run_script_file(ROOT / "scripts" / "improve_apply.py", [])
'''

if "def run_workflow_critic()" not in src:
    anchor = "def run_autoplan_goal(goal_text: str):"
    idx = src.find(anchor)
    if idx != -1:
        src = src[:idx] + helpers + "\n" + src[idx:]

handlers = '''

async def critic_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not owner_required(update, "approve_latest"):
        await update.message.reply_text("Not authorized for this action.")
        return
    code, msg = run_workflow_critic()
    await safe_reply(update, msg)


async def propose_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not owner_required(update, "approve_latest"):
        await update.message.reply_text("Not authorized for this action.")
        return
    goal = " ".join(context.args).strip() if context.args else "improve workflows"
    code, msg = run_improve_proposer(goal)
    await safe_reply(update, msg)


async def apply_improve_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not owner_required(update, "approve_latest"):
        await update.message.reply_text("Not authorized for this action.")
        return
    code, msg = run_improve_apply()
    await safe_reply(update, msg)
'''

if "async def critic_cmd(update: Update" not in src:
    anchor = "async def goal_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):"
    if anchor in src:
        src = src.replace(anchor, handlers + "\n" + anchor)

if 'CommandHandler("critic",critic_cmd)' not in src:
    reg_anchor = 'app.add_handler(CommandHandler("goal",goal_cmd))'
    if reg_anchor in src:
        src = src.replace(reg_anchor, reg_anchor + '\n    app.add_handler(CommandHandler("critic",critic_cmd))\n    app.add_handler(CommandHandler("propose",propose_cmd))\n    app.add_handler(CommandHandler("apply_improve",apply_improve_cmd))')

# natural language hooks
if 'if n.startswith("analyze workflows"):' not in src:
    nl_anchor = '    # smart routed chat\n'
    nl_block = '''    if n.startswith("analyze workflows"):
        code, msg = run_workflow_critic()
        await safe_reply(update, msg)
        return

    if n.startswith("propose improvements"):
        g = text[len("propose improvements"):].strip() or "improve workflows"
        code, msg = run_improve_proposer(g)
        await safe_reply(update, msg)
        return

'''
    if nl_anchor in src:
        src = src.replace(nl_anchor, nl_block + nl_anchor)

BOT.write_text(src, encoding="utf-8")
print(f"S5 patch applied. Backup: {BACKUP}")
