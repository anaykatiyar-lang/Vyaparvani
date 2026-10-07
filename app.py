from __future__ import annotations

import json
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from vyaparvani.calculator import calculate
from vyaparvani.extraction import ManualTextProvider

ROOT = Path(__file__).parent
PORT = int(os.environ.get("VYAPARVANI_PORT", "8000"))
PROVIDER_NAME = "manual_text"
provider = ManualTextProvider()


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT / "web"), **kwargs)

    def send_json(self, payload, status=200):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if urlparse(self.path).path == "/api/config":
            return self.send_json({"provider": PROVIDER_NAME})
        return super().do_GET()

    def do_POST(self):
        route = urlparse(self.path).path
        if route not in {"/api/extract", "/api/calculate"}:
            return self.send_error(404)
        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(length) or b"{}")
            if route == "/api/extract":
                fields = provider.extract_text(str(body.get("text", "")))
                fields["source"] = "typed_text"
                return self.send_json({"fields": fields})
            return self.send_json(calculate(body))
        except (ValueError, json.JSONDecodeError) as exc:
            return self.send_json({"error": str(exc)}, 400)


if __name__ == "__main__":
    print(f"VyaparVani is running at http://127.0.0.1:{PORT}")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
