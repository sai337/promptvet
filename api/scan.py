"""Vercel Python function: POST /api/scan  (same contract as the container server)."""
import json
import os
import sys
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from promptvet.api import MAX_CHARS, MAX_ITEMS, handle  # noqa: E402

MAX_BODY = MAX_CHARS * MAX_ITEMS // 10


class handler(BaseHTTPRequestHandler):  # noqa: N801 (Vercel requires this name)
    def _send(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):  # noqa: N802
        n = int(self.headers.get("Content-Length") or 0)
        if n > MAX_BODY:
            return self._send(413, {"error": "body too large"})
        try:
            payload = json.loads(self.rfile.read(n) or b"{}")
        except json.JSONDecodeError:
            return self._send(400, {"error": "invalid JSON"})
        code, out = handle(payload)
        self._send(code, out)

    def do_GET(self):  # noqa: N802
        self._send(405, {"error": "POST a JSON body: {\"prompt\": \"...\"}"})
