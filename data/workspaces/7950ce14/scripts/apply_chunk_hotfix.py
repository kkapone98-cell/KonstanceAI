from pathlib import Path
import re, shutil, time

ROOT = Path(r"C:\Users\Thinkpad\Desktop\KonstanceAI")
BOT = ROOT / "bot.py"
BACKUP = ROOT / "backups" / f"bot_pre_chunkfix2_{int(time.time())}.py"

src = BOT.read_text(encoding="utf-8", errors="ignore")
shutil.copyfile(BOT, BACKUP)

helper = '''

def _chunk_text(text: str, limit: int = 3000):
    t = text or ""
    if len(t) <= limit:
        return [t]
    out = []
    while t:
        if len(t) <= limit:
            out.append(t)
            break
        cut = t.rfind("\\n", 0, limit)
        if cut <= 0:
            cut = limit
        out.append(t[:cut])
        t = t[cut:].lstrip("\\n")
    return out


async def safe_reply(update: Update, text: str):
    MAX_TOTAL = 12000
    t = (text or "")[:MAX_TOTAL]
    parts = _chunk_text(t, 3000)
    if len(parts) == 1:
        await update.message.reply_text(parts[0])
        return
    for i, part in enumerate(parts, 1):
        await update.message.reply_text(f"[{i}/{len(parts)}]\\n{part}")
'''

# remove existing helper block if present
src = re.sub(r'\n\ndef _chunk_text\(text: str, limit: int = \d+\):.*?\n\nasync def safe_reply\(update: Update, text: str\):.*?(?=\n\ndef |\nasync def |\Z)', '\n', src, flags=re.S)

anchor = "def style(text, prefs):"
idx = src.find(anchor)
if idx != -1:
    src = src[:idx] + helper + "\n" + src[idx:]
else:
    src += helper

# upgrade heavy direct replies if present
src = src.replace('await update.message.reply_text(msg)', 'await safe_reply(update, msg)')
src = src.replace('await update.message.reply_text(msg if msg else "No scripts yet.")', 'await safe_reply(update, msg if msg else "No scripts yet.")')
src = src.replace('await update.message.reply_text(msg if msg else "No agents yet.")', 'await safe_reply(update, msg if msg else "No agents yet.")')

BOT.write_text(src, encoding="utf-8")
print(f"patched; backup={BACKUP}")
