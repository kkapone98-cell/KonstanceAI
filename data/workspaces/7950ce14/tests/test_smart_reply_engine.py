import json
import os
import unittest
from unittest.mock import patch

from scripts.modules import smart_reply_engine as s


class DummyResp:
    def __init__(self, payload, status=200):
        self.payload = payload
        self.status = status

    def read(self):
        return self.payload.encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class SmartReplyEngineTests(unittest.TestCase):
    def test_relay_url_normalization(self):
        with patch.dict(os.environ, {"OPENCLAW_RELAY_URL": "ws://127.0.0.1:18789"}, clear=False):
            self.assertEqual(s._relay_http_url(), "http://127.0.0.1:18789")

    def test_openclaw_generate_parses_response_field(self):
        with patch.dict(os.environ, {"OPENCLAW_RELAY_URL": "http://relay.local"}, clear=False):
            with patch("scripts.modules.smart_reply_engine.urllib_request.urlopen", return_value=DummyResp(json.dumps({"response": "hello"}))):
                out = s.openclaw_generate("hi", {}, {})
                self.assertEqual(out, "hello")

    def test_smart_reply_uses_local_when_cloud_empty(self):
        with patch("scripts.modules.smart_reply_engine.openclaw_generate", return_value=""):
            with patch("scripts.modules.smart_reply_engine._ollama_generate", return_value="local answer"):
                out = s.smart_reply("ping", {"verbosity": "medium"}, {})
                self.assertIn("local answer", out)


if __name__ == "__main__":
    unittest.main()
