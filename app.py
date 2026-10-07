from __future__ import annotations

import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from vyaparvani.local_env import load_local_env

load_local_env()

from vyaparvani.http_api import ProviderNotConfigured, calculate_fields, config, extract, extract_image, request_payload, send_json

ROOT = Path(__file__).parent
PORT = int(os.environ.get("VYAPARVANI_PORT", "8000"))
class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT / "public"), **kwargs)

    def do_GET(self):
        if urlparse(self.path).path == "/api/config":
            return send_json(self, config())
        return super().do_GET()

    def do_POST(self):
        route = urlparse(self.path).path
        if route not in {"/api/extract", "/api/calculate", "/api/extract-image"}:
            return self.send_error(404)
        body = request_payload(self)
        if body is None:
            return
        if route == "/api/extract":
            return send_json(self, extract(body))
        if route == "/api/extract-image":
            try:
                return send_json(self, extract_image(body))
            except ProviderNotConfigured as error:
                return send_json(self, {"error": str(error)}, 503)
            except ValueError as error:
                return send_json(self, {"error": str(error)}, 400)
        return send_json(self, calculate_fields(body))


if __name__ == "__main__":
    print(f"VyaparVani is running at http://127.0.0.1:{PORT}")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
