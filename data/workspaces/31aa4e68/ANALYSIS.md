# KonstanceAI — Full Analysis

**Date:** 2026-03-12  
**Owner:** Xavier  
**Project root:** `C:\Users\Thinkpad\Desktop\KonstanceAI`

---

## 1. ANALYZE — Data flow and module roles

### End-to-end flow (intended vs actual)

**Intended:** Telegram message → `on_text` → `smart_reply` (with self-model) → reply sent → `parse_code_request` → if code intent → `handle_code_request` (generate → compile → apply/stage) → optional `/approve` → `apply_patch` → `refresh` self-model.

**Actual:**

- **`bot.py`**  
  - Acquires single-instance lock, sets up logging, loads token/prefs/profile.  
  - Registers only: `/start`, `/status`, `/health`, `/cloudtest`, `/setverbosity`, and one `MessageHandler` for non-command text.  
  - **`on_text`** only: loads prefs/profile, calls `smart_reply(text, prefs, profile, history)`, appends to memory, replies with `reply[:3900]`.  
  - **No call to `parse_code_request` or `handle_code_request`** — the autonomous code path is never used.  
  - Defines `cmd_drafts`, `cmd_approve`, `cmd_reject`, `cmd_rollback_file`, `cmd_goals`, and overwrites `cmd_status` in the autonomous patch block, but **none of the new commands are registered in `main()`** (only the original five are). So `/drafts`, `/approve`, `/reject`, `/rollback`, `/goals` do nothing; unregistered commands may fall through to `on_text` as plain text.  
  - **`OWNER_ID` is used in every autonomous `cmd_*` but never defined** in `bot.py` (only `_owner_only(update)` uses `os.getenv("OWNER_ID")`). So any invocation of those handlers would raise `NameError` if they were ever registered.

- **`launcher.py`**  
  - Runs `bot.py` in a loop, handles exit code 11 (duplicate instance), backoff on crash. No HIGH_RISK logic here.

- **`scripts/modules/smart_reply_engine.py`**  
  - 3-tier: OpenClaw relay → Ollama local → echo.  
  - Exposes: `relay_available`, `ollama_fallback_available`, `openclaw_generate`, `smart_reply`.  
  - **Does not expose `_try_ollama` or `_try_openclaw`** (and they don’t exist).  
  - **Does not inject the self-model** into the prompt; ref.txt describes a patch that was never applied here.

- **`scripts/modules/intent_router.py`**  
  - Keyword pre-filter, fast-paths for rollback/drafts/goals/status, then LLM classification.  
  - **`_call_llm` imports `_try_ollama` and `_try_openclaw` from `smart_reply_engine`** — those symbols don’t exist → **ImportError** when any message hits the LLM classification path.

- **`scripts/modules/code_editor.py`**  
  - `risk_level`, `backup_file`, `list_backups`, `compile_check`, `compile_check_string`, `apply_patch`, `rollback`.  
  - HIGH_RISK = `bot.py`, `launcher.py`, `main.py`. Pre-compile on string, backup, write, post-compile, rollback on failure. Fits guardrails.

- **`scripts/modules/self_model.py`**  
  - Reads `data/mission.json` and `data/goals.json`, scans `.py` files, builds self-model block, caches in `data/self_map.json` (5 min TTL), `refresh()` on edit.  
  - **Mission shape:** expects `name`, `mission`, `origin`, `personality`, `financial_context`, `self_improvement_policy`.  
  - **`data/mission.json`** has: `identity`, `role`, `owner`, `primary_goal`, `pillars`, `constraints`, `success_metrics` — **no `mission`, `origin`, `personality`, `financial_context`, `self_improvement_policy`**. So the self-model block has empty lines for those and uses `m.get('name','Konstance')` (missing → "Konstance") and no mission sentence.

- **`scripts/modules/goal_engine.py`**  
  - Loads/saves `data/goals.json`, `capability_log.json`; `mark_achieved`, `add_goal`, `on_capability_added`, `goals_summary`, `_suggest_next_goal` (LLM).  
  - **`_suggest_next_goal` imports `_try_ollama`, `_try_openclaw` from `smart_reply_engine`** → same **ImportError** when a self-edit completes and next-goal suggestion runs.

- **`scripts/modules/autonomous_loop.py`**  
  - Draft CRUD, `generate_code`, `build_status_report`, `handle_code_request`.  
  - **`generate_code` and `build_status_report` import `_try_openclaw` / `_try_ollama`** → **ImportError** when generating code or building status.

- **`main.py`**  
  - Legacy guard: prints error and exits 1. Correct.

**Summary:** The pipeline from “Xavier’s message” to “code change on disk” is **disconnected**: no handler registration for self-edit commands, no `OWNER_ID`, no call from `on_text` to intent + `handle_code_request`, and no chat-style LLM helpers in `smart_reply_engine`, so intent/codegen/goal-suggestion would crash even if wired.

---

