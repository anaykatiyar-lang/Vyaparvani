"""Shared HTTP request helpers for the local server and Vercel functions."""

import json
import os

from .calculator import calculate
from .extraction import ManualTextProvider
from .vision import extract_invoice_image

provider = ManualTextProvider()


def decode_body(raw):
    return json.loads(raw or b"{}")


def extract(payload):
    fields = provider.extract_text(str(payload.get("text", "")))
    fields["source"] = "typed_text"
    return {"fields": fields}


def calculate_fields(payload):
    return calculate(payload)


def config():
    enabled = bool(os.environ.get("GEMINI_API_KEY"))
    return {"provider": "gemini" if enabled else "manual_text", "image_ocr": enabled}


def extract_image(payload):
    if not os.environ.get("GEMINI_API_KEY"):
        raise ProviderNotConfigured("Photo reading is not configured. Enter or paste the printed details instead.")
    return {"fields": extract_invoice_image(payload)}


def send_json(handler, payload, status=200):
    body = json.dumps(payload).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(body)


def request_payload(handler):
    try:
        length = int(handler.headers.get("Content-Length", "0"))
        payload = decode_body(handler.rfile.read(length))
        if not isinstance(payload, dict):
            raise ValueError("The request body must be a JSON object.")
        return payload
    except (ValueError, json.JSONDecodeError) as error:
        send_json(handler, {"error": str(error)}, 400)
        return None


class ProviderNotConfigured(Exception):
    """The requested extraction provider has no server-side credentials."""
