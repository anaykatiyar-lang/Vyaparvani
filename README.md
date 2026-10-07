# VyaparVani V1

VyaparVani reads an FMCG invoice or scheme and calculates the GST-inclusive net landing price per carton:

`net amount actually payable ÷ (paid cartons + explicit free cartons)`

The calculation is deterministic Python code. Invoice photos are sent to Groq's Qwen 3.8 27B vision model only after the user presses the photo-reading button. The model extracts fields; the user reviews them, and Python validation and calculation code remain authoritative.

## Run

Requires Python 3.10 or newer and no third-party packages.

```powershell
python app.py
```

Open <http://127.0.0.1:8000>. Use the camera or upload an invoice photo, choose **Read photo with Groq Qwen Vision**, review the extracted fields, and confirm any unclear quantity units. Camera capture requires browser permission.

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
- `public/app.js` — photo upload, Groq request, editable field review, and calculator UI
- `vyaparvani/groq_vision.py` — server-side Groq image extraction and response validation
- `tests/` — ground-truth scenarios derived from the five invoice photos and calculator behavior
- `data/ground_truth.json` — photo-derived values, source notes, and expected validation states
- `AGENTS.md` — repository-wide product and implementation rules
- `.agents/skills/` — focused repo-local skills for UI, extraction, calculation, validation, and testing
- `.agents/skills/landing-price-calculator/references/domain-rules.md` — the agreed V1 business rules and photo notes

## Groq photo reading

The default vision model is `qwen/qwen3.8-27b`. For local development, add the key to the gitignored `.env.local` file at the repository root:

```dotenv
GROQ_API_KEY=your_groq_api_key
# Optional; defaults to qwen/qwen3.8-27b
GROQ_VISION_MODEL=qwen/qwen3.8-27b
```

Restart `python app.py` after changing `.env.local`. Never commit the key or put it in browser code.

For Vercel, open the project’s **Settings → Environment Variables** and add `GROQ_API_KEY` with the key from the Groq Console. Add `GROQ_VISION_MODEL` only if you want to override the default. Select the deployment environments you use, save, then redeploy. Vercel does not read `.env.local` from GitHub.

The browser resizes the image before it is sent to the app server, and the server sends it to Groq for field extraction. Groq usage limits apply. The model must never infer free goods from a discount or calculate the landing price; Python validation and `calculator.py` handle the final decision and arithmetic.

## Deploy to Vercel

This repository includes Vercel Python function entry points and serves the app from `public/`. Import the GitHub repository in Vercel and leave the project root at the repository root (the directory containing this README). Configure `GROQ_API_KEY` in Vercel before enabling photo reading. Python Functions are currently listed as Beta by Vercel; check the current runtime status before using this deployment for critical business workflows.

The web app uses `/api/config`, `/api/extract`, `/api/extract-image`, and `/api/calculate`. The image endpoint calls Groq server-side; the secret key is never exposed to the browser.

## Ground truth and limits

The photo fixtures ignore handwritten scheme annotations. Some invoices print `UNT` or `BAG`, not carton, so those cases require the user to confirm what quantity the invoice means before the carton calculation can run. A jar is treated as one sold unit; no pieces-per-jar conversion is used. Multi-product invoices are represented by their printed line-level amounts and quantities, not handwritten interpretations. Refer to the fixture notes before treating an ambiguous unit as ground truth for a carton price.

Included initial tests can be run with `python -m unittest discover -s tests`.
