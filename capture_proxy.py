#!/usr/bin/env python3
"""Logging reverse-proxy for api.anthropic.com.

Run the Claude CLI with ANTHROPIC_BASE_URL=http://127.0.0.1:8399 and every
outbound /v1/messages request body is written to captures/req-<n>.json before
being forwarded upstream (SSE responses are relayed chunk-by-chunk).

Purpose: byte-level evidence of what the system prompt contains on the
session-creating turn vs resumed turns.
"""
import itertools
import json
import ssl
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import requests

UPSTREAM = "https://api.anthropic.com"
CAPTURE_DIR = Path(__file__).parent / "captures"
CAPTURE_DIR.mkdir(exist_ok=True)
_counter = itertools.count(1)
_lock = threading.Lock()

HOP_HEADERS = {"host", "content-length", "transfer-encoding", "connection", "accept-encoding"}


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        pass

    def _relay(self, method):
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length else b""

        if method == "POST" and "/v1/messages" in self.path and body:
            with _lock:
                n = next(_counter)
            try:
                parsed = json.loads(body)
                (CAPTURE_DIR / f"req-{n:03d}.json").write_text(json.dumps(parsed, indent=1))
            except json.JSONDecodeError:
                (CAPTURE_DIR / f"req-{n:03d}.raw").write_bytes(body)

        headers = {k: v for k, v in self.headers.items() if k.lower() not in HOP_HEADERS}
        upstream = requests.request(method, UPSTREAM + self.path, headers=headers,
                                    data=body or None, stream=True, timeout=600)
        self.send_response(upstream.status_code)
        for k, v in upstream.headers.items():
            if k.lower() in {"content-length", "transfer-encoding", "connection", "content-encoding"}:
                continue
            self.send_header(k, v)
        self.send_header("Transfer-Encoding", "chunked")
        self.end_headers()
        for chunk in upstream.iter_content(chunk_size=None):
            if chunk:
                self.wfile.write(f"{len(chunk):X}\r\n".encode() + chunk + b"\r\n")
                self.wfile.flush()
        self.wfile.write(b"0\r\n\r\n")

    def do_POST(self):
        self._relay("POST")

    def do_GET(self):
        self._relay("GET")


if __name__ == "__main__":
    srv = ThreadingHTTPServer(("127.0.0.1", 8399), Handler)
    print("capture proxy on http://127.0.0.1:8399 -> api.anthropic.com")
    srv.serve_forever()
