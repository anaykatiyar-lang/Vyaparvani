---
name: validation-and-warnings
description: Implement VyaparVani validation, user confirmations, or warnings for missing, ambiguous, invalid, or conflicting invoice fields. Use when changing whether a carton landing price may be shown.
---

# Validation and warnings

Validation decides whether reviewed extraction values are safe to calculate. A confidence score or plausible-looking result does not replace business validation.

## States

- `CLEAR`: product, GST-inclusive net amount payable, positive paid carton count, confirmed carton unit, and free-carton count (including user-confirmed zero) are valid. The calculator may return a price.
- `CONFIRM`: an actionable user answer can resolve uncertainty, such as whether `UNIT` means carton or whether a multi-product line was selected. Do not show a price while waiting.
- `CANNOT CALCULATE`: required values are absent/invalid, quantities are unusable, or the source is too unclear to ask a specific resolving question. Return no price.

Use the exact state names supported by the current app, including the spaced label `CANNOT CALCULATE` in user-facing output.

## V1 checks

Check product selection, amount actually payable, paid quantity, quantity unit, explicit/confirmed free-carton quantity, positivity, whole-carton counts, and consistency between fields. The amount must include GST. Do not validate or compute a separate discount scheme in V1.

Treat `UNIT`, `UNT`, `BAG`, `PCS`, and `CA` as ambiguous unless the source or user confirms they mean cartons. If multiple products appear, require the chosen product line and use that line's amount and quantity; do not divide the whole invoice total by one line's quantity.

If free quantity is unstated, ask the user to confirm zero. Do not infer free goods from lower prices or handwritten notes. Do not count internal pieces in a jar.

## Warning copy

Keep each question short and tied to a field. Examples:

- “The invoice says 12 UNIT. Does that mean 12 cartons?”
- “No free-carton count is printed. Confirm 0 free cartons?”
- “This invoice has several products. Which line should I calculate?”
- “I could not read the amount actually payable. Please enter it from the invoice.”

After confirmation, update the structured field, run validation again, and calculate only if the new state is `CLEAR`.

## Reference

Use [domain-rules.md](../landing-price-calculator/references/domain-rules.md) for V1 rules and photo cases.
