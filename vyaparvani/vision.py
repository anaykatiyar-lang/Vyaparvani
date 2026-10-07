"""Optional Gemini vision extraction. The model reports facts; calculator.py does the maths."""

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


def _json_from_model(text):
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.IGNORECASE)
    value = json.loads(cleaned)
    if not isinstance(value, dict):
        raise ValueError("The image reader returned an unexpected response.")
    return value


def extract_invoice_image(payload):
    data_url = str(payload.get("image_data_url") or "")
    match = re.fullmatch(r"data:(image/(?:jpeg|png|webp));base64,([A-Za-z0-9+/=\s]+)", data_url)
    if not match:
        raise ValueError("Choose a JPG, PNG or WebP invoice photo.")
    mime_type, encoded = match.groups()
    if mime_type not in ALLOWED_MIME_TYPES:
        raise ValueError("Choose a JPG, PNG or WebP invoice photo.")
    try:
        image_bytes = base64.b64decode(re.sub(r"\s+", "", encoded), validate=True)
    except ValueError as error:
        raise ValueError("The image could not be read. Choose it again and retry.") from error
    if not image_bytes or len(image_bytes) > MAX_IMAGE_BYTES:
        raise ValueError("The compressed photo must be smaller than 3 MB. Please choose a smaller image.")

    # Accept the common underscore spelling from environment files, then use
    # Google's canonical model ID in the REST path.
    model = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash").strip().replace("_", "-")
    if model.startswith("models/"):
        model = model[len("models/"):]
    key = os.environ["GEMINI_API_KEY"]
    prompt = """Read this FMCG purchase invoice. Return only a JSON object with exactly these keys: product, net_amount_paid, paid_quantity, quantity_unit, free_cartons, evidence.

Rules: extract printed facts only. Ignore handwriting, handwritten scheme notes, discounts as evidence of free goods, and any arithmetic you might otherwise do. Do not calculate or estimate a landing price. net_amount_paid must be the printed net/grand amount actually payable including GST, as a decimal string, only when clearly attributable to the selected single product; never use a multi-product invoice total for one product. paid_quantity must be the printed paid quantity as a decimal string. quantity_unit must be one of carton, jar, piece, bag, unit, unknown; use carton only if cartons/cases are explicitly printed, preserve UNIT/UNT/BAG/PCS/CA as their appropriate ambiguous category, and use unknown for anything else. free_cartons is a decimal string only when the printed source explicitly states free cartons; otherwise null. If a value is absent, unreadable, or unclear, return null for it. If the invoice has multiple product lines and no single product can be safely selected, return null for product, net_amount_paid, paid_quantity, and quantity_unit. evidence is a short object mapping extracted keys to a short quote or description of the printed source, never handwritten text.

JSON shape: {"product": string|null, "net_amount_paid": string|null, "paid_quantity": string|null, "quantity_unit": string|null, "free_cartons": string|null, "evidence": object}."""
    request_body = {
        "contents": [{"parts": [
            {"inline_data": {"mime_type": mime_type, "data": base64.b64encode(image_bytes).decode("ascii")}},
            {"text": prompt},
        ]}],
        # Gemini 3.x defaults to medium reasoning. Invoice field extraction is
        # a latency-sensitive task, so use low thinking and omit deprecated
        # sampling parameters such as temperature for Gemini 3.8 Flash.
        "generationConfig": {
            "responseMimeType": "application/json",
            "thinkingConfig": {"thinkingLevel": "low"},
            "maxOutputTokens": 512,
        },
    }
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    req = Request(endpoint, data=json.dumps(request_body).encode("utf-8"), headers={
        "Content-Type": "application/json", "x-goog-api-key": key,
    }, method="POST")
    try:
        with urlopen(req, timeout=45) as response:
            response_data = json.loads(response.read())
    except HTTPError as error:
        try:
            provider_error = json.loads(error.read().decode("utf-8")).get("error", {})
        except (UnicodeDecodeError, json.JSONDecodeError, AttributeError):
            provider_error = {}
        provider_status = str(provider_error.get("status") or "unknown")
        provider_message = str(provider_error.get("message") or "No provider message supplied")
        logging.warning("Gemini returned HTTP %s (%s): %s", error.code, provider_status, provider_message)
        if error.code in (401, 403):
            raise ValueError("Gemini rejected the API key or its access. Check that the key is active and the Gemini API is enabled.") from error
        if error.code == 404:
            raise ValueError(f"Gemini model '{model}' was not found. Check GEMINI_MODEL; use an exact model ID such as gemini-3.8-flash.") from error
        if error.code == 400:
            raise ValueError("Gemini rejected this image request. Choose a clear JPG, PNG or WebP photo and check the model setting.") from error
        if error.code == 429:
            raise ValueError("Gemini's request quota is currently unavailable. Check the Gemini API quota and retry later.") from error
        if error.code in (500, 502, 503, 504) or provider_status == "UNAVAILABLE":
            raise ValueError("Gemini is temporarily busy. Wait a moment and retry; the invoice details are still available for manual entry.") from error
        raise ValueError("The image reader is temporarily unavailable. Please try again or enter the details manually.") from error
    except URLError as error:
        reason = error.reason
        logging.warning("Gemini connection failed (%s).", type(reason).__name__)
        if isinstance(reason, socket.gaierror):
            raise ValueError("The app server cannot resolve Google's Gemini address. Check its DNS or internet connection, then retry.") from error
        if isinstance(reason, (TimeoutError, socket.timeout)):
            raise ValueError("The app server timed out connecting to Gemini. Check its outbound internet access, then retry.") from error
        raise ValueError("The app server cannot connect to Google's Gemini service. Check its outbound internet access, then retry.") from error
    except (TimeoutError, socket.timeout) as error:
        logging.warning("Gemini request timed out.")
        raise ValueError("Gemini did not respond in time. Google may be busy; wait a little and retry, or enter the invoice details manually.") from error

    try:
        text = response_data["candidates"][0]["content"]["parts"][0]["text"]
        fields = _json_from_model(text)
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as error:
        raise ValueError("The image reader could not identify invoice fields. Enter them manually.") from error
    allowed = {"carton", "jar", "piece", "bag", "unit", "unknown"}
    unit = str(fields.get("quantity_unit") or "unknown").strip().lower()
    if unit not in allowed:
        unit = "unknown"
    extracted = {
        "product": fields.get("product") if isinstance(fields.get("product"), str) else None,
        "net_amount_paid": fields.get("net_amount_paid") if isinstance(fields.get("net_amount_paid"), str) else None,
        "paid_quantity": fields.get("paid_quantity") if isinstance(fields.get("paid_quantity"), str) else None,
        "quantity_unit": unit,
        "free_cartons": fields.get("free_cartons") if isinstance(fields.get("free_cartons"), str) else None,
        "evidence": fields.get("evidence") if isinstance(fields.get("evidence"), dict) else {},
        "source": "invoice_photo",
    }
    return extracted
