from pathlib import Path
import shutil, time

ROOT = Path(r"C:\Users\Thinkpad\Desktop\KonstanceAI")
BOT = ROOT / "bot.py"
BACKUP = ROOT / "backups" / f"bot_pre_mission_steer_{int(time.time())}.py"

src = BOT.read_text(encoding="utf-8")
shutil.copyfile(BOT, BACKUP)

# Ensure MISSION constant exists
if 'MISSION = DATA / "mission.json"' not in src:
    anchor = 'ROUTER = DATA / "router.json"'
    if anchor in src:
        src = src.replace(anchor, anchor + '\nMISSION = DATA / "mission.json"')

# Replace build_system_prompt with mission-aware version
start = src.find('def build_system_prompt(')
if start != -1:
    end = src.find('\n\ndef ', start + 1)
    if end == -1:
        end = len(src)
    new_func = '''def build_system_prompt(prefs, profile):
    m = loadj(MISSION, {})
    tone = prefs.get("tone", "friendly")
    verbosity = prefs.get("verbosity", "medium")
    user_name = profile.get("name") or "friend"

    role = m.get("role", "personal assistant")
    goal = m.get("primary_goal", "Help the owner make practical progress.")
    pillars = m.get("pillars", [])
    constraints = m.get("constraints", [])

    pillar_text = " | ".join(pillars[:4]) if pillars else ""
    constraint_text = " | ".join(constraints[:3]) if constraints else ""

    return (
        "You are Konstance, a Telegram personal assistant. "
        f"UserName={user_name}. Tone={tone}. Verbosity={verbosity}. "
        f"Role={role}. PrimaryGoal={goal}. "
        f"OperationalPillars={pillar_text}. Constraints={constraint_text}. "
        "Prioritize actionable steps, opportunity finding, execution planning, and clear next actions. "
        "When uncertain, ask one concise clarifying question."
    )
'''
    src = src[:start] + new_func + src[end:]

BOT.write_text(src, encoding="utf-8")
print(f"Mission steering patch applied. Backup: {BACKUP}")
