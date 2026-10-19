# VyaparVani

VyaparVani is an assistant for local FMCG distributors and shopkeepers in India. It is being built to make everyday order and invoice work easier when conversations mix Hindi, English product names, and familiar units such as cartons and peti.

The project currently includes a web-based net landing price calculator. The longer-term direction is a voice-first assistant that can understand spoken orders, turn them into structured order lines, and support the distributor's existing pricing workflow.

## Why this project exists

Many FMCG orders are placed over phone calls in fast, noisy, code-switched speech: “Parle-G ke paanch carton” or “Maggi do peti.” Brand names, quantities, and units all matter. A transcript that sounds plausible but changes a product or quantity can produce an incorrect order.

VyaparVani aims to handle this workflow carefully: extract what was said, let a person review uncertain details, and keep business calculations deterministic and reviewable.

## Project status

| Capability | Status |
|---|---|
| Net landing price calculator | Implemented in the web app |
| Invoice photo text recognition | Implemented through Google Cloud Vision; user reviews extracted fields |
| Hindi/Hinglish call transcription | Early pipeline confirmed; model fine-tuning is planned |
| Structured voice orders | Planned |
| Fine-tuned Whisper model and hosted inference API | Planned |

The current repository does **not** yet contain the fine-tuned speech model, its training pipeline, or the planned order-extraction LLM. The speech work is a proposed next phase, not a feature currently available in the deployed calculator.

## Planned voice-order workflow

1. Transcribe Hindi and Hinglish distributor calls, including English FMCG brand names and spoken quantities.
2. Compare a larger fine-tuned Whisper model against a base model using calls excluded from training.
3. Measure both word error rate (WER) and order-line accuracy: whether the product and quantity were captured correctly.
4. Pass the reviewed transcript to a small language model that converts it into structured order lines.
5. Present the extracted order for human review before it is used.

The early transcription pipeline has been confirmed with a small Whisper model on a 12 GB laptop. That provides a working baseline, but not enough memory to fine-tune a larger model locally. The planned training and inference environment is a single AMD Instinct MI300X GPU with 192 GB of HBM3 memory. The MI300X's memory specification is documented by [AMD](https://www.amd.com/en/products/accelerators/instinct/mi300/mi300x.html).

The intended experiment is to fine-tune a larger Whisper model on Hindi call audio paired with Hinglish transcripts, then compare it with the base model on unseen calls. The same GPU is planned to host a transcription API and a small LLM for converting transcripts into structured orders. GPU usage is intended to stay within roughly 50 hours; compute will be stopped and the instance destroyed between sessions.

## Current calculator

The current web app calculates GST-inclusive net landing price per carton:

```text
net amount actually payable ÷ (paid cartons + explicitly confirmed free cartons)
```

The arithmetic is deterministic Python code. OCR can suggest values, but the user reviews the evidence and Python validation and calculation code remain authoritative. The calculator does not infer free goods from a discount or low unit price, and it does not convert the pieces inside a jar into cartons.

### Run locally

Requires Python 3.10 or newer. The app uses Python's standard library and has no third-party Python dependencies for the calculator itself.

```powershell
python app.py
```

Open <http://127.0.0.1:8000>. To use invoice photo reading, configure a Google Cloud Vision API key as described below. Camera capture requires browser permission.

Example input:

```text
Product: Parle Big Kaccha Mango Bite Jar 3.485 kg
Net amount paid: 6600
Paid quantity: 12 cartons
Free cartons: 0
```

The result is ₹550.00 per carton.

## Invoice photo reading setup

Invoice image text recognition currently uses Google Cloud Vision. Create a standard API key in Google Cloud, enable the Cloud Vision API in the same project, and restrict the key to that API. Keep the key on the server; it must not be placed in browser code or committed to Git.

For local development, put this in the gitignored `.env.local` file at the repository root:

```dotenv
GOOGLE_VISION_API_KEY=your_google_cloud_vision_api_key
```

For Vercel, add `GOOGLE_VISION_API_KEY` under **Project Settings → Environment Variables**, then redeploy. Google Cloud Vision recognizes handwriting as well as printed text, so check extracted values against the invoice image. The current parser pre-fills only values it can identify from explicit key/value text and leaves the rest for review.

## Deploy to Vercel

The repository includes Vercel Python function entry points and serves the interface from `public/`. Import the repository into Vercel with the project root set to the directory containing this README. Add `GOOGLE_VISION_API_KEY` in Vercel before using invoice photo reading.

The web app uses `/api/config`, `/api/extract`, `/api/extract-image`, and `/api/calculate`. The image endpoint calls Google Cloud Vision server-side. Calculator arithmetic remains local Python logic.

## Repository map

- `app.py` — local web server and API routes
- `vyaparvani/calculator.py` — input validation and net landing price calculation
- `vyaparvani/extraction.py` — conservative extraction of typed or OCR text
- `vyaparvani/http_api.py` — shared API logic, including server-side Vision requests
- `public/` — responsive calculator interface, photo upload, review, and results
- `api/` — Vercel Python function entry points
- `tests/` — calculator behavior tests
- `data/ground_truth.json` — invoice fixture values and review notes

## Calculation and review rules

- Use the GST-inclusive net amount actually payable.
- Divide by paid cartons plus free cartons explicitly shown or confirmed by the user.
- Do not infer free goods from handwriting, discounts, or unusually low prices.
- Treat a jar as one sold unit; do not infer its internal piece count.
- Ask the user to confirm quantities when the printed unit is not clearly cartons.
- OCR and future speech models may extract facts, but must not perform the calculator's arithmetic.

## Evaluation and responsible use

For the planned speech work, compare the base and fine-tuned models on calls not used in training. Report WER alongside order-line accuracy for product and quantity; WER alone can miss errors that change an order. Keep the test split at the call level so parts of one conversation do not leak across training and evaluation. Establish target metrics after measuring the baseline rather than assuming a result in advance.

Only use call audio and transcripts that are authorized for this work. Remove or protect personal information, and do not include private recordings or credentials in the repository. Treat machine-generated transcripts and order lines as drafts for human review.

Run the current calculator tests with:

```powershell
python -m unittest discover -s tests
```
