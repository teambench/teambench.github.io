# REFHID-01: Extract UserProfile into a Standalone Service

## Your Task

Extract `UserProfile` functionality from `monolith/users.py` into a new `services/profile_service.py`. All 12 tests must pass after extraction.

## Files to Work With

```
workspace/
  monolith/users.py             # User class with profile fields mixed in — extract from here
  monolith/events.py            # EventDispatcher (pub/sub) — do not modify
  services/                     # Empty — create profile_service.py here
  subscribers/notification.py   # Event subscriber
  subscribers/analytics.py      # Event subscriber
  subscribers/billing.py        # Event subscriber
  test/unit/test_profile.py     # 8 unit tests
  test/integration/test_subscribers.py  # 4 integration tests
```

## Quick Start

```bash
cd workspace
pip install pytest
python -m pytest test/ -v
```

## What to Create

Create `services/profile_service.py` exporting:
- `UserProfile` dataclass with fields: `user_id`, `avatar_url`, `bio`, `preferences`, `display_name`
- `ProfileService` class with:
  - `get_profile(user_id: str) -> UserProfile`
  - `update_profile(user_id: str, **kwargs) -> UserProfile`
  - `delete_profile(user_id: str) -> None`

## What to Update in `monolith/users.py`

- Remove profile fields from `User` class
- Import and delegate profile operations to `ProfileService`
- Keep event publishing intact

## Note

There is a pub/sub event system in `events/`. Subscribers in `subscribers/` listen to `user.updated` and `user.deleted` events. Check whether they depend on any fields you are moving.

## Target

```
python -m pytest test/ -v
# 12 passed
```
