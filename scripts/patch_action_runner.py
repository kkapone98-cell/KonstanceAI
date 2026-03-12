import pathlib, shutil, time

ROOT = pathlib.Path(r"C:\Users\Thinkpad\Desktop\KonstanceAI")
BOT = ROOT / "bot.py"
BACKUP = ROOT / "backups" / f"bot_pre_j_{int(time.time())}.py"

src = BOT.read_text(encoding="utf-8")
shutil.copyfile(BOT, BACKUP)

if "from scripts.action_bridge import do_action, list_jobs, approve_job" not in src:
    imp_anchor = "from scripts.script_bridge import create_script, list_scripts, run_script\n"
    if imp_anchor in src:
        src = src.replace(imp_anchor, imp_anchor + "from scripts.action_bridge import do_action, list_jobs, approve_job\n")
    else:
        src = "from scripts.action_bridge import do_action, list_jobs, approve_job\n" + src

handlers = '''

async def do_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # /do <action> <payload>
    if not owner_required(update, "approve_latest"):
        await update.message.reply_text("Not authorized for this action.")
        return
    args = context.args or []
    if len(args) < 2:
        await update.message.reply_text("Usage: /do <action> <payload>")
        return
    action = args[0]
    payload = " ".join(args[1:]).strip()
    code, msg = do_action(action, payload)
    await update.message.reply_text(msg)


async def jobs_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not owner_required(update, "approve_latest"):
        await update.message.reply_text("Not authorized for this action.")
        return
    code, msg = list_jobs()
    await update.message.reply_text(msg)


async def approve_job_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not owner_required(update, "approve_latest"):
        await update.message.reply_text("Not authorized for this action.")
        return
    args = context.args or []
    if len(args) < 1:
        await update.message.reply_text("Usage: /approve_job <job_id>")
        return
    code, msg = approve_job(args[0])
    await update.message.reply_text(msg)
'''

if "async def do_cmd(update: Update" not in src:
    anchor = "async def scripts_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):"
    if anchor in src:
        src = src.replace(anchor, handlers + "\n" + anchor)
    else:
        src += handlers

if 'CommandHandler("do",do_cmd)' not in src:
    reg_anchor = 'app.add_handler(CommandHandler("run_script",run_script_cmd))'
    if reg_anchor in src:
        src = src.replace(reg_anchor, reg_anchor + '\n    app.add_handler(CommandHandler("do",do_cmd))\n    app.add_handler(CommandHandler("jobs",jobs_cmd))\n    app.add_handler(CommandHandler("approve_job",approve_job_cmd))')

# Natural language action lane
if 'if n.startswith("do action "):' not in src:
    nl_anchor = '    # smart routed chat\n'
    nl_block = '''    if n.startswith("do action "):
        # format: do action <action> | <payload>
        raw = text[len("do action "):].strip()
        if "|" not in raw:
            await update.message.reply_text("Format: do action <action> | <payload>")
            return
        action, payload = [x.strip() for x in raw.split("|", 1)]
        code, msg = do_action(action, payload)
        await update.message.reply_text(msg)
        return

    if n in ["jobs", "show jobs", "list jobs"]:
        code, msg = list_jobs()
        await update.message.reply_text(msg)
        return

'''
    if nl_anchor in src:
        src = src.replace(nl_anchor, nl_block + nl_anchor)

BOT.write_text(src, encoding="utf-8")
print(f"Patched bot.py. Backup: {BACKUP}")
