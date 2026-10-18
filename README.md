# VyaparVani V1

VyaparVani reads an FMCG invoice or scheme and calculates the GST-inclusive net landing price per carton:

`net amount actually payable ÷ (paid cartons + explicit free cartons)`

The calculation is deterministic Python code. Invoice photos are sent to Google Cloud Vision for text recognition only after the user presses the photo-reading button. The app pre-fills only fields it can identify from explicit key/value text and shows the OCR text for review. The user confirms the values, and Python validation and calculation code remain authoritative.

## Run

Requires Python 3.10 or newer and no third-party packages.

```powershell
python app.py
```

Open <http://127.0.0.1:8000>. Use the camera or upload an invoice photo, choose **Read photo with Google Cloud Vision**, review the recognized text and fields, and confirm any unclear quantity units. Camera capture requires browser permission.

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
- `public/app.js` — photo upload, OCR request, editable field review, and calculator UI
- `vyaparvani/http_api.py` — server-side Google Cloud Vision OCR request and shared API logic
- `tests/` — ground-truth scenarios derived from the five invoice photos and calculator behavior
- `data/ground_truth.json` — photo-derived values, source notes, and expected validation states
- `AGENTS.md` — repository-wide product and implementation rules
- `.agents/skills/` — focused repo-local skills for UI, extraction, calculation, validation, and testing
- `.agents/skills/landing-price-calculator/references/domain-rules.md` — the agreed V1 business rules and photo notes

## Google Cloud Vision photo reading

Enable the **Cloud Vision API** in your Google Cloud project. Create an API key restricted to the Cloud Vision API. The app sends the key in the `x-goog-api-key` request header from the server; it is never put in browser code. Google charges per image after the first 1,000 monthly Vision API units, so check usage and set quota limits in Google Cloud.

```dotenv
GOOGLE_VISION_API_KEY=your_google_cloud_vision_api_key
```

For local development, put the key in the gitignored `.env.local` at the repository root and restart `python app.py`. In Vercel, add `GOOGLE_VISION_API_KEY` under **Settings → Environment Variables**, select your deployment environments, and redeploy. Google Cloud Vision recognizes handwriting as well as printed text; check each extracted value against the photo. The current parser pre-fills explicit key/value text only and leaves other fields for review. It never infers free goods or calculates a price from OCR; Python validation and `calculator.py` handle the final decision and arithmetic.

## Deploy to Vercel

This repository includes Vercel Python function entry points and serves the app from `public/`. Import the GitHub repository in Vercel and leave the project root at the repository root (the directory containing this README). Configure `GOOGLE_VISION_API_KEY` in Vercel before enabling photo reading.

The web app uses `/api/config`, `/api/extract`, `/api/extract-image`, and `/api/calculate`. The image endpoint calls Google Cloud Vision server-side; the API key is never exposed to the browser. The calculator remains local Python logic in both Vercel and local deployments.

## Ground truth and limits

The photo fixtures ignore handwritten scheme annotations. Some invoices print `UNT` or `BAG`, not carton, so those cases require the user to confirm what quantity the invoice means before the carton calculation can run. A jar is treated as one sold unit; no pieces-per-jar conversion is used. Multi-product invoices are represented by their printed line-level amounts and quantities, not handwritten interpretations. Refer to the fixture notes before treating an ambiguous unit as ground truth for a carton price.

Included initial tests can be run with `python -m unittest discover -s tests`.
