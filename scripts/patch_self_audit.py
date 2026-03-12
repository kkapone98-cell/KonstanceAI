from pathlib import Path
import shutil, time

ROOT = Path(r"C:\Users\Thinkpad\Desktop\KonstanceAI")
BOT = ROOT / "bot.py"
BACKUP = ROOT / "backups" / f"bot_pre_self_audit_{int(time.time())}.py"

src = BOT.read_text(encoding="utf-8")
shutil.copyfile(BOT, BACKUP)

if "from scripts.self_audit_bridge import run_self_audit" not in src:
    anchor = "from scripts.action_bridge import do_action, list_jobs, approve_job\n"
    if anchor in src:
        src = src.replace(anchor, anchor + "from scripts.self_audit_bridge import run_self_audit\n")
    else:
        src = "from scripts.self_audit_bridge import run_self_audit\n" + src

handlers = '''

async def self_audit_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not owner_required(update, "approve_latest"):
        await update.message.reply_text("Not authorized for this action.")
        return
    code, msg = run_self_audit()
    await update.message.reply_text(msg[:3800])
'''

if 'async def self_audit_cmd(update: Update' not in src:
    anchor = 'async def jobs_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):'
    if anchor in src:
        src = src.replace(anchor, handlers + '\n' + anchor)
    else:
        src += handlers

if 'CommandHandler("self_audit",self_audit_cmd)' not in src:
    reg_anchor = 'app.add_handler(CommandHandler("jobs",jobs_cmd))'
    if reg_anchor in src:
        src = src.replace(reg_anchor, reg_anchor + '\n    app.add_handler(CommandHandler("self_audit",self_audit_cmd))')

if 'if n in ["self audit", "audit yourself", "what can you do now"]:' not in src:
    nl_anchor = '    # smart routed chat\n'
    nl_block = '''    if n in ["self audit", "audit yourself", "what can you do now"]:
        code, msg = run_self_audit()
        await update.message.reply_text(msg[:3800])
        return

'''
    if nl_anchor in src:
        src = src.replace(nl_anchor, nl_block + nl_anchor)

BOT.write_text(src, encoding="utf-8")
print(f"Self-audit patch applied. Backup: {BACKUP}")
