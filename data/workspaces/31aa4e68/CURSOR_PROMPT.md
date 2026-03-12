# KonstanceAI — Guaranteed Working Bot + Cursor Handoff

**Copy everything below the line into Cursor Composer.** One prompt to get a working self-editing Telegram bot and a Cursor handoff workflow.

---

## QUICK START (paste this if you want the ultra-short version)

```
KonstanceAI: Telegram bot that edits its own code. Project: [path]. 
1) Verify .env has TELEGRAM_BOT_TOKEN and OWNER_ID. 2) Run python launcher.py. 
3) Test: message "add a /ping command" in Telegram. 4) Add code_model to data/llm.json for better code gen (ollama pull codellama:7b). 
5) After each self-edit, Konstance should output a "paste into Cursor" block. Fix any broken imports or missing handlers. Guarantee it works.
```

---

## FULL PROMPT

---

## CONTEXT

**KonstanceAI** = Xavier's Jarvis. Telegram bot on Windows 11, Python 3.13. Mission: help Xavier become wealthy via opportunity discovery, execution, content, tracking. Konstance edits its own code from natural conversation.

**Project root:** `C:\Users\Thinkpad\Desktop\KonstanceAI` (or current workspace)

**Already implemented (verify these exist):**
- `bot.py`: OWNER_ID from .env, handlers for /drafts /approve /reject /rollback /goals, on_text → smart_reply + maybe_handle_code_after_reply
- `smart_reply_engine.py`: _try_ollama, _try_openclaw (chat-style), smart_reply(..., self_context=)
- `autonomous_loop.py`: maybe_handle_code_after_reply, handle_code_request, generate_code
- `code_editor.py`: backup + compile + apply + rollback. HIGH_RISK = bot.py, launcher.py → /approve
- `intent_router.py`: parse_code_request (keyword + LLM)
- `self_model.py`: build_self_context from mission.json, goals.json, codebase scan

**Guardrails:**
- Single instance lock (bot.lock)
- Timestamped .bak before every write
- py_compile before + after apply
- OWNER_ID gate on all privileged commands
- New code in scripts/modules/ only

---

## YOUR TASK — DO IN ORDER

### 1. GUARANTEE WORKING BOT (do this first)

1. **Check .env:**
   - `TELEGRAM_BOT_TOKEN` (from @BotFather)
   - `OWNER_ID=8158300788` (Xavier's Telegram user ID from @userinfobot)
   - `OPENCLAW_RELAY_URL=ws://127.0.0.1:18789` (optional; if missing, Ollama fallback)

2. **Run:** `python launcher.py` or `python bot.py`.

3. **Test in Telegram (as Xavier):**
   - `/start` → "KonstanceAI online"
   - `what are your goals?` → goals list
   - `add a /ping command that replies pong` → should detect code intent, generate code, stage draft (HIGH_RISK) or apply (LOW_RISK)
   - `/drafts` → list pending drafts
   - `/approve <id>` → apply draft
   - `/rollback bot.py` → restore from .bak

4. **If any step fails:** Fix it. Common causes: missing OWNER_ID, Ollama not running, import errors.

### 2. BETTER CODE GENERATION (free, local)

Konstance uses Ollama for code gen. `qwen2.5:3b` is small.

**Add a code model for code generation only:**
- In `data/llm.json` add: `"code_model": "codellama:7b"` or `"deepseek-coder:6.7b"` (or `qwen2.5-coder` if available).
- In `autonomous_loop.generate_code` and `smart_reply_engine`:
  - Read `code_model` from llm.json; if set, use it for code generation instead of the default fallback.
- Run: `ollama pull codellama:7b` (or chosen model).

**If no code model:** Keep qwen2.5:3b. It works; just slower/less accurate for code.

### 3. CURSOR HANDOFF — Konstance → scripts for Cursor to improve

**Goal:** Xavier can talk to Konstance in Telegram → Konstance makes code → Konstance outputs a block Xavier pastes into Cursor for further improvement.

**Implementation:**
- In `autonomous_loop.handle_code_request`, after a successful apply (LOW or HIGH), add:
  - If the change was significant (new file or >50 lines), append to the reply:
    ```
    📋 CURSOR PROMPT — paste this into Cursor for review:
    ---
    Context: Konstance AI self-edit. File: {path}. Change: {description}
    Request: Review and improve this code. Consider: error handling, edge cases, alignment with mission.
    ---
    ```
- Add a `/cursor` command (owner-only): when Xavier sends `/cursor`, Konstance replies with the last applied change + a ready-to-paste Cursor prompt block (from capability_log or recent draft).
- Optionally: add `scripts/modules/cursor_handoff.py` with `format_cursor_prompt(description, target, diff_or_summary)` that builds a consistent prompt block.

**Minimal version:** Just add to the "Applied" reply: "Paste this into Cursor for review: [file path and brief description]." No new command needed.

### 4. MISSION ALIGNMENT — self_model + mission.json

`data/mission.json` has: identity, role, owner, primary_goal, pillars, constraints, success_metrics.  
`self_model` expects: name, mission, origin, personality, financial_context, self_improvement_policy.

**Fix:** In `self_model.build_self_context`, derive:
- `mission` = primary_goal
- `name` = identity
- `personality` = role
- `financial_context` = pillars[0] or primary_goal
- `self_improvement_policy` = constraints joined

So the self-model block is never empty.

---

## CONSTRAINTS

- Do not change LLM provider or Telegram library
- Keep 3-tier LLM fallback (OpenClaw → Ollama → echo)
- All new modules in scripts/modules/
- Windows, Python 3.13, no Unix-only libs
- Every file write = backup first
- Every code change = compile-check before apply

---

## OUTPUT

When done:
1. Confirm the bot starts and responds to test messages.
2. List any changes made (files and brief summary).
3. Give Xavier a one-line "how to run" and a one-line "how to test self-edit in Telegram."
