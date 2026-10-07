---
name: scheme-extraction
description: Implement or improve extraction of product, payable amount, quantity, units, and explicit free cartons from VyaparVani invoice photos or text. Use when changing OCR, vision providers, parsing, or the extraction schema.
---

# Scheme extraction

Extraction reports what the source says. It never calculates a landing price or fills gaps with plausible values. The deterministic validator and calculator remain authoritative.

## V1 fields

Extract, when legible:

- Product name and, for a multi-product invoice, the selected product line
- Net amount actually payable for that product, including GST
- Paid quantity and its printed unit
- Free carton quantity only when the source explicitly states it
- Short source evidence and uncertainty for each calculation-relevant value

Keep unknown values null/unknown. Preserve the printed unit such as `UNIT`, `UNT`, `BAG`, or `CA`; do not silently normalize an ambiguous unit to carton. Do not count handwritten scheme annotations in the supplied ground-truth photos.

## Provider boundary

Keep provider-specific OCR/vision calls behind the extraction interface. Provider output is untrusted structured input: validate types, ranges, required fields, and consistency before calculation. Do not put credentials in browser code or commit secrets. If no provider is configured, expose manual text entry and say that uploaded images are only previewed.

Ignore discount arithmetic, profit, margin, selling price, inventory, and ERP concerns. A printed lower net unit price is not evidence of free goods. For a jar, the jar is one sold unit; do not extract an invented internal piece count.

## Reference

Follow [domain-rules.md](../landing-price-calculator/references/domain-rules.md) and the field evidence in `data/ground_truth.json`.
