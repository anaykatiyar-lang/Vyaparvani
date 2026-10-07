# VyaparVani V1 domain rules

These rules reflect the user's confirmed scope. Treat photo values as evidence, and preserve unresolved units as unresolved.

## Price and quantity

- Landing price uses the actual net amount paid, with GST included.
- Divide that amount by the total cartons received.
- Total cartons = paid cartons + free cartons explicitly printed or confirmed by the user.
- If free cartons are not stated, ask the user to confirm zero. Never infer free goods from discount, a low unit rate, or handwritten notes.
- The default answer is ₹ per carton. A jar is one sold unit; no pieces inside a jar are counted.
- Ask for pieces per carton only if a piece-level conversion is actually requested.
- If the invoice unit is not clearly carton, ask what it means before calculating per carton.

## Extraction and validation

- AI/OCR extracts fields only; application code validates and calculates.
- A multi-product invoice needs a selected product line and its line-level payable amount and quantity.
- The supplied photos' handwritten scheme annotations are rare and excluded from V1 ground truth.
- `CLEAR` means all required values and carton units are reviewed and valid.
- `CONFIRM` means a user can resolve a meaningful uncertainty.
- `CANNOT CALCULATE` means a required value is absent or invalid and no safe calculation is available.

## Photo-derived examples

See `data/ground_truth.json` for five cases. The Flipkart Wholesale Parle lines show ₹6,600 for 12 printed UNITs, ₹7,020 for 13 printed UNITs, and ₹3,277.74 for 6 printed UNITs. The printed product lines are jars, treated as single sold units, but the invoice's UNIT label does not establish that each is a carton; those cases stay `CONFIRM` for a carton result. The Ashok Agency Tiranga line shows 5 BAG and a ₹2,900 GST-inclusive grand total, so it also needs unit confirmation. The Ajeet Trading photos show multiple products; select a line before calculating.

These examples must not be rewritten as clear carton calculations without user confirmation. Handwritten notes and handwritten quantities are excluded.
