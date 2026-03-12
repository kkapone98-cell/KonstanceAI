from pathlib import Path
from tools.openclaw_manager import edit_file_openclaw
import json, time
SCRIPTS_DIR = Path(r'C:\Users\Thinkpad\Desktop\KonstanceAI\scripts')
KNOW_FILE = Path(r'C:\Users\Thinkpad\Desktop\KonstanceAI\memory\knowledge.json')
def run_task(task):
    tp = task.get('task_type')
    det = task.get('details')
    if tp == 'coding':
        fn = SCRIPTS_DIR / f'{int(time.time())}_script.py'
        edit_file_openclaw(fn, f'# Auto by Konstance\n# {det}\n')
        return f'Coding task saved: {fn}'
    elif tp == 'research':
        data = []
        if KNOW_FILE.exists():
            data = json.load(open(KNOW_FILE,'r',encoding='utf-8'))
        data.append({'task': det})
        json.dump(data, open(KNOW_FILE,'w',encoding='utf-8'), indent=2)
        return 'Research saved.'
    elif tp == 'automation':
        return 'Automation simulated.'
    return 'No task done.'
