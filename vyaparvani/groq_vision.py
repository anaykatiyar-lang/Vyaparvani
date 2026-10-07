"""Groq vision extraction. The model reports facts; Python validates and calculates."""

import base64
import json
import logging
import os
import re
import socket
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


MAX_IMAGE_BYTES = 3 * 1024 * 1024
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
MODEL = "qwen/qwen3.8-27b"

PROMPT = """Extract only printed facts from this FMCG purchase invoice. Ignore handwriting, handwritten scheme notes, and discounts as evidence of free goods. Do not calculate a landing price. net_amount_paid must be the GST-inclusive amount actually payable and only when clearly attributable to one selected product; never use a multi-product invoice total for a single product. paid_quantity is the printed paid quantity. Set quantity_unit to carton only if cartons/cases are explicitly printed; otherwise use the printed unit as jar, piece, bag, unit, or unknown. free_cartons is non-null only when the source explicitly states free cartons. If a value is absent, unreadable, or ambiguous, use null. If multiple product lines cannot be distinguished safely, set product, net_amount_paid, paid_quantity, and quantity_unit to null. evidence contains short quotes from printed text only. Return the requested JSON fields only."""


SCHEMA = {
    "type": "object",
    "properties": {
        "product": {"type": ["string", "null"]},
        "net_amount_paid": {"type": ["string", "null"]},
        "paid_quantity": {"type": ["string", "null"]},
        "quantity_unit": {"type": "string", "enum": ["carton", "jar", "piece", "bag", "unit", "unknown"]},
        "free_cartons": {"type": ["string", "null"]},
        "evidence": {"type": "object", "additionalProperties": {"type": "string"}},
    },
    "required": ["product", "net_amount_paid", "paid_quantity", "quantity_unit", "free_cartons", "evidence"],
    "additionalProperties": False,
}


def _image_data_url(payload):
    data_url = str(payload.get("image_data_url") or "")
    match = re.fullmatch(r"data:(image/(?:jpeg|png|webp));base64,([A-Za-z0-9+/=\s]+)", data_url)
    if not match:
        raise ValueError("Choose a JPG, PNG or WebP invoice photo.")
    mime_type, encoded = match.groups()
    try:
        image_bytes = base64.b64decode(re.sub(r"\s+", "", encoded), validate=True)
    except ValueError as error:
        raise ValueError("The image could not be read. Choose it again and retry.") from error
    if not image_bytes or len(image_bytes) > MAX_IMAGE_BYTES:
        raise ValueError("The compressed photo must be smaller than 3 MB. Please choose a smaller image.")
    return mime_type, f"data:{mime_type};base64,{base64.b64encode(image_bytes).decode('ascii')}"


def extract_invoice_image_with_groq(payload):
    mime_type, image_data_url = _image_data_url(payload)
    model = os.environ.get("GROQ_VISION_MODEL", MODEL).strip() or MODEL
    api_key = os.environ.get("GROQ_API_KEY", "").strip()
    if not api_key:
        raise ValueError("Groq photo reading is not configured. Add GROQ_API_KEY to the server environment.")

    request_body = {
        "model": model,
        "messages": [
            {"role": "system", "content": PROMPT},
            {"role": "user", "content": [
                {"type": "text", "text": "Read the invoice and extract the printed fields."},
                {"type": "image_url", "image_url": {"url": image_data_url}},
            ]},
        ],
        "response_format": {"type": "json_schema", "json_schema": {
            "name": "invoice_fields", "strict": True, "schema": SCHEMA,
        }},
        "max_completion_tokens": 800,
        "reasoning_effort": "none",
        "temperature": 0,
    }
    request = Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=json.dumps(request_body).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=45) as response:
            response_data = json.loads(response.read())
    except HTTPError as error:
        try:
            provider_error = json.loads(error.read().decode("utf-8"))
            detail = provider_error.get("error", {}).get("message", "")
        except (UnicodeDecodeError, json.JSONDecodeError, AttributeError):
            detail = ""
        logging.warning("Groq vision returned HTTP %s: %s", error.code, str(detail)[:300])
        if error.code in (401, 403):
            raise ValueError("Groq rejected the API key or its access. Check GROQ_API_KEY in server settings.") from error
        if error.code == 429:
            raise ValueError("Groq's free-tier limit was reached. Wait for the limit to reset or check your Groq Console usage.") from error
        if error.code in (400, 413, 415):
            raise ValueError("Groq could not process this photo. Choose a clear JPG, PNG or WebP image and retry.") from error
        if error.code >= 500:
            raise ValueError("Groq vision is temporarily unavailable. Wait a moment and retry, or enter the details manually.") from error
        raise ValueError("Groq could not read this invoice. Please retry or enter the details manually.") from error
    except URLError as error:
        reason = error.reason
        logging.warning("Groq connection failed (%s).", type(reason).__name__)
        if isinstance(reason, (TimeoutError, socket.timeout)):
            raise ValueError("Groq did not respond in time. Wait a moment and retry, or enter the details manually.") from error
        raise ValueError("The app server cannot connect to Groq. Check its internet connection, then retry.") from error
    except (TimeoutError, socket.timeout) as error:
        logging.warning("Groq vision request timed out.")
        raise ValueError("Groq did not respond in time. Wait a moment and retry, or enter the details manually.") from error

    try:
        message = response_data["choices"][0]["message"]
        fields = json.loads(message["content"])
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as error:
        raise ValueError("Groq did not return structured invoice fields. Enter them manually.") from error

    unit = str(fields.get("quantity_unit") or "unknown").strip().lower()
    if unit not in {"carton", "jar", "piece", "bag", "unit", "unknown"}:
        unit = "unknown"
    return {
        "product": fields.get("product") if isinstance(fields.get("product"), str) else None,
        "net_amount_paid": fields.get("net_amount_paid") if isinstance(fields.get("net_amount_paid"), str) else None,
        "paid_quantity": fields.get("paid_quantity") if isinstance(fields.get("paid_quantity"), str) else None,
        "quantity_unit": unit,
        "free_cartons": fields.get("free_cartons") if isinstance(fields.get("free_cartons"), str) else None,
        "evidence": fields.get("evidence") if isinstance(fields.get("evidence"), dict) else {},
        "source": "invoice_photo",
        "ocr_provider": "groq",
    }
