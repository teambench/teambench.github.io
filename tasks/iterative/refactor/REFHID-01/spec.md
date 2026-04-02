# REFHID-01: Service Extraction with Hidden Subscribers

## Overview

You are given a Python monolith that mixes core `User` account data with `UserProfile` data (avatar, bio, preferences). Your task is to extract the `UserProfile` functionality into a standalone `ProfileService`, while keeping all 12 tests passing.

This is a **multi-turn** task. Round 1 focuses on the extraction itself. The Verifier will run integration tests that exercise the pub/sub event system — if subscribers break after extraction, round 2 will require you to fix them.

## Architecture

```
monolith/
  users.py          # User + UserProfile mixed together; pub/sub hooks inside
  events.py         # EventDispatcher: publish/subscribe
subscribers/
  notification.py   # Subscribes to user.updated — uses user.avatar_url, user.bio
  analytics.py      # Subscribes to user.updated — uses user.preferences
  billing.py        # Subscribes to user.updated, user.deleted — uses user.name
services/           # Target directory — currently empty
test/
  unit/test_profile.py          # 8 unit tests for UserProfile logic
  integration/test_subscribers.py  # 4 integration tests for subscriber behavior
```

## What to Extract

Move the following from `monolith/users.py` into `services/profile_service.py`:

- `UserProfile` class (fields: `avatar_url`, `bio`, `preferences`, `display_name`)
- `ProfileService` class with methods:
  - `get_profile(user_id: str) -> UserProfile`
  - `update_profile(user_id: str, **kwargs) -> UserProfile`
  - `delete_profile(user_id: str) -> None`

The `User` class in `monolith/users.py` must remain but should **delegate** profile operations to `ProfileService`. After extraction, the `User` object passed to event subscribers will **no longer carry** the profile fields directly.

## Hidden Constraint (Subscribers)

The three subscribers currently receive a full `User` object from `user.updated` / `user.deleted` events and access profile fields directly:

| Subscriber | Fields accessed |
|---|---|
| `NotificationService` | `user.avatar_url`, `user.bio` |
| `AnalyticsService` | `user.preferences` |
| `BillingService` | `user.name` (which maps to `display_name`) |

After extraction, the event payload will only contain the `User` stub (id, email, created_at). Subscribers must be updated to call `ProfileService` to retrieve the moved fields.

**The Planner knows this. The Executor's brief does not mention it explicitly.** This is the constraint that causes round-1 integration test failures.

## Fix Required (Round 2)

Each subscriber must be updated to:
1. Accept a `profile_service: ProfileService` dependency (injected via constructor or module-level singleton)
2. Call `profile_service.get_profile(user.user_id)` to retrieve the profile fields they need

## Success Criterion

All 12 tests must pass:
- 8 unit tests in `test/unit/test_profile.py`
- 4 integration tests in `test/integration/test_subscribers.py`

Run:
```bash
cd workspace && python -m pytest test/ -v
```

Score = (passing tests) / 12

## Constraints

- Do not delete `monolith/users.py` — only move profile-specific code out
- `EventDispatcher` in `monolith/events.py` must not be modified
- `services/profile_service.py` must export `ProfileService` and `UserProfile`
- Use an in-memory dict as the profile store (no DB required)
- Python 3.9+, standard library only (plus pytest)

## Files

| File | Role | Modify? |
|------|------|---------|
| `monolith/users.py` | User class + pub/sub hooks | Yes — extract profile code |
| `monolith/events.py` | EventDispatcher | No |
| `services/profile_service.py` | New service (create this) | Create |
| `subscribers/notification.py` | Event subscriber | Yes (round 2) |
| `subscribers/analytics.py` | Event subscriber | Yes (round 2) |
| `subscribers/billing.py` | Event subscriber | Yes (round 2) |
| `test/unit/test_profile.py` | 8 unit tests | No |
| `test/integration/test_subscribers.py` | 4 integration tests | No |

## Evaluation

```
Score = passing_tests / 12
```

- Round 1 oracle: ~0.50 (unit tests pass, integration tests fail)
- Round 2 expected: 1.0 (all 12 pass)
