from pathlib import Path
import shutil, time

ROOT = Path(r"C:\Users\Thinkpad\Desktop\KonstanceAI")
BOT = ROOT / "bot.py"
BACKUP = ROOT / "backups" / f"bot_pre_j_tiny_{int(time.time())}.py"

src = BOT.read_text(encoding="utf-8")
shutil.copyfile(BOT, BACKUP)

old = '''async def do_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
'''

new = '''async def do_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    # convenience parsing for create_script/run_script when user omits '|'
    if action in ["create_script", "run_script", "create_agent", "run_agent"] and "|" not in payload:
        parts = payload.split()
        if len(parts) >= 2:
            first = parts[0]
            rest = " ".join(parts[1:]).strip()
            payload = f"{first}|{rest}"

    code, msg = do_action(action, payload)
    await update.message.reply_text(msg)
'''

if old in src:
    src = src.replace(old, new)
else:
    # fallback: inject just before call
    needle = '    code, msg = do_action(action, payload)'
    inject = '''    # convenience parsing for create_script/run_script when user omits '|'
    if action in ["create_script", "run_script", "create_agent", "run_agent"] and "|" not in payload:
        parts = payload.split()
        if len(parts) >= 2:
            first = parts[0]
            rest = " ".join(parts[1:]).strip()
            payload = f"{first}|{rest}"
'''
    if needle in src and inject not in src:
        src = src.replace(needle, inject + needle)

BOT.write_text(src, encoding="utf-8")
print(f"Patched tiny /do parser. Backup: {BACKUP}")
