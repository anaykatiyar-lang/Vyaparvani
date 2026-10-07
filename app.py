from __future__ import annotations

import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from vyaparvani.http_api import calculate_fields, extract, request_payload, send_json

ROOT = Path(__file__).parent
PORT = int(os.environ.get("VYAPARVANI_PORT", "8000"))
class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT / "public"), **kwargs)

    def do_POST(self):
        route = urlparse(self.path).path
        if route not in {"/api/extract", "/api/calculate"}:
            return self.send_error(404)
        body = request_payload(self)
        if body is None:
            return
        if route == "/api/extract":
            return send_json(self, extract(body))
        return send_json(self, calculate_fields(body))


if __name__ == "__main__":
    print(f"VyaparVani is running at http://127.0.0.1:{PORT}")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
