"""Extraction boundary. Providers return facts; calculator.py owns all arithmetic."""

import re
from typing import Protocol


class ExtractionProvider(Protocol):
    def extract_text(self, text: str) -> dict: ...


class ManualTextProvider:
    """Conservative key/value parser for pasted text; it never computes prices."""
    patterns = {
        "product": r"(?:product|item)\s*[:=-]\s*(.+)",
        "net_amount_paid": r"(?:net amount paid|amount payable|grand total|total payable)\s*[:=-]\s*(?:₹\s*)?([\d,]+(?:\.\d{1,2})?)",
        "paid_quantity": r"(?:paid quantity|quantity|qty)\s*[:=-]\s*([\d,]+(?:\.\d+)?)",
        "free_cartons": r"(?:free cartons|free quantity|free qty)\s*[:=-]\s*([\d,]+(?:\.\d+)?)",
        "quantity_unit": r"(?:paid quantity|quantity|qty)\s*[:=-]\s*[\d,.]+\s*(cartons?|cases?|jars?|pieces?|pcs?|bags?|units?)\b",
    }

    def extract_text(self, text: str) -> dict:
        fields = {"product": None, "net_amount_paid": None, "paid_quantity": None,
                  "free_cartons": None, "quantity_unit": "unknown", "evidence": {}}
        for line in text.splitlines():
            for key, pattern in self.patterns.items():
                match = re.search(pattern, line, re.IGNORECASE)
                if not match:
                    continue
                value = match.group(1).strip()
                if key == "quantity_unit":
                    value = value.lower().rstrip("s")
                    value = {"case": "carton", "pc": "piece", "pcs": "piece"}.get(value, value)
                fields[key] = value
                fields["evidence"][key] = line.strip()
        # A quantity with a unit can be written on the same line as the quantity.
        return fields
