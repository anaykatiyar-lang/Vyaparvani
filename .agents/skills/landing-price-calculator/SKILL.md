---
name: landing-price-calculator
description: Implement or review VyaparVani's deterministic GST-inclusive landing-price calculation per carton. Use when changing calculation, amount precision, quantity handling, breakdowns, or calculation tests.
---

# Landing price calculator

Keep the calculator deterministic and separate from OCR/AI. It accepts reviewed values, validates them, and performs arithmetic with decimal-safe money handling.

## V1 formula

```text
total cartons received = paid cartons + explicitly stated/confirmed free cartons
landing price per carton = GST-inclusive net amount actually payable / total cartons received
```

Use the actual amount payable, including GST. Never back out GST, recalculate tax, or substitute taxable value or unit rate. Never infer free cartons from a discount or a low price. If no free quantity is printed, require the user to confirm `0` before using it.

Only calculate per carton when the paid and free quantity units are confirmed as cartons. Do not assume `UNIT`, `UNT`, `BAG`, `PCS`, or `CA` means carton without evidence or confirmation. A jar is one sold unit; do not expand it into pieces. Piece-level conversion is out of the default flow and should only be added when requested and supported by confirmed conversion data.

## Implementation

- Keep financial arithmetic in the existing Python calculator module.
- Use `Decimal` (or an equivalent exact decimal representation in an explicitly approved future stack) for money and round the displayed result to two decimal places using the existing rounding rule.
- Reject non-positive payable amounts, non-positive paid quantities, negative free quantities, non-integer carton counts, and non-finite numbers.
- Return no price unless the validation state is `CLEAR`.
- Include an audit breakdown of payable amount, paid cartons, free cartons, total received cartons, and division.
- Do not add percentage/fixed discount engines, slabs, selling price, margin, profit, inventory, or ERP logic to V1.

## Reference

Read [domain-rules.md](references/domain-rules.md) before changing business behavior. Use `data/ground_truth.json` as photo-derived regression evidence; preserve its confirmation cases rather than forcing an unverified carton interpretation.
