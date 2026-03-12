"""
scripts/modules/autonomous_loop.py
Konstance full autonomous orchestration loop.
Handles code requests end-to-end: classify → generate → verify → apply/stage → report → improve.
"""
import json, re, time, logging, uuid
from pathlib import Path

from scripts.modules.intent_router import parse_code_request

logger       = logging.getLogger(__name__)
ROOT         = Path(__file__).parent.parent.parent
PENDING_PATH = ROOT / "data" / "pending_edits.json"


# ── Draft store ───────────────────────────────────────────────────────────────

def _load_drafts() -> dict:
    try:
        if PENDING_PATH.exists():
            return json.loads(PENDING_PATH.read_text(encoding="utf-8"))
    except Exception: pass
    return {"drafts": {}}

def _save_drafts(d: dict):
    PENDING_PATH.parent.mkdir(parents=True, exist_ok=True)
    PENDING_PATH.write_text(json.dumps(d, indent=2), encoding="utf-8")

def store_draft(user_id, target, content, description, bak_path="") -> str:
    d = _load_drafts()
    did = str(uuid.uuid4())[:8]
    d["drafts"][did] = {
        "user_id": user_id, "target": str(target), "new_content": content,
        "description": description, "created_at": int(time.time()), "backup_path": bak_path
    }
    _save_drafts(d)
    return did

def get_draft(did: str) -> dict | None:
    return _load_drafts()["drafts"].get(did)

def delete_draft(did: str):
    d = _load_drafts()
    if did in d["drafts"]:
        del d["drafts"][did]; _save_drafts(d)

def list_drafts() -> dict:
    return _load_drafts().get("drafts", {})


def get_pending_drafts_for_user(user_id) -> list:
    drafts = _load_drafts().get("drafts", {})
    uid = str(user_id) if user_id is not None else ""
    return [(did, d) for did, d in drafts.items() if str(d.get("user_id", "")) == uid]


_APPROVAL_PHRASES = frozenset({"yes", "yep", "yeah", "ok", "okay", "sure", "go ahead", "do it", "apply", "approve", "approved", "apply it", "go for it", "sounds good"})


def _is_natural_approval(text: str) -> bool:
    t = text.lower().strip()
    return t in _APPROVAL_PHRASES or bool(re.match(r"^(yes|ok|approve|apply)\s*[!.]?$", t))


def _extract_draft_id_from_message(text: str) -> str | None:
    m = re.search(r"\b(?:approve|apply)\s+([a-f0-9]{8})\b", text.lower())
    return m.group(1) if m else None


async def _apply_draft_and_reply(update, context, did: str, draft: dict, send):
    from scripts.modules.code_editor import apply_patch
    from scripts.modules.self_model import refresh as refresh_self
    from scripts.modules.goal_engine import on_capability_added
    await send(f"Applying `{did}`...", parse_mode="Markdown")
    r = apply_patch(Path(draft["target"]), draft["new_content"])
    if r["success"]:
        delete_draft(did)
        bak = Path(r["backup_path"]).name if r.get("backup_path") else "none"
        await send(f"Applied! Backup: `{bak}`. Test it now.", parse_mode="Markdown")
        refresh_self()
        next_goal = on_capability_added(draft.get("description", ""), draft.get("target", ""))
        if next_goal:
            await send(f"Next goal: _{next_goal}_", parse_mode="Markdown")
    else:
        await send(f"Failed: {r.get('error', 'unknown')}", parse_mode="Markdown")


async def handle_natural_approval(update, context, text: str, owner_id: int) -> bool:
    user_id = getattr(update.effective_user, "id", None)
    if user_id != owner_id:
        return False
    pending = get_pending_drafts_for_user(user_id)
    if not pending:
        return False
    send = update.message.reply_text
    did = _extract_draft_id_from_message(text)
    if did and did in [d[0] for d in pending]:
        draft = get_draft(did)
        if draft:
            await _apply_draft_and_reply(update, context, did, draft, send)
            return True
    if len(pending) == 1 and _is_natural_approval(text):
        did, draft = pending[0]
        await _apply_draft_and_reply(update, context, did, draft, send)
        return True
    if len(pending) > 1 and _is_natural_approval(text):
        lines = ["You have multiple drafts. Say _approve abc12345_ for the one to apply:\n"]
        for did, d in pending:
            lines.append(f"`{did}` — _{d.get('description', '')[:50]}..._")
        await send("\n".join(lines), parse_mode="Markdown")
        return True
    return False


