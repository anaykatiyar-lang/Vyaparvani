# VyaparVani V1

VyaparVani reads an FMCG invoice or scheme and calculates the GST-inclusive net landing price per carton:

`net amount actually payable ÷ (paid cartons + explicit free cartons)`

The calculation is deterministic Python code. Photo text recognition runs in the browser using Tesseract.js; no Mistral or Gemini API key is needed. Recognized text is sent to VyaparVani's own extraction endpoint to prefill fields, then the user reviews them before calculation.

## Run

Requires Python 3.10 or newer and no third-party packages.

```powershell
python app.py
```

Open <http://127.0.0.1:8000>. Use the camera or upload an invoice photo, read it on-device, review the extracted fields, and confirm any unclear quantity units. Camera capture requires browser permission. Tesseract.js and its English language data are loaded from jsDelivr on first use; the invoice image itself stays in the browser. Typed/OCR text is parsed conservatively by the app.

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
- `public/app.js` — on-device Tesseract OCR, editable field review, and calculator UI
- `tests/` — ground-truth scenarios derived from the five invoice photos and calculator behavior
- `data/ground_truth.json` — photo-derived values, source notes, and expected validation states
- `AGENTS.md` — repository-wide product and implementation rules
- `.agents/skills/` — focused repo-local skills for UI, extraction, calculation, validation, and testing
- `.agents/skills/landing-price-calculator/references/domain-rules.md` — the agreed V1 business rules and photo notes

## Photo OCR

The website uses Tesseract.js 7 in a browser worker with English OCR. Its JavaScript, WebAssembly worker, and language data are downloaded when needed and cached by the browser. Photo OCR requires an internet connection the first time those assets are loaded, but it does not require provider credentials and does not upload the invoice image. The recognized text is sent to the app's own `/api/extract` endpoint for conservative field prefill. The user must review all values; Python validation and `calculator.py` remain authoritative for confirmation and arithmetic.

## Deploy to Vercel

This repository includes Vercel Python function entry points and serves the app from `public/`. Import the GitHub repository in Vercel and leave the project root at the repository root (the directory containing this README). No OCR provider credentials are required. Python Functions are currently listed as Beta by Vercel; check the current runtime status before using this deployment for critical business workflows.

The web app uses `/api/extract` for recognized text prefill and `/api/calculate` for validated arithmetic. The photo itself is processed in the browser and is not sent to a backend OCR provider.

## Ground truth and limits

The photo fixtures ignore handwritten scheme annotations. Some invoices print `UNT` or `BAG`, not carton, so those cases require the user to confirm what quantity the invoice means before the carton calculation can run. A jar is treated as one sold unit; no pieces-per-jar conversion is used. Multi-product invoices are represented by their printed line-level amounts and quantities, not handwritten interpretations. Refer to the fixture notes before treating an ambiguous unit as ground truth for a carton price.

Included initial tests can be run with `python -m unittest discover -s tests`.
