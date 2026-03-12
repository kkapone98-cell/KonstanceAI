import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.application import KonstanceApplication
from ai_brain.intent_parser import parse_intent
from core.config import load_config
from core.contracts import MessageContext
from scripts.modules.safe_executor import install_dependency


class TelegramIntegrationTests(unittest.TestCase):
    def test_status_and_preferences_flow(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "data").mkdir()
            (root / "logs").mkdir()
            with patch.dict(
                "os.environ",
                {"TELEGRAM_BOT_TOKEN": "123:abc", "OWNER_ID": "99", "KONSTANCE_ROOT": str(root)},
                clear=False,
            ):
                config = load_config(root)
                app = KonstanceApplication(config)

                with patch("core.application.relay_available", return_value=False), patch(
                    "core.application.ollama_fallback_available", return_value=True
                ):
                    status = app.handle_user_message(MessageContext(user_id=99, text="/status", is_owner=True))
                self.assertIn("Status: running", status.text)
                self.assertIn("Ollama available: True", status.text)

                updated = app.handle_user_message(
                    MessageContext(user_id=99, text="set verbosity to short", is_owner=True)
                )
                self.assertIn("Verbosity updated", updated.text)
                self.assertEqual(app.state.load_prefs()["verbosity"], "short")

    def test_owner_safe_command_policy(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "data").mkdir()
            (root / "logs").mkdir()
            (root / "launcher.py").write_text("print('ok')\n", encoding="utf-8")
            with patch.dict(
                "os.environ",
                {"TELEGRAM_BOT_TOKEN": "123:abc", "OWNER_ID": "99", "KONSTANCE_ROOT": str(root)},
                clear=False,
            ):
                app = KonstanceApplication(load_config(root))
                blocked = app.handle_user_message(
                    MessageContext(user_id=99, text="/run del important.txt", is_owner=True)
                )
                self.assertIn("Command failed", blocked.text)
                self.assertTrue(blocked.metadata.get("owner_alert"))

    def test_startclean_intent_matches_slash_command(self):
        intent = parse_intent("/startclean")
        self.assertEqual(intent.name, "start_clean")

    def test_install_dependency_package_command_has_no_quotes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "data").mkdir()
            (root / "logs").mkdir()
            with patch.dict(
                "os.environ",
                {"TELEGRAM_BOT_TOKEN": "123:abc", "OWNER_ID": "99", "KONSTANCE_ROOT": str(root)},
                clear=False,
            ):
                config = load_config(root)
                with patch("scripts.modules.safe_executor.execute_owner_command") as mock_exec:
                    mock_exec.return_value = {"ok": True, "returncode": 0, "output": "ok", "command": []}
                    install_dependency(config, "requests")
                    called = mock_exec.call_args[0][1]
                    self.assertEqual(called, "python -m pip install requests")

    def test_non_owner_cannot_plan_upgrade(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "data").mkdir()
            (root / "logs").mkdir()
            with patch.dict(
                "os.environ",
                {"TELEGRAM_BOT_TOKEN": "123:abc", "OWNER_ID": "99", "KONSTANCE_ROOT": str(root)},
                clear=False,
            ):
                app = KonstanceApplication(load_config(root))
                response = app.handle_user_message(
                    MessageContext(user_id=5, text="fix bot.py", is_owner=False)
                )
                self.assertIn("Not authorized", response.text)


if __name__ == "__main__":
    unittest.main()

