# KonstanceAI Audit & Fix Report

## Summary
I audited the cloned repo and found the bot was non-functional because `bot.py` imported many missing modules (`scripts/...`) and used hardcoded Windows-only root paths (`C:\Users\Thinkpad\Desktop\KonstanceAI`). That caused immediate startup failure, so launcher loops looked like the bot was "sleeping forever".

I replaced the broken runtime with a tested, cross-platform baseline that:
- Starts Telegram polling correctly with `python-telegram-bot`
- Uses SmartReplyEngine (OpenClaw relay first, Ollama fallback second)
- Uses project-relative paths (no hardcoded machine paths)
- Enforces single-instance lock to prevent duplicate pollers
- Restarts safely through launcher with backoff

---

## Priority Findings

| Priority | Finding | Impact | Fix |
|---|---|---|---|
| **Critical** | `bot.py` imports missing modules (`scripts.modules.*`, `scripts.*`) | Bot crashes before polling starts | Replaced with complete runnable `bot.py` and implemented `scripts/modules/smart_reply_engine.py` |
| **Critical** | Hardcoded `C:\Users\Thinkpad\Desktop\KonstanceAI` in `bot.py` and `launcher.py` | Fails on any other machine/path | Replaced with `Path(__file__).resolve().parent` + optional `KONSTANCE_ROOT` |
| **Critical** | Polling conflicts possible from multiple instances | Telegram `getUpdates` collision / unstable runtime | Added lock-file based single-instance guard with exit code `11` handling |
| High | No real tests for runtime modules | Regressions likely | Added minimal unit tests for token loading + SmartReplyEngine routing |
| Low | Legacy `main.py` points to missing package paths | Confusion / dead entrypoint | Kept as legacy; production path now `python launcher.py` |

---

## Full Fix Code (files changed)

- `bot.py` (fully replaced)
- `launcher.py` (fully replaced)
- `scripts/modules/smart_reply_engine.py` (new complete implementation)
- `scripts/__init__.py` (new)
- `scripts/modules/__init__.py` (new)
- `tests/test_smart_reply_engine.py` (new)
- `tests/test_bot_config.py` (new)

---

## Root Cause: Why Telegram polling never actually started

1. `bot.py` tried to import:
   - `scripts.modules.chat_improve_bridge`
   - `scripts.agent_bridge`, `scripts.script_bridge`, etc.
   - `scripts.modules.smart_reply_engine`
2. Those files/directories were not present in repo.
3. Python crashed on import before app construction and `app.run_polling()`.
4. `launcher.py` monitored/restarted process, so externally it looked like a sleeping/restarting bot rather than a responding poller.

---

## Local Implementation Guide (Xavier)

1. Clone and checkout fixed branch:
   - `git clone https://github.com/kkapone98-cell/konsanse`
   - `cd konsanse`
   - `git checkout ai-fixes-backup`

2. Install dependencies:
   - `pip install -r requirements.txt`

3. Set Telegram token (either method):
   - `.env`:
     - `TELEGRAM_BOT_TOKEN=123456:ABC...`
   - or file:
     - create `telegram_token.txt` with one token line

4. Optional OpenClaw relay settings in `.env`:
   - `OPENCLAW_RELAY_URL=ws://127.0.0.1:18789`
   - `OPENCLAW_RELAY_TOKEN=...` (if required)

5. Run:
   - `python launcher.py`

6. In Telegram:
   - send `/start`
   - send `/status`
   - send normal message text

Expected: bot responds and continues responding to messages.

---

## Testing Checklist

- [x] Syntax checks:
  - `python -m py_compile bot.py launcher.py scripts/modules/smart_reply_engine.py`
- [x] Unit tests pass:
  - `python -m unittest discover -s tests -v`
- [ ] Manual Telegram smoke test with real token:
  - `/start` returns online
  - `/status` returns runtime state
  - normal text returns SmartReplyEngine response
- [ ] Optional OpenClaw cloud test:
  - `/cloudtest` reports OK when relay is reachable

---

## Xavier Local AI Model Setup (recommended)

### Ollama fallback (required for local resilience)
1. Install Ollama
2. Pull model:
   - `ollama pull qwen2.5:3b`
3. Optional model config file:
   - `data/llm.json`
   - Example:
     ```json
     {
       "fallback": "qwen2.5:3b"
     }
     ```

### OpenClaw relay (optional but preferred)
- If relay is up, SmartReplyEngine uses relay first.
- If relay is down, engine falls back automatically to Ollama.

---

## Verification Output (executed during audit)

- `python3 -m unittest discover -s tests -v` → **OK (5 tests passed)**

---

## Notes

This fix intentionally prioritizes stable production polling and response behavior first. It removes broken scaffold imports that were never present in repository and restores a clean runtime path that Xavier can actually run immediately.
