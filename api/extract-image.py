from http.server import BaseHTTPRequestHandler

from vyaparvani.http_api import ProviderNotConfigured, extract_image, request_payload, send_json


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        payload = request_payload(self)
        if payload is None:
            return
        try:
            send_json(self, extract_image(payload))
        except ProviderNotConfigured as error:
            send_json(self, {"error": str(error)}, 503)
        except ValueError as error:
            send_json(self, {"error": str(error)}, 400)
