"""
Discount application for orders.

BUG: Race condition in apply_discount — reads then writes the order total
without a database-level row lock. Two concurrent requests for the same
order can both read the original price and both apply the discount,
resulting in the discount being applied twice (double-discount).

Fix: Add .with_for_update() to the SQLAlchemy query to acquire a row lock
before the read-modify-write cycle.
"""

from decimal import Decimal


def apply_discount(session, order_id: int, discount_rate: float) -> dict:
    """
    Apply a percentage discount to an order's total.

    Args:
        session:       SQLAlchemy session
        order_id:      ID of the order to discount
        discount_rate: Fraction to discount (e.g. 0.10 = 10% off)

    Returns:
        Dict with order_id, original_total, discounted_total

    BUG: No row lock — concurrent calls can double-apply the discount.
    Thread A reads total=100.00, computes 90.00, writes 90.00.
    Thread B reads total=100.00 (same read!), computes 90.00, writes 90.00.
    Result: both threads write 90.00 — one discount application is lost.
    OR:
    Thread A writes 90.00, Thread B reads 90.00, computes 81.00, writes 81.00.
    Result: discount applied twice — $19 instead of $10 removed.
    """
    from orders.models import Order

    # BUG: missing .with_for_update() here — allows concurrent reads before write
    order = session.query(Order).filter_by(id=order_id).first()

    if order is None:
        raise ValueError(f"Order {order_id} not found")

    original_total = float(order.total)
    discounted = original_total * (1 - discount_rate)
    discounted = round(discounted, 4)

    order.total = discounted
    session.commit()

    return {
        "order_id": order_id,
        "original_total": original_total,
        "discounted_total": discounted,
    }


def get_applicable_discounts(customer_id: str, order_total: float) -> list:
    """Return list of applicable discount rates for a customer/total combination."""
    discounts = []
    if order_total >= 100:
        discounts.append({"code": "BULK10", "rate": 0.10})
    if order_total >= 500:
        discounts.append({"code": "BULK20", "rate": 0.20})
    return discounts
