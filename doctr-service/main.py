"""Small CPU docTR OCR service. It recognizes text only; it never calculates prices."""

import base64
import hmac
import os
import re
from functools import lru_cache
from io import BytesIO

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from PIL import Image, UnidentifiedImageError

MAX_IMAGE_BYTES = 3 * 1024 * 1024
TOKEN = os.environ.get("DOCTR_OCR_TOKEN", "").strip()
app = FastAPI(title="VyaparVani docTR OCR", docs_url=None, redoc_url=None)


class OcrRequest(BaseModel):
    image_data_url: str


@lru_cache(maxsize=1)
def get_predictor():
    from doctr.models import ocr_predictor

    return ocr_predictor(det_arch="fast_base", reco_arch="crnn_vgg16_bn", pretrained=True)


@app.get("/health")
def health():
    return {"ok": True, "engine": "docTR"}


@app.post("/ocr")
def ocr(request: OcrRequest, authorization: str | None = Header(default=None)):
    if not TOKEN:
        raise HTTPException(status_code=503, detail="OCR service token is not configured")
    expected = f"Bearer {TOKEN}"
    if not authorization or not hmac.compare_digest(authorization, expected):
        raise HTTPException(status_code=401, detail="Unauthorized")

    match = re.fullmatch(r"data:image/(?:jpeg|png|webp);base64,([A-Za-z0-9+/=\s]+)", request.image_data_url)
    if not match:
        raise HTTPException(status_code=400, detail="Choose a JPG, PNG or WebP invoice photo")
    try:
        raw = base64.b64decode(re.sub(r"\s+", "", match.group(1)), validate=True)
        if not raw or len(raw) > MAX_IMAGE_BYTES:
            raise ValueError("invalid size")
        image = Image.open(BytesIO(raw)).convert("RGB")
        if image.width * image.height > 25_000_000:
            raise ValueError("image dimensions are too large")
    except (ValueError, UnidentifiedImageError, OSError) as error:
        raise HTTPException(status_code=400, detail="The compressed photo is invalid or too large") from error

    try:
        document = get_predictor()([image])
        exported = document.export()
        lines = []
        for page in exported.get("pages", []):
            for block in page.get("blocks", []):
                for line in block.get("lines", []):
                    words = [word.get("value", "").strip() for word in line.get("words", [])]
                    words = [word for word in words if word]
                    if words:
                        lines.append(" ".join(words))
        text = "\n".join(lines).strip()
    except Exception as error:
        raise HTTPException(status_code=503, detail="docTR could not process this photo") from error
    if not text:
        raise HTTPException(status_code=422, detail="No readable text found")
    return {"text": text, "engine": "docTR", "line_count": len(lines)}