## 2. ASSESS MISSION ALIGNMENT — `data/mission.json` vs codebase

| Goal / pillar | In mission | Supported by code? | What’s missing |
|---------------|------------|--------------------|----------------|
| **Primary goal** | “Help Xavier become wealthy by finding, validating, and executing high-ROI opportunities.” | **No.** No opportunity discovery, validation, or execution flows. | Opportunity engine, validation logic, execution hooks. |
| **Opportunity Engine** | “Discover money plays (flips, FBA, services, content).” | **No.** No scrapers, feeds, or discovery modules. | Discovery module, data sources, triggers. |
| **Execution Engine** | “Build scripts/agents to run those plays.” | **Partially.** Self-edit can add modules; no orchestration to “run” plays (e.g. run a script, report outcome). | Task runner, outcome reporting, agent orchestration. |
| **Content Engine** | “Generate short-form content workflows.” | **No.** No content generation or workflow automation. | Content module, workflow definitions. |
| **Tracking Engine** | “Track actions, outcomes, and revenue impact.” | **Partially.** `capability_log.json` logs self-edits; no revenue/action/outcome schema. | Metrics schema, revenue/action tracking, dashboards. |
| **Constraints** | Safety, draft→test→approve, stable core, modular. | **Yes** in design (code_editor, HIGH_RISK approval). Not exercised because the loop isn’t wired. | Wiring the loop so these run. |
| **Success metrics** | Opportunities/week, automations deployed, revenue/profit impact, time saved. | **No.** No counting of opportunities, no revenue/profit fields, no time-saved tracking. | Logging and aggregation for these. |

**Verdict:** The codebase is built for **self-edit and self-awareness**, not yet for the four pillars (opportunity, execution, content, tracking). To support the written mission, the first step is to **make the existing autonomous loop actually run**; then add the missing engines and metrics.

---

## 3. FIND GAPS — Capabilities needed for the mission

- **Autonomous loop wiring (critical)**  
  - Register `/drafts`, `/approve`, `/reject`, `/rollback`, `/goals` and ensure only owner can run them (`OWNER_ID`).  
  - From `on_text`, after sending the conversational reply, call `parse_code_request` and, if `is_code_request`, `handle_code_request`.  
  - **Why:** Without this, no self-edit from natural language and no use of goals/drafts.

- **Chat-style LLM helpers in `smart_reply_engine`**  
  - Implement `_try_openclaw(messages, system_override=None)` and `_try_ollama(messages, system_override=None)` returning a single string.  
  - **Why:** `intent_router`, `goal_engine`, and `autonomous_loop` depend on them; otherwise ImportError/runtime errors.

- **Self-model in every LLM prompt**  
  - Pass self-model block into `smart_reply` (or into the generate functions) so OpenClaw and Ollama always see mission, goals, codebase, commands.  
  - **Why:** So Konstance can “know itself” and align replies and code actions with mission.

- **Mission.json ↔ self_model shape**  
  - Either extend `mission.json` with `mission`, `origin`, `personality`, `financial_context`, `self_improvement_policy`, or have `self_model` derive them from `primary_goal`, `role`, `pillars`, `constraints` (e.g. mission = primary_goal, personality = role).  
  - **Why:** So the self-model block is meaningful and stable.

- **Opportunity Engine (new module)**  
  - e.g. `scripts/modules/opportunity_engine.py`: discover and store “plays” (flips, FBA, etc.), expose to LLM or commands.  
  - **Why:** Directly supports “find high-ROI opportunities.”

- **Tracking Engine (extend)**  
  - Schema for actions, outcomes, revenue impact; persist and aggregate.  
  - **Why:** Required for “revenue/profit impact” and “time saved.”

- **Scheduled / autonomous tasks**  
  - Run tasks on a schedule without Xavier messaging (e.g. cron-like or loop).  
  - **Why:** Matches goal “Konstance acts on a schedule.”

---

## 4. FIND RISKS — What could break or slip through

- **Silent / confusing failures**  
  - **`OWNER_ID` undefined:** Any future registration of the autonomous commands would raise `NameError` on first use.  
  - **Unregistered commands:** `/approve`, `/drafts`, etc. never run; user might think the bot is broken or ignore drafts.  
  - **Intent/codegen never run:** Code path that does compile + backup + apply is never reached from chat, so no silent bad self-edit from this path; but the **design** appears to work while it doesn’t.

- **Bad self-edit slipping through**  
  - **Compile-only check:** No tests or lint; logic bugs or runtime errors (e.g. wrong imports) can land on disk.  
  - **Path resolution:** If a draft stored a relative path and `cmd_approve` ran from a different cwd, `apply_patch` could write to the wrong place. Mitigation: store and resolve paths relative to `ROOT` or always store absolute.  
  - **HIGH_RISK bypass:** If something ever called `apply_patch` on `bot.py` without going through the draft flow, guardrail would be bypassed. Currently only `handle_code_request` and `cmd_approve` call `apply_patch`; both respect risk.

