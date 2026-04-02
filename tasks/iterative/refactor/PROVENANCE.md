# Refactoring Tasks — Real-World Provenance

This document records the real-world engineering blog posts, GitHub issues, and postmortems that inspired the refactoring tasks in this category.

---

## REFHID-01: Service Extraction with Hidden Subscribers

**Inspired by:** Real microservice extraction stories — specifically the Uber Engineering "Splitting the Monolith" series and the pub/sub subscriber breakage pattern documented in the Shopify Engineering blog on service extraction.

### Real-World References

| Source | Reference |
|--------|-----------|
| Uber Engineering — "Splitting the Monolith" blog series | https://www.uber.com/en-US/blog/microservice-architecture/ — Documents the hidden dependency problem when extracting services: consumers of monolith events assume a rich, flat event payload and break silently when extracted services emit leaner payloads |
| Shopify Engineering — "Deconstructing the Monolith" | https://shopify.engineering/deconstructing-the-monolith-designing-software-that-maximizes-developer-productivity — Describes the pub/sub subscriber issue: after extraction, event subscribers that read fields directly off domain objects (`user.avatar_url`, `user.bio`) fail because those fields now live in a separate service |

### Design Notes

The core failure mode — three event subscribers (`NotificationService`, `AnalyticsService`, `BillingService`) reading profile fields directly off the `User` object in pub/sub events — directly mirrors the Shopify extraction postmortem pattern. The monolith's event bus passes a rich domain object; after extraction, the extracted service no longer populates those fields on `User`, so all subscribers that assumed a flat payload break silently (no compile error, no immediate runtime error, just wrong behavior at the point of field access).

The Uber blog series documents this as one of the top two hidden costs of service extraction: consumers of internal events are not always visible from the service boundary being split, making integration test coverage the only reliable detection mechanism.

---

## REFHID-02: Config Format Migration (INI → YAML)

**Inspired by:** Real GitHub issue [docker/compose#9362](https://github.com/docker/compose/issues/9362) — config file format migration breaking shell scripts and Docker Compose volume mounts.

### Real-World References

| Source | Link |
|--------|------|
| docker/compose#9362 — config format migration breaking shell scripts | https://github.com/docker/compose/issues/9362 |

### Design Notes

The docker/compose#9362 issue documents a real migration scenario: the Compose project changed its config file format, and shell scripts in CI pipelines and deployment tooling that parsed the old format with `grep`/`awk` broke silently. The Python application layer was updated correctly, but the shell-layer consumers (`deploy/start.sh`, `deploy/health_check.sh`) and the Docker Compose volume mount (`docker-compose.yml`) were not, causing failures that only surfaced during deploy integration tests — not unit tests.

This task recreates that exact failure mode: `src/config.py` is correctly migrated to PyYAML in round 1 (unit tests pass), but the shell scripts and `docker-compose.yml` still reference `app.ini`, causing the deploy integration tests to fail. The fix requires updating all three shell-layer artifacts, matching the remediation pattern documented in the docker/compose issue.

---

## REFHID-03: Migrate ORM from SQLAlchemy Core to Prisma

**Inspired by:** Real Prisma GitHub issues documenting missing SQL primitives that affect migration completeness.

### Real-World References

| Source | Link |
|--------|------|
| prisma/prisma#7252 — `SELECT FOR UPDATE` (row-level locking) not supported in Prisma query API | https://github.com/prisma/prisma/issues/7252 |
| prisma/prisma#5068 — `LATERAL JOIN` unsupported in Prisma, requiring raw query fallback | https://github.com/prisma/prisma/issues/5068 |

### Design Notes

Both Prisma issues document a recurring pain point in ORM migration: advanced SQL primitives that are idiomatic in raw SQL or SQLAlchemy Core have no direct equivalent in Prisma's query API, forcing engineers to use `prisma.$queryRaw()` or `prisma.$executeRaw()` as escape hatches.

The `lock_and_get_order(order_id)` function in this task targets exactly the `SELECT FOR UPDATE` gap documented in prisma/prisma#7252 — the Prisma client has no `.forUpdate()` or lock-hint mechanism, so the migration must use a raw query. The `get_product_inventory(ids)` function touches the lateral-join pattern documented in prisma/prisma#5068. These two functions represent the "hidden breaks" in the migration: naively translating the other six functions to Prisma query API works, but these two require awareness of Prisma's documented limitations.
