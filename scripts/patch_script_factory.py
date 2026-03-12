import pathlib, shutil, time

ROOT = pathlib.Path(r"C:\Users\Thinkpad\Desktop\KonstanceAI")
BOT = ROOT / "bot.py"
BACKUP = ROOT / "backups" / f"bot_pre_i_{int(time.time())}.py"

src = BOT.read_text(encoding="utf-8")
shutil.copyfile(BOT, BACKUP)

if "from scripts.script_bridge import create_script, list_scripts, run_script" not in src:
    marker = "from scripts.agent_bridge import create_agent, list_agents, run_agent\n"
    if marker in src:
        src = src.replace(marker, marker + "from scripts.script_bridge import create_script, list_scripts, run_script\n")
    else:
        src = "from scripts.script_bridge import create_script, list_scripts, run_script\n" + src

handlers = '''

async def scripts_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code, msg = list_scripts()
    await update.message.reply_text(msg if msg else "No scripts yet.")


async def create_script_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not owner_required(update, "approve_latest"):
        await update.message.reply_text("Not authorized for this action.")
        return
    args = context.args or []
    if len(args) < 2:
        await update.message.reply_text("Usage: /create_script <name> <purpose>")
        return
    name = args[0]
    purpose = " ".join(args[1:]).strip()
    code, msg = create_script(name, purpose)
    await update.message.reply_text(msg)


async def run_script_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not owner_required(update, "approve_latest"):
        await update.message.reply_text("Not authorized for this action.")
        return
    args = context.args or []
    if len(args) < 1:
        await update.message.reply_text("Usage: /run_script <name> [input]")
        return
    name = args[0]
    input_text = " ".join(args[1:]).strip() if len(args) > 1 else ""
    code, msg = run_script(name, input_text)
    await update.message.reply_text(msg)
'''

if "async def scripts_cmd(update: Update" not in src:
    anchor = "async def agents(update: Update, context: ContextTypes.DEFAULT_TYPE):"
    if anchor in src:
        src = src.replace(anchor, handlers + "\n" + anchor)
    else:
        src += handlers

if 'CommandHandler("scripts",scripts_cmd)' not in src:
    reg_anchor = 'app.add_handler(CommandHandler("run_agent",run_agent_cmd))'
    if reg_anchor in src:
        src = src.replace(reg_anchor, reg_anchor + '\n    app.add_handler(CommandHandler("scripts",scripts_cmd))\n    app.add_handler(CommandHandler("create_script",create_script_cmd))\n    app.add_handler(CommandHandler("run_script",run_script_cmd))')

# natural language hooks
if 'if n.startswith("create script "):' not in src:
    nl_anchor = '    # smart routed chat\n'
    nl_block = '''    if n.startswith("create script "):
        # format: create script <name> | <purpose>
        raw = text[len("create script "):].strip()
        if "|" not in raw:
            await update.message.reply_text("Format: create script <name> | <purpose>")
            return
        name, purpose = [x.strip() for x in raw.split("|", 1)]
        code, msg = create_script(name, purpose)
        await update.message.reply_text(msg)
        return

    if n.startswith("run script "):
        # format: run script <name> | <input>
        raw = text[len("run script "):].strip()
        if "|" not in raw:
            await update.message.reply_text("Format: run script <name> | <input>")
            return
        name, inp = [x.strip() for x in raw.split("|", 1)]
        code, msg = run_script(name, inp)
        await update.message.reply_text(msg)
        return

    if n in ["scripts", "list scripts", "show scripts"]:
        code, msg = list_scripts()
        await update.message.reply_text(msg if msg else "No scripts yet.")
        return

'''
    if nl_anchor in src:
        src = src.replace(nl_anchor, nl_block + nl_anchor)

BOT.write_text(src, encoding="utf-8")
print(f"Patched bot.py. Backup: {BACKUP}")
