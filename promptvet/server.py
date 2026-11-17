"""Tiny HTTP server for containers (EKS). Stdlib only: no framework CVEs to patch."""
from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .api import MAX_CHARS, MAX_ITEMS, handle

STATIC = Path(os.getenv("PROMPTVET_STATIC", Path(__file__).resolve().parent.parent / "public"))
MAX_BODY = MAX_CHARS * MAX_ITEMS // 10


class Handler(BaseHTTPRequestHandler):
    server_version = "promptvet"

    def _send(self, code: int, body: bytes, ctype: str = "application/json") -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ("/healthz", "/readyz"):
            return self._send(200, b'{"ok":true}')
        name = {"/": "index.html", "/report": "report.html", "/report.html": "report.html",
                "/summary.json": "summary.json"}.get(self.path)
        f = STATIC / name if name else None
        if f and f.is_file():
            ctype = "application/json" if name.endswith(".json") else "text/html; charset=utf-8"
            return self._send(200, f.read_bytes(), ctype)
        self._send(404, b'{"error":"not found"}')

    def do_POST(self):
        if self.path != "/api/scan":
            return self._send(404, b'{"error":"not found"}')
        n = int(self.headers.get("Content-Length") or 0)
        if n > MAX_BODY:
            return self._send(413, b'{"error":"body too large"}')
        try:
            payload = json.loads(self.rfile.read(n) or b"{}")
        except json.JSONDecodeError:
            return self._send(400, b'{"error":"invalid JSON"}')
        code, out = handle(payload)
        self._send(code, json.dumps(out).encode())

    def log_message(self, fmt, *args):
        print(json.dumps({"path": self.path, "msg": fmt % args}))


def serve(host: str = "0.0.0.0", port: int = 8080) -> None:
    ThreadingHTTPServer((host, port), Handler).serve_forever()
