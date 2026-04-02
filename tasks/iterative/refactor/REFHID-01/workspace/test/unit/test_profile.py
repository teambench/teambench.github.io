"""
8 unit tests for ProfileService and UserProfile.
These tests import from services.profile_service — the target of extraction.
All 8 should pass once the service is created.
"""
import pytest

try:
    from services.profile_service import ProfileService, UserProfile
    _available = True
except ImportError:
    ProfileService = UserProfile = None
    _available = False

pytestmark = pytest.mark.skipif(
    not _available,
    reason="services/profile_service.py not yet created — create it to unlock these tests",
)


@pytest.fixture
def service():
    return ProfileService()


class TestUserProfile:
    def test_profile_has_required_fields(self):
        profile = UserProfile(
            user_id="u1",
            avatar_url="https://example.com/avatar.png",
            bio="Hello world",
            preferences={"theme": "dark"},
            display_name="Alice",
        )
        assert profile.user_id == "u1"
        assert profile.avatar_url == "https://example.com/avatar.png"
        assert profile.bio == "Hello world"
        assert profile.preferences == {"theme": "dark"}
        assert profile.display_name == "Alice"

    def test_profile_defaults(self):
        profile = UserProfile(user_id="u2")
        assert profile.avatar_url == ""
        assert profile.bio == ""
        assert profile.preferences == {}
        assert profile.display_name == ""

    def test_profile_to_dict(self):
        profile = UserProfile(user_id="u3", display_name="Bob", bio="Bio text")
        d = profile.to_dict()
        assert d["user_id"] == "u3"
        assert d["display_name"] == "Bob"
        assert d["bio"] == "Bio text"


class TestProfileService:
    def test_get_profile_returns_none_for_unknown(self, service):
        result = service.get_profile("nonexistent")
        assert result is None

    def test_update_profile_creates_entry(self, service):
        profile = service.update_profile(
            "u1",
            avatar_url="https://cdn.example.com/pic.jpg",
            bio="Test bio",
            preferences={"lang": "en"},
            display_name="Charlie",
        )
        assert isinstance(profile, UserProfile)
        assert profile.user_id == "u1"
        assert profile.avatar_url == "https://cdn.example.com/pic.jpg"

    def test_get_profile_after_update(self, service):
        service.update_profile("u2", display_name="Diana", bio="Hi there")
        profile = service.get_profile("u2")
        assert profile is not None
        assert profile.display_name == "Diana"
        assert profile.bio == "Hi there"

    def test_update_profile_partial(self, service):
        service.update_profile("u3", display_name="Eve", bio="Original bio")
        service.update_profile("u3", bio="Updated bio")
        profile = service.get_profile("u3")
        assert profile.display_name == "Eve"
        assert profile.bio == "Updated bio"

    def test_delete_profile(self, service):
        service.update_profile("u4", display_name="Frank")
        service.delete_profile("u4")
        assert service.get_profile("u4") is None
