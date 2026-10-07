from http.server import BaseHTTPRequestHandler

from vyaparvani.http_api import calculate_fields, request_payload, send_json


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        payload = request_payload(self)
        if payload is not None:
            send_json(self, calculate_fields(payload))

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()
