"""
Price calculator for orders.

BUG: Uses Python float arithmetic for monetary values.
Float cannot represent many decimal values exactly, causing rounding errors
on edge-case price combinations (~0.1% of orders).

Fix: Replace float arithmetic with decimal.Decimal throughout.
"""


def calculate_total(items: list) -> float:
    """
    Calculate the total price for a list of order items.

    Args:
        items: List of dicts with 'unit_price' and 'quantity' keys.

    Returns:
        Total as a float.

    BUG: float accumulation causes rounding errors.
    Example: calculate_total([{'unit_price': 0.1, 'quantity': 3}])
             returns 0.30000000000000004 instead of 0.30
    """
    total = 0.0  # BUG: should be Decimal('0')
    for item in items:
        price = float(item.get('unit_price', 0))    # BUG: should be Decimal(str(...))
        qty = int(item.get('quantity', 1))
        total += price * qty                         # BUG: float multiply accumulates error
    return total


def apply_tax(total: float, tax_rate: float = 0.08) -> float:
    """Apply a tax rate to a total. Returns total including tax."""
    return total * (1 + tax_rate)   # BUG: float multiply


def round_to_cents(amount: float) -> float:
    """Round amount to 2 decimal places."""
    return round(amount, 2)
