# VyaparVani V1

VyaparVani reads an FMCG invoice or scheme and calculates the GST-inclusive net landing price per carton:

`net amount actually payable ÷ (paid cartons + explicit free cartons)`

The calculation is deterministic Python code. Extraction is kept behind a provider interface so a Gemini or vision provider can be added later. V1 includes typed-text extraction and a manual review flow for uploaded images; it does not pretend to OCR images without a configured provider.

## Run

Requires Python 3.10 or newer and no third-party packages.

```powershell
cd outputs/vyaparvani
python app.py
```

Open <http://127.0.0.1:8000>. Upload a photo or paste invoice text, review the extracted fields, and confirm any unclear quantity units. Uploaded images stay in the browser and are not sent to a service. Typed text is parsed by a conservative local extractor.

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
- `web/` — upload, text entry, editable review fields, states, and calculation breakdown
- `tests/` — ground-truth scenarios derived from the five invoice photos and calculator behavior
- `data/ground_truth.json` — photo-derived values, source notes, and expected validation states
- `AGENTS.md` — repository-wide product and implementation rules
- `.agents/skills/` — focused repo-local skills for UI, extraction, calculation, validation, and testing
- `.agents/skills/landing-price-calculator/references/domain-rules.md` — the agreed V1 business rules and photo notes

## Extraction provider configuration

The configured provider defaults to `manual_text`. `GEMINI_API_KEY` and `GEMINI_MODEL` are future configuration values only; V1 does not call Gemini, and no credentials are embedded in the project. A future provider should implement `ExtractionProvider.extract_text(text)` and/or image extraction, then return the structured schema described in `vyaparvani/extraction.py`. Keep monetary calculation in `calculator.py`.

## Ground truth and limits

The photo fixtures ignore handwritten scheme annotations. Some invoices print `UNT` or `BAG`, not carton, so those cases require the user to confirm what quantity the invoice means before the carton calculation can run. A jar is treated as one sold unit; no pieces-per-jar conversion is used. Multi-product invoices are represented by their printed line-level amounts and quantities, not handwritten interpretations. Refer to the fixture notes before treating an ambiguous unit as ground truth for a carton price.

Included initial tests can be run with `python -m unittest discover -s tests`.
