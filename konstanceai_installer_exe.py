import os
import sys
import subprocess
from datetime import datetime
import telegram
import logging
import time

PROJECT_DIR = os.path.abspath(".")  # Ensure all files are written here

ENV_PATH = os.path.join(PROJECT_DIR, ".env")  # Writable location
TELEGRAM_TOKEN_PATH = os.path.join(PROJECT_DIR, "telegram_token.txt")  # Writable location

LOG_FILE = os.path.join(PROJECT_DIR, "installer_log.txt")
logging.basicConfig(filename=LOG_FILE, level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)
logging.getLogger().addHandler(console_handler)
logging.info("=== Starting KonstanceAI EXE ===")

# Load GitHub credentials
with open(ENV_PATH) as f:
    lines = f.readlines()
    env = dict(line.strip().split('=', 1) for line in lines if '=' in line)
GITHUB_USER = env.get("GITHUB_USER")
GITHUB_TOKEN = env.get("GITHUB_TOKEN")

# Update .gitignore
gitignore_path = os.path.join(PROJECT_DIR, ".gitignore")
entries = ["__pycache__/", "*.pyc", "logs/", "backups/", ".env", "*.log"]
if not os.path.exists(gitignore_path):
    with open(gitignore_path, "w", encoding="utf-8") as f:
        f.write("\\n".join(entries) + "\\n")
else:
    with open(gitignore_path, "a+", encoding="utf-8") as f:
        content = f.read()
        for e in entries:
            if e not in content:
                f.write(f"{e}\\n")
logging.info(".gitignore updated.")

# Clear Telegram updates
try:
    bot_token = open(TELEGRAM_TOKEN_PATH).read().strip()
    bot = telegram.Bot(token=bot_token)
    updates = bot.get_updates(timeout=1)
    for update in updates:
        if update.message:
            bot.delete_message(chat_id=update.message.chat.id, message_id=update.message.message_id)
    logging.info("Pending Telegram updates cleared.")
except Exception as e:
    logging.warning(f"Telegram issue: {e}")

# Fix Python files
EXCLUDE_DIRS = ["backups", "logs", "__pycache__"]
python_files = []
for root, dirs, files in os.walk(PROJECT_DIR):
    if any(ex in root for ex in EXCLUDE_DIRS):
        continue
    for f in files:
        if f.endswith(".py"):
            python_files.append(os.path.join(root, f))
for file_path in python_files:
    with open(file_path, "r+", encoding="utf-8") as f:
        content = f.read()
        content = content.replace("asyncio.get_event_loop()", "asyncio.new_event_loop()")
        f.seek(0)
        f.write(content)
        f.truncate()
logging.info(f"{len(python_files)} Python files fixed.")

# Stop existing Python bots
try:
    subprocess.run(["taskkill", "/f", "/im", "python.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    logging.info("Existing Python processes stopped.")
except Exception as e:
    logging.warning(f"Error stopping Python processes: {e}")
time.sleep(2)

# Launch KonstanceAI
main_py = os.path.join(PROJECT_DIR, "main.py")
if os.path.exists(main_py):
    subprocess.Popen([sys.executable, main_py])
    logging.info("KonstanceAI started.")
else:
    logging.error("main.py not found!")

# Git commit & push
try:
    os.chdir(PROJECT_DIR)
    subprocess.run(["git", "add", "."], check=True)
    commit_msg = f"Auto-fixed files - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    subprocess.run(["git", "commit", "-m", commit_msg], check=True)
    subprocess.run(["git", "pull", "--rebase"], check=True)
    subprocess.run(["git", "push", f"https://{GITHUB_USER}:{GITHUB_TOKEN}@github.com/kkapone98-cell/KonstanceAI.git"], check=True)
    logging.info("Git push completed successfully.")
except subprocess.CalledProcessError as e:
    logging.warning(f"Git operation issue: {e}")

logging.info("=== KonstanceAI EXE Complete ===")
