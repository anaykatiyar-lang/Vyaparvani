from http.server import BaseHTTPRequestHandler

from vyaparvani.http_api import extract, request_payload, send_json


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        payload = request_payload(self)
        if payload is not None:
            send_json(self, extract(payload))

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()
