import subprocess, json, pathlib
MEM_CONV = pathlib.Path(r'C:\Users\Thinkpad\Desktop\KonstanceAI\memory\conversations.json')
def run_task(task):
    try:
        if MEM_CONV.exists():
            data = json.load(open(MEM_CONV,'r',encoding='utf-8'))
        else:
            data = []
        context = ' '.join([m.get('user','')+m.get('ai','') for m in data[-50:]])
        user_input = task.get('details','')
        full_input = context + '\nUser: ' + user_input
        c = subprocess.run(['ollama','generate','mistral',full_input], capture_output=True, text=True)
        return c.stdout.strip()
    except Exception as e:
        return f'[Error]: {e}'
