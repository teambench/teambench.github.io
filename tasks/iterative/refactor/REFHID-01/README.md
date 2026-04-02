# REFHID-01: Service Extraction with Hidden Subscribers

## Description

A Python monolith mixes `UserProfile` data (avatar, bio, preferences, display_name) into the core `User` class. The task is to extract `UserProfile` into a standalone `ProfileService` in `services/profile_service.py`.

The hidden constraint: three event subscribers (`NotificationService`, `AnalyticsService`, `BillingService`) read profile fields directly off the `User` object passed in pub/sub events. After extraction, those fields no longer live on `User` — subscribers must call `ProfileService.get_profile()` instead.

## Multi-Turn Dynamics

| Round | What happens |
|-------|-------------|
| Round 1 | Executor extracts `ProfileService`, unit tests pass (8/12). Integration tests fail — subscribers still access missing fields. |
| Round 2 | Verifier's attestation flags the 4 failing integration tests. Executor updates subscribers to use `ProfileService`. All 12 pass. |

The integration tests fail in round 1 because:
- `NotificationService` accesses `user.avatar_url` and `user.bio` — missing after extraction
- `AnalyticsService` accesses `user.preferences` — missing after extraction
- `BillingService` accesses `user.name` (alias for `display_name`) — missing after extraction

## Expected Scores

| Agent type | Expected score |
|-----------|---------------|
| Oracle (reads spec.md) | 0.50 round 1 → 1.0 round 2 |
| Single-pass (brief.md only) | ~0.65 |
| Multi-turn (brief → attestation → round 2) | 1.0 |

## Stopping Condition

Stop when score = 1.0 (all 12 tests pass), or after 3 rounds.

## Running Tests

```bash
cd workspace
pip install pytest
python -m pytest test/ -v
```

## Grading

```bash
bash grader.sh
# outputs a float: 0.0000 to 1.0000
```

Score = passing_tests / 12

## Generating Variants

```bash
python generator.py --seed 123 --output-dir ./generated/seed-123/
```

Parameterizes: avatar field name, bio field name, preferences field name, display_name field name, service class name, entity class name, event names.

## Real-World Provenance

This task is based on the microservice extraction pattern documented in two real engineering blog posts:

- **Uber Engineering — "Splitting the Monolith"**: https://www.uber.com/en-US/blog/microservice-architecture/
  Documents the hidden dependency problem when extracting services: consumers of monolith pub/sub events assume a rich, flat event payload and break silently when the extracted service emits a leaner payload.
- **Shopify Engineering — "Deconstructing the Monolith"**: https://shopify.engineering/deconstructing-the-monolith-designing-software-that-maximizes-developer-productivity
  Describes exactly this failure mode: after extraction, event subscribers that read fields directly off domain objects (`user.avatar_url`, `user.bio`) fail because those fields now live in a separate service.

The three hidden subscribers (`NotificationService`, `AnalyticsService`, `BillingService`) accessing profile fields directly off the `User` event object mirror the pub/sub breakage pattern from the Shopify post.

See [`../PROVENANCE.md`](../PROVENANCE.md) for full details.
