from pathlib import Path
import shutil, time

ROOT = Path(r"C:\Users\Thinkpad\Desktop\KonstanceAI")
BOT = ROOT / "bot.py"
BACKUP = ROOT / "backups" / f"bot_pre_mission_{int(time.time())}.py"

src = BOT.read_text(encoding="utf-8")
shutil.copyfile(BOT, BACKUP)

# ensure constant path exists
if 'MISSION = DATA / "mission.json"' not in src:
    anchor = 'ROUTER = DATA / "router.json"'
    if anchor in src:
        src = src.replace(anchor, anchor + '\nMISSION = DATA / "mission.json"')

# helper function
helper = '''

def mission_text():
    m = loadj(MISSION, {})
    if not m:
        return "Mission file not found."
    lines = []
    lines.append(f"Identity: {m.get('identity','Konstance')}")
    lines.append(f"Role: {m.get('role','assistant')}")
    lines.append(f"Owner: {m.get('owner','')}")
    lines.append(f"Primary Goal: {m.get('primary_goal','')}")
    if m.get('pillars'):
        lines.append("Pillars:")
        lines.extend([f"- {x}" for x in m.get('pillars', [])])
    return "\\n".join(lines)
'''

if 'def mission_text()' not in src:
    insert_after = 'def style(text, prefs):'
    idx = src.find(insert_after)
    if idx != -1:
        # place helper before style function
        src = src[:idx] + helper + '\n' + src[idx:]
    else:
        src += helper

# handlers
handlers = '''

async def purpose(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(mission_text())


async def northstar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    m = loadj(MISSION, {})
    goal = m.get("primary_goal", "No goal set.")
    await update.message.reply_text(f"Northstar: {goal}")
'''

if 'async def purpose(update: Update' not in src:
    anchor = 'async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):'
    idx = src.find(anchor)
    if idx != -1:
        src = src[:idx] + handlers + '\n' + src[idx:]
    else:
        src += handlers

# register commands
if 'CommandHandler("purpose",purpose)' not in src:
    reg_anchor = 'app.add_handler(CommandHandler("status",status))'
    if reg_anchor in src:
        src = src.replace(reg_anchor, reg_anchor + '\n    app.add_handler(CommandHandler("purpose",purpose))\n    app.add_handler(CommandHandler("northstar",northstar))')

# natural-language trigger in handle_message
nl = '''
    if n in ["what is your purpose", "your purpose", "northstar", "what is your goal"]:
        await update.message.reply_text(mission_text())
        return
'''
if 'what is your purpose' not in src:
    anchor = '    # smart routed chat\n'
    if anchor in src:
        src = src.replace(anchor, nl + anchor)

BOT.write_text(src, encoding="utf-8")
print(f"Mission patch applied. Backup: {BACKUP}")
