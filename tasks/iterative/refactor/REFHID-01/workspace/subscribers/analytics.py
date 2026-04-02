"""
AnalyticsService — subscribes to user.updated events.
Uses user.preferences to track feature usage.

HIDDEN CONSTRAINT: After UserProfile extraction, the User object passed in events
will no longer carry preferences. This subscriber must be updated to call
ProfileService.get_profile(user.user_id) instead.
"""
from __future__ import annotations
from typing import List, Dict, Any

from monolith.events import dispatcher


class AnalyticsService:
    """Tracks user preference changes for analytics."""

    def __init__(self):
        self.events_recorded: List[Dict[str, Any]] = []
        dispatcher.subscribe("user.updated", self._on_user_updated)

    def _on_user_updated(self, user) -> None:
        """
        Record analytics event from user preferences.
        Currently accesses user.preferences directly.
        After ProfileService extraction this field won't be on the User object.
        """
        event = {
            "event": "user_updated",
            "user_id": user.user_id,
            "preferences_snapshot": dict(user.preferences),  # will break after extraction
        }
        self.events_recorded.append(event)

    def get_events(self) -> List[Dict[str, Any]]:
        return list(self.events_recorded)

    def clear(self) -> None:
        self.events_recorded.clear()
