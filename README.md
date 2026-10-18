# VyaparVani V1

VyaparVani reads an FMCG invoice or scheme and calculates the GST-inclusive net landing price per carton:

`net amount actually payable ÷ (paid cartons + explicit free cartons)`

The calculation is deterministic Python code. Invoice photos are sent to a separately hosted Mindee docTR OCR service only after the user presses the photo-reading button. docTR returns recognized text; the app pre-fills only fields it can identify from explicit key/value text and shows the OCR text for review. The user confirms the values, and Python validation and calculation code remain authoritative.

## Run

Requires Python 3.10 or newer and no third-party packages.

```powershell
python app.py
```

Open <http://127.0.0.1:8000>. Use the camera or upload an invoice photo, choose **Read photo with docTR OCR**, review the recognized text and fields, and confirm any unclear quantity units. Camera capture requires browser permission.

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
- `doctr-service/` — separate CPU docTR OCR service, packaged as a Docker container
- `tests/` — ground-truth scenarios derived from the five invoice photos and calculator behavior
- `data/ground_truth.json` — photo-derived values, source notes, and expected validation states
- `AGENTS.md` — repository-wide product and implementation rules
- `.agents/skills/` — focused repo-local skills for UI, extraction, calculation, validation, and testing
- `.agents/skills/landing-price-calculator/references/domain-rules.md` — the agreed V1 business rules and photo notes

## docTR photo reading

The OCR service uses the open-source [Mindee docTR](https://github.com/mindee/doctr) project with its PyTorch CPU backend. It is a separate container because model dependencies, weights and inference do not suit a small serverless request handler's memory and cold-start profile. Create a long random shared token for both services (for example, `python -c "import secrets; print(secrets.token_urlsafe(32))"`).

```dotenv
DOCTR_OCR_URL=https://your-ocr-service.example.com
DOCTR_OCR_TOKEN=your-long-random-shared-token
```

For local development, put these values in the gitignored `.env.local` at the repository root and restart `python app.py`. The token is sent only between the Vercel/local server and the OCR service; it is never exposed to the browser.

### Deploy the OCR service

1. Deploy the `doctr-service/` directory as a Docker web service on a container host with at least 2 GB RAM and outbound access to download docTR model weights on first start. Render, Railway, Fly.io, or a similar Docker host can run this service; it is not deployed as part of Vercel.
2. Set `DOCTR_OCR_TOKEN` on the OCR service to a long random secret. Keep the service HTTPS-only and do not expose its token in client code.
3. Wait for `https://your-ocr-service.example.com/health` to return `{"ok":true,"engine":"docTR"}` after its first model initialization. The service loads model weights on first OCR request.
4. In Vercel **Settings → Environment Variables**, set `DOCTR_OCR_URL` to the service base URL and `DOCTR_OCR_TOKEN` to the same secret. Select the deployment environments and redeploy. Vercel does not read `.env.local` from GitHub.

The browser resizes the image before it is sent to the app server, which forwards it to docTR. docTR recognizes text but does not identify handwriting versus print or interpret invoice meaning. As a result, handwritten text may appear in the OCR text; check every value against the photo. The current conservative parser pre-fills explicit key/value text only and leaves other fields for user review. It never infers free goods or calculates a price from OCR; Python validation and `calculator.py` handle the final decision and arithmetic.

## Deploy to Vercel

This repository includes Vercel Python function entry points and serves the app from `public/`. Import the GitHub repository in Vercel and leave the project root at the repository root (the directory containing this README). Deploy the separate docTR Docker service and configure `DOCTR_OCR_URL` and `DOCTR_OCR_TOKEN` in Vercel before enabling photo reading.

The web app uses `/api/config`, `/api/extract`, `/api/extract-image`, and `/api/calculate`. The image endpoint calls the authenticated docTR service server-side; its token is never exposed to the browser. The calculator remains local Python logic in both Vercel and local deployments.

## Ground truth and limits

The photo fixtures ignore handwritten scheme annotations. Some invoices print `UNT` or `BAG`, not carton, so those cases require the user to confirm what quantity the invoice means before the carton calculation can run. A jar is treated as one sold unit; no pieces-per-jar conversion is used. Multi-product invoices are represented by their printed line-level amounts and quantities, not handwritten interpretations. Refer to the fixture notes before treating an ambiguous unit as ground truth for a carton price.

Included initial tests can be run with `python -m unittest discover -s tests`.
