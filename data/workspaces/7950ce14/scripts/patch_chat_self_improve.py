from pathlib import Path
import shutil, time

ROOT = Path(r"C:\Users\Thinkpad\Desktop\KonstanceAI")
BOT = ROOT / "bot.py"
BACKUP = ROOT / "backups" / f"bot_pre_chat_improve_{int(time.time())}.py"

src = BOT.read_text(encoding="utf-8", errors="ignore")
shutil.copyfile(BOT, BACKUP)

# import hook
imp = "from scripts.modules.chat_improve_bridge import enqueue_improve_request\n"
if imp not in src:
    anchor = "from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters\n"
    if anchor in src:
        src = src.replace(anchor, anchor + imp)
    else:
        src = imp + src

# command handler
handler_block = '''

async def improve_now_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not owner_required(update, "approve_latest"):
        await update.message.reply_text("Not authorized for this action.")
        return
    req = " ".join(context.args).strip() if context.args else ""
    if not req:
        await update.message.reply_text("Usage: /improve_now <improvement request>")
        return
    row = enqueue_improve_request(req, requested_by=str(update.effective_user.id))
    await update.message.reply_text(f"Queued self-improve job: {row['id']}")
'''

if "async def improve_now_cmd(update: Update" not in src:
    anchor = "async def improve(update: Update, context: ContextTypes.DEFAULT_TYPE):"
    if anchor in src:
        src = src.replace(anchor, handler_block + "\n" + anchor)

# register command
if 'CommandHandler("improve_now",improve_now_cmd)' not in src:
    reg_anchor = 'app.add_handler(CommandHandler("improve",improve))'
    if reg_anchor in src:
        src = src.replace(reg_anchor, reg_anchor + '\n    app.add_handler(CommandHandler("improve_now",improve_now_cmd))')

# natural-language hook in handle_message
nl_block = '''    if n.startswith("improve yourself") or n.startswith("self-improve"):
        row = enqueue_improve_request(text, requested_by=str(update.effective_user.id))
        await update.message.reply_text(f"Queued self-improve job: {row['id']}")
        return

'''
if "n.startswith(\"improve yourself\")" not in src:
    nl_anchor = "    # smart routed chat\n"
    if nl_anchor in src:
        src = src.replace(nl_anchor, nl_block + nl_anchor)

BOT.write_text(src, encoding="utf-8")
print(f"patched bot.py; backup={BACKUP}")