# ── Code generation ───────────────────────────────────────────────────────────

async def generate_code(description: str, target_path: Path) -> str:
    """
    Uses the best available LLM to generate new/modified file content.
    Tries OpenClaw first (better quality), falls back to Ollama.
    Returns raw Python code string.
    """
    current = ""
    if target_path.exists():
        try: current = target_path.read_text(encoding="utf-8")
        except Exception: pass

    prompt = (
        f"You are editing KonstanceAI Python source code for Xavier's autonomous Telegram bot.\n"
        f"Task: {description}\n"
        f"Target file: {target_path}\n\n"
        f"Rules:\n"
        f"- Output ONLY the complete updated Python file content\n"
        f"- No markdown, no fences, no explanation\n"
        f"- Preserve all existing functionality unless the task says otherwise\n"
        f"- Use async/await correctly for Telegram handlers\n"
        f"- Add a clear comment marking what was changed\n"
    )
    if current:
        prompt += f"\nCURRENT FILE CONTENT:\n{current}"

    msgs = [{"role": "user", "content": prompt}]

    # Try OpenClaw first for code quality
    for fn_name in ["_try_openclaw", "_try_ollama"]:
        try:
            if fn_name == "_try_openclaw":
                from scripts.modules.smart_reply_engine import _try_openclaw
                result = _try_openclaw(messages=msgs)
            else:
                from scripts.modules.smart_reply_engine import _try_ollama
                result = _try_ollama(messages=msgs)
            if result and len(result.strip()) > 50:
                # Strip markdown fences if model ignored instructions
                result = re.sub(r"^```(?:python)?\s*", "", result.strip())
                result = re.sub(r"\s*```$", "", result)
                return result
        except Exception as e:
            logger.warning(f"{fn_name} codegen failed: {e}")

    return ""


# ── Status report ─────────────────────────────────────────────────────────────

def build_status_report() -> str:
    lines = ["⚡ *Konstance Status*\n"]
    # Uptime proxy: launcher log or just report running
    lines.append("🟢 Bot: running")
    # LLM health
    try:
        from scripts.modules.smart_reply_engine import _try_openclaw
        r = _try_openclaw(messages=[{"role":"user","content":"ping"}])
        lines.append(f"🟢 OpenClaw: {'ok' if r else 'no response'}")
    except Exception:
        lines.append("🔴 OpenClaw: unreachable")
    # Pending drafts
    drafts = list_drafts()
    lines.append(f"📋 Pending drafts: {len(drafts)}")
    # Capability log
    cap_log = ROOT / "data" / "capability_log.json"
    if cap_log.exists():
        try:
            data = json.loads(cap_log.read_text(encoding="utf-8"))
            lines.append(f"🔧 Total improvements: {data.get('total_improvements', 0)}")
            if data.get("last_improvement"):
                lines.append(f"📅 Last improvement: {data['last_improvement']}")
        except Exception: pass
    return "\n".join(lines)


# ── Main orchestration ────────────────────────────────────────────────────────

