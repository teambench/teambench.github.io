"""
NotificationService — subscribes to user.updated events.
Uses user.avatar_url and user.bio to build notification payloads.

HIDDEN CONSTRAINT: After UserProfile extraction, the User object passed in events
will no longer carry avatar_url or bio. This subscriber must be updated to call
ProfileService.get_profile(user.user_id) instead.
"""
from __future__ import annotations
from typing import List, Dict, Any

from monolith.events import dispatcher


class NotificationService:
    """Sends notifications when user profiles change."""

    def __init__(self):
        self.sent_notifications: List[Dict[str, Any]] = []
        dispatcher.subscribe("user.updated", self._on_user_updated)

    def _on_user_updated(self, user) -> None:
        """
        Build notification payload using profile fields.
        Currently accesses user.avatar_url and user.bio directly.
        After ProfileService extraction these fields won't be on the User object.
        """
        notification = {
            "type": "profile_updated",
            "user_id": user.user_id,
            "avatar_url": user.avatar_url,   # will break after extraction
            "bio_preview": user.bio[:100] if user.bio else "",  # will break after extraction
        }
        self.sent_notifications.append(notification)

    def get_last_notification(self) -> Dict[str, Any] | None:
        return self.sent_notifications[-1] if self.sent_notifications else None

    def clear(self) -> None:
        self.sent_notifications.clear()
