import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.config import load_config
from core.state import RuntimeState
from doctor.analyzer import analyze_runtime
from doctor.recovery import persist_report


class DoctorSystemTests(unittest.TestCase):
    def test_doctor_finds_health_and_log_issues(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "data" / "doctor").mkdir(parents=True)
            (root / "logs").mkdir()
            (root / "logs" / "bot.log").write_text("ERROR Traceback sample\n", encoding="utf-8")

            with patch.dict(
                "os.environ",
                {"TELEGRAM_BOT_TOKEN": "123:abc", "OWNER_ID": "99", "KONSTANCE_ROOT": str(root)},
                clear=False,
            ):
                config = load_config(root)
                state = RuntimeState(config)
                state.ensure()
                state.update_health(relay_available=False, ollama_available=False, quarantined=True)

                report = analyze_runtime(state)
                self.assertFalse(report.ok)
                self.assertTrue(report.findings)

                persist_report(state, report)
                saved = state.doctor_reports_path.read_text(encoding="utf-8")
                self.assertIn("Doctor found issues", saved)


if __name__ == "__main__":
    unittest.main()

