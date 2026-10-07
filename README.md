# VyaparVani V1

VyaparVani reads an FMCG invoice or scheme and calculates the GST-inclusive net landing price per carton:

`net amount actually payable ÷ (paid cartons + explicit free cartons)`

The calculation is deterministic Python code. Typed text uses a conservative local extractor. Photo extraction is optional and uses a server-side Gemini key when configured; otherwise photos stay as local previews and the user enters the details manually.

## Run

Requires Python 3.10 or newer and no third-party packages.

```powershell
python app.py
```

Open <http://127.0.0.1:8000>. Use the camera or upload an invoice photo, review the extracted fields, and confirm any unclear quantity units. Camera capture requires browser permission. Configure `MISTRAL_API_KEY` or `GEMINI_API_KEY` on the server to enable photo reading. Mistral OCR is preferred when both keys are present; set `IMAGE_READER_PROVIDER` to `mistral` or `gemini` to choose explicitly. Without a configured provider, photos remain local previews and the user enters printed values manually. Typed text is parsed by a conservative local extractor.

## Example typed input

```text
Product: Parle Big Kaccha Mango Bite Jar 3.485 kg
Net amount paid: 6600
Paid quantity: 12 cartons
Free cartons: 0
```

The app shows ₹550.00/carton. It never removes GST, adds internal pieces to a jar, or infers free goods from a discount or low unit price.

## Project map

- `app.py` — local web server and extraction API
- `vyaparvani/calculator.py` — validation and deterministic calculation
- `vyaparvani/extraction.py` — provider protocol and text extraction implementation
- `public/` — responsive camera/upload flow, text entry, editable review fields, states, and calculation breakdown
- `api/` — Vercel Python function entry points
- `vyaparvani/http_api.py` — shared API logic used locally and on Vercel
- `vyaparvani/vision.py` — optional Gemini image-to-fields provider
- `tests/` — ground-truth scenarios derived from the five invoice photos and calculator behavior
- `data/ground_truth.json` — photo-derived values, source notes, and expected validation states
- `AGENTS.md` — repository-wide product and implementation rules
- `.agents/skills/` — focused repo-local skills for UI, extraction, calculation, validation, and testing
- `.agents/skills/landing-price-calculator/references/domain-rules.md` — the agreed V1 business rules and photo notes

## Extraction provider configuration

For local development, put provider keys in the gitignored `.env.local` at the repository root. The local `app.py` reads it when the server starts. Do not commit the file or place keys in browser code. To use Mistral OCR, add `MISTRAL_API_KEY=...`; the default OCR model is `mistral-ocr-latest`. Optional settings are `IMAGE_READER_PROVIDER=mistral` and `MISTRAL_OCR_MODEL=mistral-ocr-latest`. Gemini remains available with `GEMINI_API_KEY` and optional `GEMINI_MODEL`. For Vercel, add the selected keys and optional provider/model settings as project environment variables; serverless functions do not load `.env.local`.

```powershell
$env:MISTRAL_API_KEY = "your-key-from-mistral"
$env:IMAGE_READER_PROVIDER = "mistral" # optional; Mistral is preferred automatically when its key is present
$env:MISTRAL_OCR_MODEL = "mistral-ocr-latest" # optional
python app.py
```

Provider keys are read only by the server and must never be placed in browser code or committed. On Vercel, add the selected provider key and optional provider/model settings in the project's environment variables. The user chooses **Read photo** before the image is sent to Mistral OCR or Gemini for field extraction. The selected provider returns fields for user review; Python validation and `calculator.py` remain authoritative for confirmation and all arithmetic. With no configured key, image previews and typed/manual entry remain available.

## Deploy to Vercel

This repository includes Vercel Python function entry points and serves the app from `public/`. Import the GitHub repository in Vercel and leave the project root at the repository root (the directory containing this README). No provider credentials are required for manual V1 use. Python Functions are currently listed as Beta by Vercel; check the current runtime status before using this deployment for critical business workflows.

The API endpoints are `/api/config`, `/api/extract`, `/api/extract-image`, and `/api/calculate`. They use the same shared validation and extraction logic as the local server.

## Ground truth and limits

The photo fixtures ignore handwritten scheme annotations. Some invoices print `UNT` or `BAG`, not carton, so those cases require the user to confirm what quantity the invoice means before the carton calculation can run. A jar is treated as one sold unit; no pieces-per-jar conversion is used. Multi-product invoices are represented by their printed line-level amounts and quantities, not handwritten interpretations. Refer to the fixture notes before treating an ambiguous unit as ground truth for a carton price.

Included initial tests can be run with `python -m unittest discover -s tests`.
