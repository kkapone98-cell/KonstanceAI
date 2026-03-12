import json,time,subprocess,pathlib
ROOT=pathlib.Path(r"C:\Users\Thinkpad\Desktop\KonstanceAI")
STATE=ROOT/"data"/"watchdog.json"
BOT=ROOT/"bot.py"
raw=STATE.read_text(encoding="utf-8-sig") if STATE.exists() else '{"checks":0,"last_ok":null,"restarts":0}'
s=json.loads(raw)
s["checks"]=int(s.get("checks",0))+1
out=subprocess.check_output(["tasklist","/FI","IMAGENAME eq python.exe"],text=True,errors="ignore")
running=("python.exe" in out.lower())
if running: s["last_ok"]=int(time.time()); print("watchdog: python running")
if (not running): print("watchdog: python not running, starting bot..."); subprocess.Popen(["python",str(BOT)],cwd=str(ROOT)); s["restarts"]=int(s.get("restarts",0))+1
STATE.write_text(json.dumps(s,indent=2),encoding="utf-8")
