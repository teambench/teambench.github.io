"""
AuthService — handles authentication token validation.

Called by UserService for every incoming request.
Connects to PostgreSQL to validate session tokens.
"""

import time
import random
import threading
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# ============================================================
# BUG: max_connections is set to 5, which is far too low for
# production load. Under concurrent traffic this pool becomes
# exhausted, causing "connection pool exhausted" errors that
# cascade up through UserService to CheckoutService.
#
# Fix: change max_connections=5 to max_connections=50
# ============================================================
max_connections = 5

# Simulated DB query latency without index (ms)
_BASE_QUERY_LATENCY_MS = 180  # slow without index on users.email
_INDEX_QUERY_LATENCY_MS = 2   # fast with index


def _has_email_index():
    """Check if db/schema.sql contains the index on users.email."""
    import os
    schema_path = os.path.join(os.path.dirname(__file__), '..', 'db', 'schema.sql')
    try:
        with open(schema_path) as f:
            content = f.read()
        return 'idx_users_email' in content or (
            'INDEX' in content.upper() and 'users' in content and 'email' in content
        )
    except FileNotFoundError:
        return False


class ConnectionPool:
    """Simulated database connection pool."""

    def __init__(self, max_conn):
        self._max = max_conn
        self._sem = threading.Semaphore(max_conn)
        self._lock = threading.Lock()
        self._active = 0

    @contextmanager
    def acquire(self, timeout=0.05):
        acquired = self._sem.acquire(timeout=timeout)
        if not acquired:
            raise ConnectionPoolExhausted(
                f"connection pool exhausted (max_connections={self._max})"
            )
        with self._lock:
            self._active += 1
        try:
            yield _DBConnection(_has_email_index())
        finally:
            with self._lock:
                self._active -= 1
            self._sem.release()

    @property
    def active_connections(self):
        return self._active


class _DBConnection:
    def __init__(self, has_index):
        self._has_index = has_index

    def query_user_by_email(self, email):
        """Simulate DB query. Much slower without email index."""
        if self._has_index:
            latency = _INDEX_QUERY_LATENCY_MS + random.uniform(0, 2)
        else:
            latency = _BASE_QUERY_LATENCY_MS + random.uniform(0, 40)
        time.sleep(latency / 1000.0)
        # Return fake user record
        return {"id": hash(email) % 100000, "email": email, "valid": True}


class ConnectionPoolExhausted(Exception):
    pass


# Module-level pool — initialized once with max_connections
_pool = None
_pool_lock = threading.Lock()


def get_pool():
    global _pool
    if _pool is None:
        with _pool_lock:
            if _pool is None:
                _pool = ConnectionPool(max_connections)
    return _pool


def reset_pool():
    """Force pool re-initialization (used by tests after changing max_connections)."""
    global _pool
    with _pool_lock:
        _pool = None


def validate_token(token: str) -> dict:
    """
    Validate an auth token. Returns user info dict on success.
    Raises AuthError on failure.
    """
    pool = get_pool()
    try:
        with pool.acquire(timeout=0.05) as conn:
            # Extract email from token (simplified — real impl would decode JWT)
            email = _decode_token_email(token)
            user = conn.query_user_by_email(email)
            if not user["valid"]:
                raise AuthError("invalid token")
            return user
    except ConnectionPoolExhausted as e:
        logger.error(f"connection pool exhausted (max_connections={max_connections}): {e}")
        raise AuthError(f"service unavailable: {e}")


def _decode_token_email(token: str) -> str:
    """Extract email from token string (simplified)."""
    # Token format: "tok_{email}_{timestamp}"
    parts = token.split("_", 2)
    if len(parts) < 3:
        return f"user_{token[:8]}@example.com"
    return parts[1] if "@" in parts[1] else f"{parts[1]}@example.com"


class AuthError(Exception):
    pass
