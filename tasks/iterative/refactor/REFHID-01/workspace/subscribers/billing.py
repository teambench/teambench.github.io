"""
BillingService — subscribes to user.updated and user.deleted events.
Uses user.name (alias for display_name) for billing records.

HIDDEN CONSTRAINT: After UserProfile extraction, the User object passed in events
will no longer carry name/display_name. This subscriber must be updated to call
ProfileService.get_profile(user.user_id) instead.
"""
from __future__ import annotations
from typing import List, Dict, Any

from monolith.events import dispatcher


class BillingService:
    """Maintains billing records synced with user profile data."""

    def __init__(self):
        self.billing_records: Dict[str, Dict[str, Any]] = {}
        self.deleted_users: List[str] = []
        dispatcher.subscribe("user.updated", self._on_user_updated)
        dispatcher.subscribe("user.deleted", self._on_user_deleted)

    def _on_user_updated(self, user) -> None:
        """
        Sync billing name from user.name (display_name alias).
        Currently accesses user.name directly.
        After ProfileService extraction this field won't be on the User object.
        """
        self.billing_records[user.user_id] = {
            "user_id": user.user_id,
            "billing_name": user.name,   # will break after extraction
            "email": user.email,
        }

    def _on_user_deleted(self, user) -> None:
        """Mark user as deleted in billing system."""
        self.deleted_users.append(user.user_id)
        self.billing_records.pop(user.user_id, None)

    def get_billing_record(self, user_id: str) -> Dict[str, Any] | None:
        return self.billing_records.get(user_id)

    def is_deleted(self, user_id: str) -> bool:
        return user_id in self.deleted_users

    def clear(self) -> None:
        self.billing_records.clear()
        self.deleted_users.clear()
