import pathlib, shutil, time

ROOT = pathlib.Path(r"C:\Users\Thinkpad\Desktop\KonstanceAI")
BOT = ROOT / "bot.py"
BACKUP = ROOT / "backups" / f"bot_pre_h5_{int(time.time())}.py"

src = BOT.read_text(encoding="utf-8")
shutil.copyfile(BOT, BACKUP)

if "from scripts.agent_bridge import create_agent, list_agents, run_agent" not in src:
    # add import after telegram imports
    marker = "from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters\n"
    if marker in src:
        src = src.replace(marker, marker + "from scripts.agent_bridge import create_agent, list_agents, run_agent\n")
    else:
        # fallback prepend
        src = "from scripts.agent_bridge import create_agent, list_agents, run_agent\n" + src

handlers_block = '''

async def agents(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code, msg = list_agents()
    await update.message.reply_text(msg if msg else "No agents yet.")


async def create_agent_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not owner_required(update, "approve_latest"):
        await update.message.reply_text("Not authorized for this action.")
        return
    args = context.args or []
    if len(args) < 2:
        await update.message.reply_text("Usage: /create_agent <name> <purpose>")
        return
    name = args[0]
    purpose = " ".join(args[1:]).strip()
    code, msg = create_agent(name, purpose)
    await update.message.reply_text(msg)


async def run_agent_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not owner_required(update, "approve_latest"):
        await update.message.reply_text("Not authorized for this action.")
        return
    args = context.args or []
    if len(args) < 2:
        await update.message.reply_text("Usage: /run_agent <name> <task>")
        return
    name = args[0]
    task = " ".join(args[1:]).strip()
    code, msg = run_agent(name, task)
    await update.message.reply_text(msg)
'''

if "async def agents(update: Update" not in src:
    anchor = "async def addtask(update: Update, context: ContextTypes.DEFAULT_TYPE):"
    if anchor in src:
        src = src.replace(anchor, handlers_block + "\n" + anchor)
    else:
        src += handlers_block

# register command handlers in main()
reg_anchor = 'app.add_handler(CommandHandler("addtask",addtask))'
if reg_anchor in src and 'CommandHandler("agents",agents)' not in src:
    src = src.replace(reg_anchor, reg_anchor + '\n    app.add_handler(CommandHandler("agents",agents))\n    app.add_handler(CommandHandler("create_agent",create_agent_cmd))\n    app.add_handler(CommandHandler("run_agent",run_agent_cmd))')

# natural language intents in handle_message
if 'if n.startswith("create agent "):' not in src:
    nl_anchor = '    # natural tasks\n'
    nl_block = '''    if n.startswith("create agent "):
        # format: create agent <name> | <purpose>
        raw = text[len("create agent "):].strip()
        if "|" not in raw:
            await update.message.reply_text("Format: create agent <name> | <purpose>")
            return
        name, purpose = [x.strip() for x in raw.split("|", 1)]
        code, msg = create_agent(name, purpose)
        await update.message.reply_text(msg)
        return

    if n.startswith("run agent "):
        # format: run agent <name> | <task>
        raw = text[len("run agent "):].strip()
        if "|" not in raw:
            await update.message.reply_text("Format: run agent <name> | <task>")
            return
        name, task = [x.strip() for x in raw.split("|", 1)]
        code, msg = run_agent(name, task)
        await update.message.reply_text(msg)
        return

    if n in ["agents", "list agents", "show agents"]:
        code, msg = list_agents()
        await update.message.reply_text(msg if msg else "No agents yet.")
        return

'''
    if nl_anchor in src:
        src = src.replace(nl_anchor, nl_block + nl_anchor)

BOT.write_text(src, encoding="utf-8")
print(f"Patched bot.py. Backup: {BACKUP}")
