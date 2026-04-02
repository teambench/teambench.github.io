"""
CheckoutService — processes checkout requests.

Calls UserService to validate the user before processing payment.
Any failure in UserService (which calls AuthService) propagates here.
"""

import logging
from services.user_service import get_user, UserServiceError

logger = logging.getLogger(__name__)


class CheckoutError(Exception):
    pass


def process_checkout(token: str, cart: dict) -> dict:
    """
    Process a checkout for the authenticated user.

    Args:
        token: User auth token
        cart: Dict with 'items' list and optional 'coupon'

    Returns:
        Order confirmation dict

    Raises:
        CheckoutError on any failure
    """
    try:
        user = get_user(token)
    except UserServiceError as e:
        logger.error(f"checkout failed — user validation error: {e}")
        raise CheckoutError(f"checkout failed: {e}")

    # Calculate total
    items = cart.get("items", [])
    total = sum(item.get("price", 0) * item.get("qty", 1) for item in items)

    order_id = f"ORD-{user['id']}-{abs(hash(token)) % 999999:06d}"
    logger.info(f"checkout complete: order={order_id} total={total:.2f}")

    return {
        "order_id": order_id,
        "user_id": user["id"],
        "total": total,
        "status": "confirmed",
    }
