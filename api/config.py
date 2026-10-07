from http.server import BaseHTTPRequestHandler

from vyaparvani.http_api import config, send_json


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        send_json(self, config())
