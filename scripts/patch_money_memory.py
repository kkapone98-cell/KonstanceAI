from pathlib import Path
import shutil, time

ROOT = Path(r"C:\Users\Thinkpad\Desktop\KonstanceAI")
BOT = ROOT / "bot.py"
BACKUP = ROOT / "backups" / f"bot_pre_money_{int(time.time())}.py"

src = BOT.read_text(encoding="utf-8")
shutil.copyfile(BOT, BACKUP)

if "from scripts.money_memory_bridge import money_menu, best_next_play, add_play, log_outcome" not in src:
    anchor = "from scripts.self_audit_bridge import run_self_audit\n"
    if anchor in src:
        src = src.replace(anchor, anchor + "from scripts.money_memory_bridge import money_menu, best_next_play, add_play, log_outcome\n")
    else:
        src = "from scripts.money_memory_bridge import money_menu, best_next_play, add_play, log_outcome\n" + src

handlers = '''

async def money_menu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not owner_required(update, "approve_latest"):
        await update.message.reply_text("Not authorized for this action.")
        return
    code, msg = money_menu()
    await safe_reply(update, msg)


async def best_play_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not owner_required(update, "approve_latest"):
        await update.message.reply_text("Not authorized for this action.")
        return
    code, msg = best_next_play()
    await safe_reply(update, msg)


async def add_play_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not owner_required(update, "approve_latest"):
        await update.message.reply_text("Not authorized for this action.")
        return
    args = context.args or []
    if len(args) < 3:
        await update.message.reply_text("Usage: /add_play <name> <lane> <roi> [effort] [notes]")
        return
    name = args[0]
    lane = args[1]
    roi = args[2]
    effort = args[3] if len(args) > 3 else "medium"
    notes = " ".join(args[4:]).strip() if len(args) > 4 else ""
    code, msg = add_play(name, lane, roi, effort, notes)
    await safe_reply(update, msg)
'''

if "async def money_menu_cmd(update: Update" not in src:
    anchor = "async def self_audit_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):"
    if anchor in src:
        src = src.replace(anchor, handlers + "\n" + anchor)
    else:
        src += handlers

if 'CommandHandler("money_menu",money_menu_cmd)' not in src:
    reg_anchor = 'app.add_handler(CommandHandler("self_audit",self_audit_cmd))'
    if reg_anchor in src:
        src = src.replace(reg_anchor, reg_anchor + '\n    app.add_handler(CommandHandler("money_menu",money_menu_cmd))\n    app.add_handler(CommandHandler("best_play",best_play_cmd))\n    app.add_handler(CommandHandler("add_play",add_play_cmd))')

if 'if n in ["money menu", "money options", "ways to make money"]:' not in src:
    nl_anchor = '    # smart routed chat\n'
    nl_block = '''    if n in ["money menu", "money options", "ways to make money"]:
        code, msg = money_menu()
        await safe_reply(update, msg)
        return

    if n in ["best next play", "what should we run next", "best play"]:
        code, msg = best_next_play()
        await safe_reply(update, msg)
        return

'''
    if nl_anchor in src:
        src = src.replace(nl_anchor, nl_block + nl_anchor)

BOT.write_text(src, encoding="utf-8")
print(f"Money memory patch applied. Backup: {BACKUP}")
