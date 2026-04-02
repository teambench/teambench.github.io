"""
4 integration tests verifying that subscribers work correctly
after UserProfile is extracted from the User monolith.

These tests will FAIL in round 1 if subscribers still access profile
fields directly on the User object (since those fields will be gone).
They pass once subscribers are updated to call ProfileService.
"""
import pytest

from monolith.events import dispatcher
from monolith.users import User, UserRepository

# Soft import — fails gracefully if profile_service hasn't been created yet
try:
    from services.profile_service import ProfileService as _ProfileService
    _profile_service_available = True
except ImportError:
    _ProfileService = None
    _profile_service_available = False

# Soft import subscribers
try:
    from subscribers.notification import NotificationService as _NotificationService
    from subscribers.analytics import AnalyticsService as _AnalyticsService
    from subscribers.billing import BillingService as _BillingService
    _subscribers_available = True
except ImportError:
    _NotificationService = _AnalyticsService = _BillingService = None
    _subscribers_available = False

_needs_profile_service = pytest.mark.skipif(
    not _profile_service_available,
    reason="services/profile_service.py not yet created",
)
_needs_subscribers = pytest.mark.skipif(
    not (_profile_service_available and _subscribers_available),
    reason="profile_service or updated subscribers not yet available",
)


@pytest.fixture(autouse=True)
def reset_dispatcher():
    """Reset pub/sub state between tests."""
    dispatcher.clear()
    yield
    dispatcher.clear()


@pytest.fixture
def profile_service():
    if not _profile_service_available:
        pytest.skip("services/profile_service.py not yet created")
    return _ProfileService()


@pytest.fixture
def notification_svc(profile_service):
    if not _subscribers_available:
        pytest.skip("subscribers not yet updated to accept profile_service")
    try:
        return _NotificationService(profile_service=profile_service)
    except TypeError:
        pytest.fail(
            "NotificationService must accept profile_service= kwarg. "
            "Update __init__ to: def __init__(self, profile_service): ..."
        )


@pytest.fixture
def analytics_svc(profile_service):
    if not _subscribers_available:
        pytest.skip("subscribers not yet updated to accept profile_service")
    try:
        return _AnalyticsService(profile_service=profile_service)
    except TypeError:
        pytest.fail(
            "AnalyticsService must accept profile_service= kwarg."
        )


@pytest.fixture
def billing_svc(profile_service):
    if not _subscribers_available:
        pytest.skip("subscribers not yet updated to accept profile_service")
    try:
        return _BillingService(profile_service=profile_service)
    except TypeError:
        pytest.fail(
            "BillingService must accept profile_service= kwarg."
        )


@pytest.fixture
def repo():
    return UserRepository()


class TestNotificationSubscriber:
    @_needs_subscribers
    def test_notification_includes_avatar_and_bio(
        self, notification_svc, profile_service, repo
    ):
        """NotificationService must get avatar_url and bio from ProfileService."""
        user = User(email="alice@example.com")
        repo.save(user)
        profile_service.update_profile(
            user.user_id,
            avatar_url="https://example.com/alice.png",
            bio="Alice's bio",
        )
        user.update(email="alice2@example.com")  # triggers user.updated

        note = notification_svc.get_last_notification()
        assert note is not None, (
            "NotificationService received no notification. "
            "Did you subscribe to 'user.updated' in __init__?"
        )
        assert note["user_id"] == user.user_id
        assert note["avatar_url"] == "https://example.com/alice.png", (
            f"Expected avatar_url='https://example.com/alice.png', got {note['avatar_url']!r}. "
            "NotificationService must call profile_service.get_profile(user.user_id) "
            "to retrieve avatar_url after UserProfile extraction."
        )
        assert note["bio_preview"] == "Alice's bio", (
            f"Expected bio_preview='Alice's bio', got {note['bio_preview']!r}. "
            "NotificationService must call profile_service.get_profile(user.user_id) "
            "to retrieve bio after UserProfile extraction."
        )


class TestAnalyticsSubscriber:
    @_needs_subscribers
    def test_analytics_captures_preferences(
        self, analytics_svc, profile_service, repo
    ):
        """AnalyticsService must get preferences from ProfileService."""
        user = User(email="bob@example.com")
        repo.save(user)
        profile_service.update_profile(
            user.user_id,
            preferences={"theme": "dark", "language": "en"},
        )
        user.update(email="bob2@example.com")  # triggers user.updated

        events = analytics_svc.get_events()
        assert len(events) == 1, (
            f"Expected 1 analytics event, got {len(events)}. "
            "AnalyticsService must subscribe to 'user.updated' in __init__."
        )
        assert events[0]["preferences_snapshot"] == {"theme": "dark", "language": "en"}, (
            "AnalyticsService must call profile_service.get_profile(user.user_id) "
            "to retrieve preferences after UserProfile extraction."
        )


class TestBillingSubscriber:
    @_needs_subscribers
    def test_billing_sync_on_update(self, billing_svc, profile_service, repo):
        """BillingService must get display_name (billing_name) from ProfileService."""
        user = User(email="carol@example.com")
        repo.save(user)
        profile_service.update_profile(user.user_id, display_name="Carol Smith")
        user.update(email="carol2@example.com")  # triggers user.updated

        record = billing_svc.get_billing_record(user.user_id)
        assert record is not None, (
            "BillingService must create a billing record on user.updated event."
        )
        assert record["billing_name"] == "Carol Smith", (
            f"Expected billing_name='Carol Smith', got {record['billing_name']!r}. "
            "BillingService must call profile_service.get_profile(user.user_id) "
            "to retrieve display_name after UserProfile extraction."
        )
        assert record["email"] == "carol2@example.com"

    @_needs_subscribers
    def test_billing_marks_deleted_user(self, billing_svc, profile_service, repo):
        """BillingService must record deletion from user.deleted event."""
        user = User(email="dave@example.com")
        repo.save(user)
        profile_service.update_profile(user.user_id, display_name="Dave")
        user.update(email="dave@example.com")  # create billing record first
        user.delete()  # triggers user.deleted

        assert billing_svc.is_deleted(user.user_id), (
            "BillingService must subscribe to 'user.deleted' and mark user as deleted."
        )
        assert billing_svc.get_billing_record(user.user_id) is None