- **Edge cases**  
  - **Empty or malformed LLM response:** Intent router and code gen could get empty or non-JSON; fallbacks exist but could still produce weak or wrong targets.  
  - **Concurrent edits:** Single instance prevents two pollers; two quick approves could still race on the same file (no file lock in `apply_patch`).  
  - **pending_edits.json shape:** Autonomous code uses `drafts: { id: {...} }`. If the file was ever written by another schema (e.g. “pending”/“approved” arrays), draft load/save could overwrite or misread.  
  - **self_map.json write:** `build_self_context` writes the cache file; if the process dies mid-write, cache could be corrupted (acceptable; next run rebuilds).

- **Mission/config**  
  - **mission.json:** Missing keys produce empty self-model lines; no crash but weaker context.  
  - **goals.json:** If structure changes and code still expects `active`/`achieved` and `goal`/`status`, could KeyError; worth a defensive load with defaults.

---

## 5. PRIORITIZE — Next 5 things to build

| # | What | Why (goal/mission) | Where it lives | Risk |
|---|------|---------------------|----------------|------|
| **1** | **Wire the autonomous loop** — OWNER_ID, register `/drafts`/`/approve`/`/reject`/`/rollback`/`/goals`, call `parse_code_request` + `handle_code_request` from `on_text`, add `_try_ollama`/`_try_openclaw` and inject self-model into prompts. | Makes self-edit and self-awareness actually run; foundation for “improves its own capabilities” and for all other goals. | `bot.py`, `scripts/modules/smart_reply_engine.py` | Low (logic in modules; bot.py stays thin). |
| **2** | **Align mission.json with self_model** — Derive or add `mission`, `personality`, `financial_context`, etc., so the self-model block is complete. | So “mission, goals, constraints” in the prompt are accurate and actionable. | `data/mission.json`, `scripts/modules/self_model.py` | Low. |
| **3** | **Financial / tracking schema** — Actions, outcomes, revenue impact, time saved; persist and expose to Konstance. | Supports “revenue/profit impact” and “time saved” in success_metrics. | `data/` (e.g. `tracking.json`), `scripts/modules/tracking_engine.py` | Low. |
| **4** | **Scheduled task system** — Konstance runs tasks on a schedule (e.g. daily scan, alerts) without user message. | Matches goal “Konstance acts on a schedule.” | `scripts/modules/scheduler.py`, small hook in `launcher` or `bot` startup | Medium (long-running, resource use). |
| **5** | **Opportunity Engine (MVP)** — One source (e.g. RSS or API), parse “plays,” store and surface to LLM/commands. | Directly supports “discover money plays.” | `scripts/modules/opportunity_engine.py` | Medium (external deps, rate limits). |

---

## 6. PROPOSE — #1 priority implementation

The **#1 priority** is implemented in code as follows:

1. **`bot.py`**  
   - Define `OWNER_ID` from env (int) once at module load.  
   - In `main()`, register handlers for `drafts`, `approve`, `reject`, `rollback`, `goals` (and keep existing `status`).  
   - In `on_text`, after sending the normal reply, call a new module function that parses intent and, if code request, runs `handle_code_request` (owner-only).

2. **`scripts/modules/smart_reply_engine.py`**  
   - Add `_try_openclaw(messages, system_override=None)` and `_try_ollama(messages, system_override=None)` (signatures used by intent_router, goal_engine, autonomous_loop).  
   - Add optional `self_context` to `smart_reply` and prepend it to the user prompt so every LLM call sees the self-model.

3. **Orchestration from `on_text`**  
   - Implement `scripts/modules/autonomous_loop.py`: `maybe_handle_code_after_reply(update, context, text, owner_id)` that calls `parse_code_request(text)`, and if `is_code_request` and user is owner, calls `handle_code_request(...)`.  
   - `bot.py` calls this after sending the conversational reply.

All changes keep guardrails: no second instance, no new HIGH_RISK logic in bot core, backup/compile in `code_editor` unchanged, OWNER_ID gating on all privileged commands.

**Implementation (done in this session):**

- **bot.py:** `load_dotenv` and `OWNER_ID` at top; imports for `build_self_context` and `maybe_handle_code_after_reply`; `on_text` gets self-context, passes it to `smart_reply`, then calls `maybe_handle_code_after_reply(update, context, text, OWNER_ID)`; `main()` registers `CommandHandler` for `drafts`, `approve`, `reject`, `rollback`, `goals`.
- **scripts/modules/smart_reply_engine.py:** `_build_prompt_from_messages`, `_try_openclaw`, `_try_ollama` (chat-style, used by intent_router, goal_engine, autonomous_loop); `smart_reply(..., self_context=None)` prepends self-model to the user prompt.
- **scripts/modules/autonomous_loop.py:** `parse_code_request` import; `maybe_handle_code_after_reply(update, context, text, owner_id)` so `on_text` can trigger the code-request flow after the reply (owner-only).
