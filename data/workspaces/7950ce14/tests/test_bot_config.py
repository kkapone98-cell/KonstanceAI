import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import bot


class BotConfigTests(unittest.TestCase):
    def test_load_token_from_env(self):
        with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "123:abc"}, clear=False):
            tok = bot._load_token()
            self.assertEqual(tok, "123:abc")

    def test_load_token_from_file(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "telegram_token.txt").write_text("777:xyz", encoding="utf-8")
            with patch("bot.ROOT", root):
                with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": ""}, clear=False):
                    tok = bot._load_token()
                    self.assertEqual(tok, "777:xyz")


if __name__ == "__main__":
    unittest.main()
