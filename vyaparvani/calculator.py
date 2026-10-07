from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

VALID_UNITS = {"carton", "jar", "piece", "bag", "unit", "unknown"}
VALID_STATES = {"CLEAR", "CONFIRM", "CANNOT CALCULATE"}


def _number(value):
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value).replace(",", "").replace("₹", "").strip())
    except (InvalidOperation, ValueError):
        return None


def validate_and_calculate(fields):
    """Validate reviewed extraction fields and calculate only per carton."""
    issues = []
    product = str(fields.get("product") or "").strip()
    amount = _number(fields.get("net_amount_paid"))
    paid = _number(fields.get("paid_quantity"))
    free = _number(fields.get("free_cartons"))
    amount = amount if amount is not None and amount.is_finite() else None
    paid = paid if paid is not None and paid.is_finite() else None
    free = free if free is not None and free.is_finite() else None
    unit = str(fields.get("quantity_unit") or "unknown").strip().lower().rstrip("s")
    if unit not in VALID_UNITS:
        unit = "unknown"

    if not product:
        issues.append({"field": "product", "message": "Confirm the product name."})
    if amount is None or amount <= 0:
        issues.append({"field": "net_amount_paid", "message": "Enter the positive net amount actually payable, including GST."})
    if paid is None or paid <= 0:
        issues.append({"field": "paid_quantity", "message": "Enter the positive paid quantity."})
    elif paid != paid.to_integral_value():
        issues.append({"field": "paid_quantity", "message": "Carton quantity must be a whole number."})
    if free is None:
        issues.append({"field": "free_cartons", "message": "Confirm the explicit free-carton quantity (enter 0 if none)."})
    elif free < 0 or free != free.to_integral_value():
        issues.append({"field": "free_cartons", "message": "Free cartons must be a whole number of zero or more."})
    if unit != "carton":
        issues.append({"field": "quantity_unit", "message": "Confirm that the printed quantity represents cartons."})

    if amount is None or amount <= 0 or paid is None or paid <= 0 or free is None or free < 0:
        status = "CANNOT CALCULATE"
    elif issues:
        status = "CONFIRM"
    else:
        status = "CLEAR"

    result = {
        "status": status,
        "product": product or None,
        "net_amount_paid": str(amount) if amount is not None else None,
        "paid_cartons": str(paid) if paid is not None else None,
        "free_cartons": str(free) if free is not None else None,
        "total_cartons": None,
        "landing_price_per_carton": None,
        "breakdown": [],
        "issues": issues,
    }
    if status == "CLEAR":
        total = paid + free
        price = (amount / total).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        result.update({
            "total_cartons": str(total),
            "landing_price_per_carton": str(price),
            "breakdown": [
                f"Net amount paid (GST included): ₹{amount:,.2f}",
                f"Paid cartons: {paid}",
                f"Explicit free cartons: {free}",
                f"Total cartons received: {paid} + {free} = {total}",
                f"Landing price: ₹{amount:,.2f} ÷ {total} = ₹{price:,.2f}/carton",
            ],
        })
    return result


def calculate(fields):
    """Public API alias used by the app."""
    return validate_and_calculate(fields)
