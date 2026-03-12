"""Legacy OpenClaw wrapper kept as a compatibility guard."""

from scripts.modules.smart_reply_engine import generate_file_update


def edit_file_openclaw(file_path, content):
    raise RuntimeError(
        "Direct live-file editing through tools/openclaw_manager.py is retired. "
        "Use ai_brain.self_upgrade_agent.plan_upgrade_request instead."
    )


def generate_openclaw_patch(description, target_path, current_text=""):
    return generate_file_update(description=description, target_path=str(target_path), current_text=current_text)
