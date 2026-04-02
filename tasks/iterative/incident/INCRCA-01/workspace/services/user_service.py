"""
UserService — validates user identity by calling AuthService.

Called by CheckoutService for every checkout request.
"""

import logging
from services.auth_service import validate_token, AuthError

logger = logging.getLogger(__name__)


class UserServiceError(Exception):
    pass


def get_user(token: str) -> dict:
    """
    Retrieve user info for the given auth token.
    Delegates to AuthService for token validation.
    """
    try:
        user = validate_token(token)
        logger.debug(f"user validated: id={user['id']}")
        return user
    except AuthError as e:
        logger.warning(f"downstream timeout or auth failure: {e}")
        raise UserServiceError(f"could not validate user: {e}")
