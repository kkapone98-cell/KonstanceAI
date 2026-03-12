import subprocess
def check_ollama():
    try:
        subprocess.run(['ollama','status'],check=True)
        subprocess.run(['ollama','pull','mistral'],check=True)
        subprocess.run(['ollama','pull','codellama'],check=True)
        print('[Ollama Manager] Ollama and models ready')
    except Exception as e:
        print(f'[Ollama Manager] Error: {e}')
