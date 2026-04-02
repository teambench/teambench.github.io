"""
Prisma client setup.
Do NOT modify this file.

In production this connects to a real PostgreSQL database.
Tests use the mock_prisma fixture to inject a mock client.
"""
from __future__ import annotations
from typing import Optional

# The Prisma client — set via connect() or injected in tests
_client = None


def get_client():
    """Return the active Prisma client instance."""
    if _client is None:
        raise RuntimeError(
            "Prisma client not connected. "
            "Call set_client() first or use the mock_prisma fixture in tests."
        )
    return _client


def set_client(client) -> None:
    """Set the active Prisma client (used by tests and app startup)."""
    global _client
    _client = client


def reset_client() -> None:
    """Reset the client (used in test teardown)."""
    global _client
    _client = None
