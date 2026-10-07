---
name: vyaparvani-ui
description: Build or change VyaparVani screens and interactions for invoice entry, field review, validation states, and carton landing-price results. Use when working on its web interface or responsive presentation.
---

# VyaparVani UI

Make the existing interface fast to use, readable on a phone, and clear about what is confirmed. Follow the current plain HTML/CSS/JavaScript app unless the user explicitly asks to change its stack.

## Main flow

Support this sequence:

1. Upload a photo or enter/paste invoice text.
2. Show extracted or entered product, net amount payable, paid quantity and unit, and explicit free-carton quantity.
3. Let the user correct fields and resolve ambiguities.
4. Show a carton landing price only when validation is `CLEAR`.
5. Show the amount, paid cartons, explicit free cartons, total cartons, and division used.

The amount is GST-inclusive. Make that visible beside the amount field. Do not show profit, margins, selling prices, inventory, or accounting features.

## Interaction rules

- Make photo upload, typed text, and manual field correction easy to find.
- Be honest about provider capability: photo preview is not OCR. If no image extraction provider is configured, say that the user must enter or paste the printed details.
- Make `CONFIRM` explain the precise question, such as whether a printed `UNIT` count means cartons.
- Make `CANNOT CALCULATE` identify the missing or invalid value.
- Do not display a calculated price in either non-clear state.
- Keep warnings short and actionable; do not add voice controls or language switching unless separately requested.
- Treat a jar as one sold unit. Do not ask for pieces-per-jar for the default carton result.

## Visual and accessibility guidance

Prioritize the input, review fields, validation message, and final price. Use readable type, clear labels, visible focus, semantic controls, and layouts that work on narrow screens. Avoid decorative dashboards and motion that delays the task. Respect reduced-motion preferences.

## Reference

Use [domain-rules.md](../landing-price-calculator/references/domain-rules.md) for agreed product behavior. Keep UI copy consistent with the actual implemented provider and states.
