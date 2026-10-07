# VyaparVani V1

VyaparVani reads an FMCG invoice or scheme and calculates the GST-inclusive net landing price per carton:

`net amount actually payable ÷ (paid cartons + explicit free cartons)`

The calculation is deterministic Python code. Typed text uses a conservative local extractor. Photo extraction is optional and uses a server-side Gemini key when configured; otherwise photos stay as local previews and the user enters the details manually.

## Run

Requires Python 3.10 or newer and no third-party packages.

```powershell
python app.py
```

Open <http://127.0.0.1:8000>. Use the camera or upload an invoice photo, review the extracted fields, and confirm any unclear quantity units. Camera capture requires browser permission. If `GEMINI_API_KEY` is configured on the server, the user can choose to send the photo to Gemini for field extraction; otherwise the photo remains a local preview and the user enters the printed values manually. Typed text is parsed by a conservative local extractor.

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

The configured provider defaults to `manual_text`. For local development, put `GEMINI_API_KEY=...` in `.env.local` at the repository root. The local `app.py` reads that gitignored file when the server starts. Do not commit `.env.local` or place the key in a GitHub file. For a Vercel deployment, add `GEMINI_API_KEY` as a Vercel project environment variable; serverless functions do not load `.env.local`. You can alternatively set the key in PowerShell before starting the app:

```powershell
$env:GEMINI_API_KEY = "your-key-from-google-ai-studio"
$env:GEMINI_MODEL = "gemini-3.8-flash" # optional
python app.py
```

The key is read only by the server and must never be placed in browser code or committed. On Vercel, add `GEMINI_API_KEY` and optionally `GEMINI_MODEL` in the project's environment-variable settings. The user chooses **Read photo with Gemini** before the invoice image is transmitted. Gemini returns structured fields and source evidence; Python validation and `calculator.py` remain authoritative for confirmation and arithmetic. With no key, image previews and typed/manual entry remain available.

## Deploy to Vercel

This repository includes Vercel Python function entry points and serves the app from `public/`. Import the GitHub repository in Vercel and leave the project root at the repository root (the directory containing this README). No provider credentials are required for manual V1 use. Python Functions are currently listed as Beta by Vercel; check the current runtime status before using this deployment for critical business workflows.

The API endpoints are `/api/config`, `/api/extract`, `/api/extract-image`, and `/api/calculate`. They use the same shared validation and extraction logic as the local server.

## Ground truth and limits

The photo fixtures ignore handwritten scheme annotations. Some invoices print `UNT` or `BAG`, not carton, so those cases require the user to confirm what quantity the invoice means before the carton calculation can run. A jar is treated as one sold unit; no pieces-per-jar conversion is used. Multi-product invoices are represented by their printed line-level amounts and quantities, not handwritten interpretations. Refer to the fixture notes before treating an ambiguous unit as ground truth for a carton price.

Included initial tests can be run with `python -m unittest discover -s tests`.
