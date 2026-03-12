from pathlib import Path
import shutil, time
p = Path(r"C:\Users\Thinkpad\Desktop\KonstanceAI\bot.py")
src = p.read_text(encoding="utf-8", errors="ignore")
bk = p.parent / "backups" / f"bot_pre_kimi_bridge_{int(time.time())}.py"
shutil.copyfile(p, bk)
mark = "# SMART_REPLY_OVERRIDE_V2"
if mark not in src:
src += f"""

{mark}
from scripts.modules.smart_reply_engine import smart_reply, style_text
def style(text, prefs): return style_text(text, prefs)
def llm_reply(user_text, prefs, profile, force_cloud=False): return smart_reply(user_text, prefs, profile)
"""
p.write_text(src, encoding="utf-8")
print("patched", bk)
