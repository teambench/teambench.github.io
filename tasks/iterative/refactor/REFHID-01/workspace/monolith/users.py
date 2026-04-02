"""
User management monolith.
UserProfile fields are mixed into the User class — needs extraction.
"""
from __future__ import annotations
import uuid
from datetime import datetime
from typing import Optional, Dict, Any

from monolith.events import dispatcher


class UserProfile:
    """Profile data for a user — to be extracted into services/profile_service.py."""

    def __init__(
        self,
        user_id: str,
        avatar_url: str = "",
        bio: str = "",
        preferences: Optional[Dict[str, Any]] = None,
        display_name: str = "",
    ):
        self.user_id = user_id
        self.avatar_url = avatar_url
        self.bio = bio
        self.preferences = preferences or {}
        self.display_name = display_name

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "avatar_url": self.avatar_url,
            "bio": self.bio,
            "preferences": self.preferences,
            "display_name": self.display_name,
        }


class User:
    """
    Core user account — currently carries both account and profile fields.
    After refactoring, profile fields should live in UserProfile/ProfileService.
    """

    def __init__(
        self,
        email: str,
        # Profile fields (to be extracted)
        avatar_url: str = "",
        bio: str = "",
        preferences: Optional[Dict[str, Any]] = None,
        display_name: str = "",
        user_id: Optional[str] = None,
    ):
        self.user_id: str = user_id or str(uuid.uuid4())
        self.email: str = email
        self.created_at: datetime = datetime.utcnow()

        # Profile fields — these will move to ProfileService after extraction
        self.avatar_url: str = avatar_url
        self.bio: str = bio
        self.preferences: Dict[str, Any] = preferences or {}
        self.display_name: str = display_name
        # Legacy alias used by BillingService
        self.name: str = display_name

    def update(self, **kwargs) -> None:
        """Update user fields and publish user.updated event."""
        allowed_account_fields = {"email"}
        allowed_profile_fields = {"avatar_url", "bio", "preferences", "display_name"}

        for key, value in kwargs.items():
            if key in allowed_account_fields or key in allowed_profile_fields:
                setattr(self, key, value)
                if key == "display_name":
                    self.name = value  # keep alias in sync

        dispatcher.publish("user.updated", self)

    def delete(self) -> None:
        """Publish user.deleted event before removal."""
        dispatcher.publish("user.deleted", self)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "email": self.email,
            "created_at": self.created_at.isoformat(),
            "avatar_url": self.avatar_url,
            "bio": self.bio,
            "preferences": self.preferences,
            "display_name": self.display_name,
        }


class UserRepository:
    """In-memory user store."""

    def __init__(self):
        self._store: Dict[str, User] = {}

    def save(self, user: User) -> User:
        self._store[user.user_id] = user
        return user

    def get(self, user_id: str) -> Optional[User]:
        return self._store.get(user_id)

    def delete(self, user_id: str) -> bool:
        if user_id in self._store:
            del self._store[user_id]
            return True
        return False

    def all(self) -> list:
        return list(self._store.values())
