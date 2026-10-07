# VyaparVani repository instructions

## Product boundary

VyaparVani V1 helps a shopkeeper read an FMCG invoice or scheme and calculate the net landing price per carton. Keep changes focused on that workflow. Profit, margin, selling price, inventory, ERP, bookkeeping, discount-plan engines, and slab schemes are outside V1.

## V1 calculation rules

- Use the GST-inclusive net amount actually payable. Never remove GST or substitute a pre-tax rate.
- Calculate `net amount paid ÷ total cartons received`.
- Total cartons are paid cartons plus free cartons explicitly stated or confirmed by the user.
- Do not infer free cartons from a low unit price, discount, handwriting, or an apparent deal.
- Treat a jar as one sold unit. Do not convert a jar into internal pieces.
- The default result is rupees per carton. Ask the user to confirm a printed quantity when its unit is not clearly cartons.
- Ask for pieces per carton only when the user actually requests a piece-level conversion.
- AI/OCR may extract fields only. Python validation and calculation code determine whether a result can be shown and perform all arithmetic.

## Validation and evidence

Use the existing states `CLEAR`, `CONFIRM`, and `CANNOT CALCULATE`. Ambiguous or missing required data must not produce a price. Preserve source evidence where possible and let the user review extracted fields. Ignore rare handwritten scheme annotations in the current ground-truth photos.

## Project conventions

The current app is Python standard library plus plain HTML, CSS, and JavaScript. Extend its existing structure before proposing a framework or dependency. Keep credentials out of source and browser code; future OCR or vision credentials belong in server-side configuration. Keep examples and tests aligned with `.agents/skills/landing-price-calculator/references/domain-rules.md` and `data/ground_truth.json`.
