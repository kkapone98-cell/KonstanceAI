# KonstanceAI Launcher & Setup

Fully local system: Telegram bot, OpenClaw relay (optional), Ollama fallback, verbose logging, crash recovery.

---

## Step-by-step setup

### 1. Install requirements

From the project folder (e.g. `C:\Users\Thinkpad\Desktop\KonstanceAI`):

```bat
pip install -r requirements.txt
```

Includes: `python-dotenv`, `python-telegram-bot`, `requests`.

### 2. Environment and tokens

Use **either** `.env` **or** token files (or both; env overrides files).

**Option A – .env (recommended)**  
Create or edit `.env` in the project root:

```env
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
OPENCLAW_RELAY_URL=ws://127.0.0.1:18789
OPENCLAW_RELAY_TOKEN=your-relay-token-if-required
HUGGINGFACE_TOKEN=optional-hf-token
OPENCLAW_CMD=optional-command-to-start-openclaw
OPENCLAW_CWD=optional-cwd-for-openclaw
```

**Option B – Token files**  
- **telegram_token.txt** — one line: your Telegram bot token (`123456:ABC-DEF...`).
- **huggingface_token.txt** — optional; one line: HuggingFace token.

The bot logs whether each token was loaded from `env` or `file:...`.

### 3. Ollama (local fallback)

- Install and run [Ollama](https://ollama.com).
- Ensure the fallback model from `data/llm.json` is pulled, e.g.:

  ```bat
  ollama run qwen2.5:3b
  ```

- The launcher verifies Ollama is ready before starting the bot (up to 30 s). If Ollama is not ready, the bot still starts but may only echo when the OpenClaw relay is down.

### 4. Run the system

```bat
python launcher.py
```

**What the launcher does:**

1. Creates `logs/` and `data/` if missing; logs to **console** and **logs/launcher.log**.
2. Checks `.env` and token files; warns in logs if Telegram token is missing.
3. **OpenClaw**: If `OPENCLAW_CMD` is set and the relay is not already up, starts OpenClaw. If the relay is already running, skips starting it. Waits up to 90 s for the relay when it was just started (else 25 s).
4. **Ollama**: Verifies the fallback model (from `data/llm.json`) responds; logs success or warning.
5. Starts **bot.py** as a subprocess (Windows: `CREATE_NO_WINDOW` for a clean launch).
6. Monitors bot (and OpenClaw if the launcher started it); **auto-restarts** on crash.

To run only the bot (no launcher):

```bat
python bot.py
```

---

## Tokens and env

| Purpose        | .env variable         | Token file              |
|----------------|-----------------------|-------------------------|
| Telegram       | `TELEGRAM_BOT_TOKEN`  | `telegram_token.txt`    |
| HuggingFace    | `HUGGINGFACE_TOKEN` or `HF_TOKEN` | `huggingface_token.txt` |
| OpenClaw relay | `OPENCLAW_RELAY_URL`, `OPENCLAW_RELAY_TOKEN` | — |
| Start OpenClaw | `OPENCLAW_CMD`, `OPENCLAW_CWD`    | — |

`OPENCLAW_RELAY_URL` can be `http://...` or `ws://...`; `ws://` is converted to `http://` for API calls.

---

## OpenClaw and Kimmi-style flows

- **Relay available**: Bot uses OpenClaw for replies; file editing (improve, approve, rollback) works when the relay supports it.
- **Relay down**: Bot uses **Ollama fallback** from `data/llm.json`; replies stay local. File-editing flows depend on the relay.

---

## Logs

- **Launcher**: `logs/launcher.log` (DEBUG) + console (INFO).
- **Bot**: `logs/bot.log` (DEBUG) + console (INFO).

Startup logs include: token source (env vs file), OpenClaw relay status, Ollama fallback status, LLM config.

---

## Confirmation

- **Fully local**: Bot and Ollama run locally; only Telegram and optional HuggingFace use the internet.
- **Auto-verify**: Launcher checks OpenClaw relay and Ollama fallback before starting the bot.
- **Crash recovery**: Launcher restarts `bot.py` (and OpenClaw if it started it) when they exit.
- **Paths**: Launcher and bot use the project root; `logs/`, `data/`, `backups/` are created as needed.
