import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.config import load_config
from upgrade_system.promoter import promote_workspace
from upgrade_system.rollback import rollback_last_promotion


class UpgradePipelineTests(unittest.TestCase):
    def test_promote_and_rollback(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "data" / "upgrade_history").mkdir(parents=True)
            (root / "logs").mkdir()
            (root / "ai_brain").mkdir()
            live_file = root / "ai_brain" / "sample.py"
            live_file.write_text("value = 1\n", encoding="utf-8")

            workspace = root / "data" / "workspaces" / "draft01"
            workspace.mkdir(parents=True)
            (workspace / "ai_brain").mkdir()
            (workspace / "ai_brain" / "sample.py").write_text("value = 2\n", encoding="utf-8")

            with patch.dict(
                "os.environ",
                {"TELEGRAM_BOT_TOKEN": "123:abc", "OWNER_ID": "99", "KONSTANCE_ROOT": str(root)},
                clear=False,
            ):
                config = load_config(root)
                result = promote_workspace(config, workspace, "draft01")
                self.assertTrue(result["success"])
                self.assertEqual(live_file.read_text(encoding="utf-8"), "value = 2\n")
                upgrades_memory = root / "data" / "memory" / "upgrades.json"
                self.assertTrue(upgrades_memory.exists())
                self.assertIn('"event": "promoted"', upgrades_memory.read_text(encoding="utf-8"))

                rolled = rollback_last_promotion(config)
                self.assertTrue(rolled["success"])
                self.assertEqual(live_file.read_text(encoding="utf-8"), "value = 1\n")
                self.assertIn('"event": "rolled_back"', upgrades_memory.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

