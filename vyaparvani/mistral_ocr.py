"""Mistral Document AI OCR provider. Provider extracts; calculator owns decisions and arithmetic."""

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

PROMPT = """Extract printed facts from this FMCG purchase invoice. Ignore handwriting, handwritten scheme notes, and discounts as evidence of free goods. Return only a JSON object with keys product, net_amount_paid, paid_quantity, quantity_unit, free_cartons, evidence. Use strings for clearly printed values, and null for missing, unreadable, or ambiguous values. Never calculate a landing price. net_amount_paid must be the GST-inclusive amount actually payable and only when clearly attributable to a single product; never use a multi-product invoice total for one product. paid_quantity must be the printed paid quantity. quantity_unit must be one of carton, jar, piece, bag, unit, unknown; use carton only if cartons/cases are explicitly printed. free_cartons must be non-null only when the printed source explicitly states free cartons. If multiple product lines cannot be safely distinguished, set product, net_amount_paid, paid_quantity, and quantity_unit to null. evidence should map extracted field names to short quotes from printed text only. JSON shape: {\"product\": string|null, \"net_amount_paid\": string|null, \"paid_quantity\": string|null, \"quantity_unit\": string|null, \"free_cartons\": string|null, \"evidence\": object}."""


def _read_data_url(payload):
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
    canonical_data = base64.b64encode(image_bytes).decode("ascii")
    return mime_type, f"data:{mime_type};base64,{canonical_data}"


def extract_invoice_image_with_mistral(payload):
    mime_type, image_data_url = _read_data_url(payload)
    model = os.environ.get("MISTRAL_OCR_MODEL", "mistral-ocr-latest").strip()
    api_key = os.environ["MISTRAL_API_KEY"]
    request_body = {
        "model": model,
        "document": {"type": "image_url", "image_url": image_data_url},
        "document_annotation_prompt": PROMPT,
        "document_annotation_format": {"type": "json_object"},
        "include_blocks": True,
        "confidence_scores_granularity": "block",
    }
    request = Request(
        "https://api.mistral.ai/v1/ocr",
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
            detail = provider_error.get("detail") or provider_error.get("message") or ""
        except (UnicodeDecodeError, json.JSONDecodeError):
            detail = ""
        logging.warning("Mistral OCR returned HTTP %s: %s", error.code, str(detail)[:300])
        if error.code in (401, 403):
            raise ValueError("Mistral rejected the API key or its access. Check the key in server settings.") from error
        if error.code == 429:
            raise ValueError("Mistral OCR usage is currently limited. Check your Mistral usage limits and retry later.") from error
        if error.code in (400, 413, 415):
            raise ValueError("Mistral could not process this image. Choose a clear JPG, PNG or WebP photo and retry.") from error
        if error.code >= 500:
            raise ValueError("Mistral OCR is temporarily unavailable. Wait a moment and retry, or enter the details manually.") from error
        raise ValueError("Mistral could not read this invoice. Please try again or enter the details manually.") from error
    except URLError as error:
        reason = error.reason
        logging.warning("Mistral OCR connection failed (%s).", type(reason).__name__)
        if isinstance(reason, (TimeoutError, socket.timeout)):
            raise ValueError("Mistral OCR did not respond in time. Check the server connection, then retry.") from error
        raise ValueError("The app server cannot connect to Mistral OCR. Check its outbound internet access, then retry.") from error
    except (TimeoutError, socket.timeout) as error:
        logging.warning("Mistral OCR request timed out.")
        raise ValueError("Mistral OCR did not respond in time. Wait a moment and retry, or enter the details manually.") from error

    annotation = response_data.get("document_annotation")
    if isinstance(annotation, str):
        try:
            fields = json.loads(annotation)
        except json.JSONDecodeError as error:
            raise ValueError("Mistral OCR could not structure the invoice fields. Enter them manually.") from error
    elif isinstance(annotation, dict):
        fields = annotation
    else:
        raise ValueError("Mistral OCR did not return structured invoice fields. Enter them manually.")

    allowed_units = {"carton", "jar", "piece", "bag", "unit", "unknown"}
    unit = str(fields.get("quantity_unit") or "unknown").strip().lower()
    if unit not in allowed_units:
        unit = "unknown"
    return {
        "product": fields.get("product") if isinstance(fields.get("product"), str) else None,
        "net_amount_paid": fields.get("net_amount_paid") if isinstance(fields.get("net_amount_paid"), str) else None,
        "paid_quantity": fields.get("paid_quantity") if isinstance(fields.get("paid_quantity"), str) else None,
        "quantity_unit": unit,
        "free_cartons": fields.get("free_cartons") if isinstance(fields.get("free_cartons"), str) else None,
        "evidence": fields.get("evidence") if isinstance(fields.get("evidence"), dict) else {},
        "source": "invoice_photo",
        "ocr_provider": "mistral",
    }
