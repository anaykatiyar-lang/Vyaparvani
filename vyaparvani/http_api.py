"""Shared HTTP request helpers for the local server and Vercel functions."""

import json
import os
import base64
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .calculator import calculate
from .extraction import ManualTextProvider

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
    enabled = bool(os.environ.get("GOOGLE_VISION_API_KEY", "").strip())
    return {"provider": "google_cloud_vision" if enabled else "manual_text", "image_ocr": enabled}


def extract_image(payload):
    api_key = os.environ.get("GOOGLE_VISION_API_KEY", "").strip()
    if not api_key:
        raise ProviderNotConfigured("Photo reading is not configured. Set GOOGLE_VISION_API_KEY on the server.")
    data_url = str(payload.get("image_data_url") or "")
    match = re.fullmatch(r"data:(image/(?:jpeg|png|webp));base64,([A-Za-z0-9+/=\s]+)", data_url)
    if not match:
        raise ValueError("Choose a JPG, PNG or WebP invoice photo.")
    try:
        image = base64.b64decode(re.sub(r"\s+", "", match.group(2)), validate=True)
    except ValueError as error:
        raise ValueError("The image could not be read. Choose it again and retry.") from error
    if not image or len(image) > 3 * 1024 * 1024:
        raise ValueError("The compressed photo must be smaller than 3 MB. Please choose a smaller image.")
    request_body = {
        "requests": [{
            "image": {"content": base64.b64encode(image).decode("ascii")},
            "features": [{"type": "DOCUMENT_TEXT_DETECTION"}],
            "imageContext": {"languageHints": ["en", "hi"]},
        }],
    }
    request = Request(
        "https://vision.googleapis.com/v1/images:annotate",
        data=json.dumps(request_body).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
        method="POST",
    )
    try:
        with urlopen(request, timeout=50) as response:
            result = json.loads(response.read())
    except HTTPError as error:
        if error.code in (401, 403):
            raise ValueError("Google rejected the API key or the Cloud Vision API is not enabled for its project. Check the key and API restrictions.") from error
        if error.code == 429:
            raise ValueError("Google Cloud Vision quota was reached. Check the project's Vision API usage and quota.") from error
        if error.code in (400, 413, 415):
            raise ValueError("Google Cloud Vision could not process this photo. Choose a clear JPG, PNG or WebP image and retry.") from error
        raise ValueError("Google Cloud Vision could not read this photo. Retry or enter the details manually.") from error
    except (URLError, TimeoutError, OSError) as error:
        raise ValueError("Could not reach Google Cloud Vision. Check the connection and retry.") from error
    try:
        annotation = result["responses"][0]
    except (KeyError, IndexError, TypeError) as error:
        raise ValueError("Google Cloud Vision returned an unreadable response. Retry or enter the details manually.") from error
    if annotation.get("error"):
        detail = annotation["error"].get("message", "").strip()
        raise ValueError(detail or "Google Cloud Vision could not read this photo.")
    text = annotation.get("fullTextAnnotation", {}).get("text")
    if not isinstance(text, str) or not text.strip():
        raise ValueError("No readable text was found in this photo. Try a sharper image or enter the details manually.")
    fields = provider.extract_text(text)
    fields.update({"source": "invoice_photo", "ocr_provider": "google_cloud_vision", "ocr_text": text})
    return {"fields": fields}


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
    """Google Cloud Vision is not configured on the server."""
