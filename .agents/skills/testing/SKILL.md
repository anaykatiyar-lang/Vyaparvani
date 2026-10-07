---
name: testing
description: Add or run focused tests for VyaparVani extraction, validation, and carton landing-price behavior. Use when changing calculation-critical behavior or the invoice review flow.
---

# VyaparVani testing

Test the product behavior the user has agreed to, rather than hypothetical discount features. Keep calculation tests independent of OCR and model output.

## Ground truth

Use `data/ground_truth.json` and [domain-rules.md](../landing-price-calculator/references/domain-rules.md). Preserve handwritten-note exclusions and ambiguous printed units. A test should expect confirmation when the source does not prove a carton unit; do not make a photo case “pass” by assuming the unit.

## Core cases

Cover:

- A clear GST-inclusive amount divided by confirmed paid cartons plus explicit free cartons.
- User-confirmed zero free cartons.
- Missing/invalid payable amount or paid quantity returning no price.
- Missing free-carton confirmation returning no price.
- Ambiguous `UNIT`, `UNT`, `BAG`, `PCS`, or `CA` quantity requiring confirmation.
- Multiple products requiring selection of one product line.
- Jar treated as one sold unit, with no internal piece conversion.
- Lower unit price never creating inferred free cartons.
- Decimal amounts, two-decimal display rounding, and deterministic repeated results.

Keep regression tests in the existing Python `unittest` suite unless the project stack changes. Do not add tests for profit, margin, discount schemes, slabs, or inventory until the product scope is explicitly expanded.

When asked to verify a change, run the smallest relevant suite and report what actually ran. Do not claim tests passed if they were not executed. For changes that affect behavior, add a focused regression case where practical.
