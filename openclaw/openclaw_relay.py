"""Minimal local OpenClaw-compatible relay for KonstanceAI.

This relay supports:
- GET /health for launcher and status checks
- POST / with {"message": "...", "context": {...}} and {"response": "..."} output
"""

from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib import request as urllib_request
from urllib.error import URLError


def _relay_bind() -> tuple[str, int]:
    raw = (os.getenv("OPENCLAW_RELAY_URL") or "ws://127.0.0.1:18789").strip()
    if raw.startswith("ws://"):
        raw = "http://" + raw[5:]
    elif raw.startswith("wss://"):
        raw = "https://" + raw[6:]

    host_port = raw.split("://", 1)[-1].split("/", 1)[0].strip()
    host, _, port_text = host_port.partition(":")
    host = host or "127.0.0.1"
    try:
        port = int(port_text) if port_text else 18789
    except ValueError:
        port = 18789
    return host, port


def _relay_token() -> str:
    return (os.getenv("OPENCLAW_RELAY_TOKEN") or "").strip()


def _safe_json(data: bytes) -> dict:
    try:
        return json.loads(data.decode("utf-8", errors="ignore"))
    except Exception:
        return {}


def _ollama_generate(prompt: str, timeout_sec: int = 45) -> str:
    model = (os.getenv("OPENCLAW_OLLAMA_MODEL") or os.getenv("OLLAMA_MODEL") or "qwen2.5:3b").strip()
    payload = {"model": model, "prompt": prompt, "stream": False}
    req = urllib_request.Request(
        "http://127.0.0.1:11434/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib_request.urlopen(req, timeout=timeout_sec) as resp:
        raw = resp.read().decode("utf-8", errors="ignore")
    body = json.loads(raw)
    return str(body.get("response") or "").strip()


class RelayHandler(BaseHTTPRequestHandler):
    server_version = "OpenClawRelay/0.1"

    def log_message(self, fmt: str, *args) -> None:
        return

    def _json(self, code: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _authorized(self) -> bool:
        token = _relay_token()
        if not token:
            return True
        auth = self.headers.get("Authorization", "").strip()
        return auth == f"Bearer {token}"

    def do_GET(self) -> None:
        if self.path.rstrip("/") == "/health":
            self._json(200, {"ok": True, "service": "openclaw-relay"})
            return
        self._json(404, {"error": "not_found"})

    def do_POST(self) -> None:
        if not self._authorized():
            self._json(401, {"error": "unauthorized"})
            return

        length = int(self.headers.get("Content-Length", "0") or "0")
        payload = _safe_json(self.rfile.read(length))
        message = str(payload.get("message") or "").strip()
        context = payload.get("context") or {}
        if not message:
            self._json(400, {"error": "missing_message"})
            return

        prompt = message
        if isinstance(context, dict):
            history = context.get("history") or []
            if isinstance(history, list) and history:
                snippets = []
                for item in history[-4:]:
                    if isinstance(item, dict):
                        user = str(item.get("user") or "").strip()
                        bot = str(item.get("bot") or "").strip()
                        if user:
                            snippets.append(f"User: {user}")
                        if bot:
                            snippets.append(f"Assistant: {bot}")
                if snippets:
                    prompt = "\n".join(snippets + [f"User: {message}", "Assistant:"])

        try:
            text = _ollama_generate(prompt)
        except (URLError, OSError, TimeoutError, ValueError, json.JSONDecodeError):
            text = ""

        if not text:
            text = "OpenClaw relay online. Ollama is not responding yet."

        self._json(200, {"response": text})


def main() -> int:
    host, port = _relay_bind()
    server = ThreadingHTTPServer((host, port), RelayHandler)
    print(f"OpenClaw relay listening on http://{host}:{port}")
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
