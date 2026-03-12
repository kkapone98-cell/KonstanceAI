# LEGACY_GUARD_ADDED
import sys
print('ERROR: main.py is legacy. Run: python launcher.py')
sys.exit(1)

import subprocess
import sys
import time
from tools.ollama_manager import check,pull
from interface.telegram_bot import run

def install():

    packages=["python-telegram-bot","requests","psutil"]

    for p in packages:

        subprocess.call([sys.executable,"-m","pip","install",p])

def start():

    install()

    if not check():

        print("Install Ollama from https://ollama.com")

        return

    pull()

    while True:

        try:

            run()

        except Exception as e:

            print("Bot crashed restarting",e)

            time.sleep(5)

if __name__=="__main__":

    start()
