from pathlib import Path
import shutil, time

ROOT = Path(r"C:\Users\Thinkpad\Desktop\KonstanceAI")
BOT = ROOT / "bot.py"
BACKUP = ROOT / "backups" / f"bot_pre_smart_reply_{int(time.time())}.py"
MARK = "# SMART_REPLY_OVERRIDE_V1"

src = BOT.read_text(encoding="utf-8", errors="ignore")
shutil.copyfile(BOT, BACKUP)

if MARK not in src:
    block = '''

# SMART_REPLY_OVERRIDE_V1
from scripts.modules.smart_reply_engine import smart_reply, style_text

def style(text, prefs):
    return style_text(text, prefs)

def llm_reply(user_text, prefs, profile, force_cloud=False):
    return smart_reply(user_text, prefs, profile)
'''
    src += block
    BOT.write_text(src, encoding="utf-8")
    print(f"patched bot.py; backup={BACKUP}")
else:
    print("smart override already present")