async def handle_code_request(update, context, intent: dict, owner_id: int):
    """
    Full autonomous handling of a detected code request.
    Called from on_text() after normal LLM reply is sent.
    """
    from scripts.modules.code_editor import (
        apply_patch, rollback as do_rollback,
        list_backups, backup_file, compile_check_string, risk_level
    )
    from scripts.modules.goal_engine import on_capability_added, goals_summary
    from scripts.modules.self_model import refresh as refresh_self

    action      = intent["action"]
    target_hint = intent["target_hint"]
    description = intent["description"]
    risk        = intent["risk"]
    user_id     = update.effective_user.id

    send = update.message.reply_text

    # ── Meta-actions ──
    if action == "show_goals":
        await send(goals_summary(), parse_mode="Markdown")
        return

    if action == "show_status":
        await send(build_status_report(), parse_mode="Markdown")
        return

    if action == "show_drafts":
        drafts = list_drafts()
        if not drafts:
            await send("📋 No pending drafts.")
            return
        lines = ["📋 *Pending Drafts:*\n"]
        for did, v in drafts.items():
            target_name = Path(v.get("target", "unknown")).name
            desc = v.get("description", "")
            lines.append(f"• `{did}` — `{target_name}` — _{desc}_")
        await send("\n".join(lines), parse_mode="Markdown")
        return

    if action == "rollback":
        fname = target_hint if target_hint != "unknown" else None
        if not fname:
            await send("Which file should I roll back? e.g. `rollback bot.py`", parse_mode="Markdown")
            return
        for p in [Path(fname), ROOT / "scripts/modules" / fname]:
            if p.exists() or list_backups(p):
                r = do_rollback(p)
                if r["success"]:
                    bak = Path(r["restored_from"]).name
                    await send(f"✅ Rolled back `{fname}` from `{bak}`", parse_mode="Markdown")
                else:
                    await send(f"❌ Rollback failed: {r['error']}")
                return
        await send(f"❌ No backups found for `{target_hint}`", parse_mode="Markdown")
        return

    # ── Resolve target path ──
    if target_hint == "unknown" or not target_hint:
        await send(
            "⚠️ I couldn't determine which file to edit.\n"
            "Be more specific — e.g. _'add /ping command to bot.py'_",
            parse_mode="Markdown"
        )
        return

    target_path = Path(target_hint)
    if not target_path.is_absolute():
        # Resolve relative to project root
        if not (ROOT / target_path).exists() and "modules" not in str(target_path):
            candidate = ROOT / "scripts/modules" / target_path
            if candidate.exists():
                target_path = candidate
            else:
                target_path = ROOT / target_path
        else:
            target_path = ROOT / target_path

    actual_risk = risk_level(target_path)  # always use code_editor's classification
    if actual_risk == "high":
        risk = "high"

    # ── Announce plan ──
    await send(
        f"🔍 *Code request detected*\n"
        f"Action: `{action}`\n"
        f"Target: `{target_path.name}`\n"
        f"Risk: {'🔴 HIGH' if risk == 'high' else '🟢 LOW'}\n"
        f"Plan: _{description}_\n\n"
        f"⚙️ Generating code...",
        parse_mode="Markdown"
    )

    # ── Generate code ──
    new_code = await generate_code(description, target_path)
    if not new_code or len(new_code.strip()) < 20:
        await send("❌ Code generation returned empty result. LLM may be down. Try again.")
        return

    # ── Compile check ──
    ok, err = compile_check_string(new_code)
    if not ok:
        await send(
            f"❌ Generated code failed compile check:\n`{err}`\n\nAborted — nothing changed.",
            parse_mode="Markdown"
        )
        return

    await send("✅ Compile check passed.")

    # ── Apply or stage ──
    if risk == "low":
        result = apply_patch(target_path, new_code)
        if result["success"]:
            bak = Path(result["backup_path"]).name if result["backup_path"] else "none"
            await send(
                f"✅ *Applied to* `{target_path.name}`\n"
                f"Backup: `{bak}`\n"
                f"Compile: passed ✓\n\n"
                f"Test it now.",
                parse_mode="Markdown"
            )
            # Post-edit: refresh self-model, update goals, suggest next
            refresh_self()
            next_goal = on_capability_added(description, str(target_path))
            if next_goal:
                await send(f"🎯 *Next goal queued:*\n_{next_goal}_", parse_mode="Markdown")
        else:
            await send(
                f"❌ Apply failed at stage `{result['stage']}`:\n{result['error']}",
                parse_mode="Markdown"
            )

    else:  # HIGH RISK — stage for approval
        bak_path = ""
        if target_path.exists():
            try: bak_path = str(backup_file(target_path))
            except Exception: pass

        did = store_draft(user_id, str(target_path), new_code, description, bak_path)
        await send(
            f"📋 *Draft staged* — ID: `{did}`\n"
            f"Target: `{target_path.name}`\n"
            f"Plan: _{description}_\n"
            f"Compile: passed ✓\n\n"
            f"Reply _yes_, _approve_, or _go ahead_ to apply\n"
            f"Or say _approve {did}_ — /reject {did} to cancel",
            parse_mode="Markdown"
        )


async def maybe_handle_code_after_reply(update, context, text: str, owner_id: int) -> None:
    """
    Called from on_text after the conversational reply is sent.
    If the message is a code request and the user is the owner, run the full code-request flow.
    """
    if not text or not text.strip():
        return
    try:
        intent = parse_code_request(text.strip())
    except Exception:
        return
    if not intent.get("is_code_request"):
        return
    if getattr(update.effective_user, "id", None) != owner_id:
        return
    await handle_code_request(update, context, intent, owner_id)
