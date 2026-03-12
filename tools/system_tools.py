import subprocess
def run_command(cmd):
    try:
        result=subprocess.run(cmd,shell=True,capture_output=True,text=True)
        print(f'[System Tools] Output: {result.stdout}')
    except Exception as e:
        print(f'[System Tools] Error: {e}')
