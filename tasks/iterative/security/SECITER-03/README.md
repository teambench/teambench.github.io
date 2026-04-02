# SECITER-03: Dependency Upgrade Cascade

## Description

Resolve 3 CVEs by upgrading pinned vulnerable dependencies, then fix all code broken by the upgrades. The hidden challenge is that upgrading jsonwebtoken v8 → v9 breaks the callback API used in 3 separate auth files — a single-pass agent that only bumps versions will see tests fail.

## CVEs

| Package | CVE | Vulnerable | Fix |
|---------|-----|-----------|-----|
| `lodash` | CVE-2019-10744 | 4.17.15 | >=4.17.21 |
| `jsonwebtoken` | CVE-2022-23529 | 8.5.1 | >=9.0.0 |
| `express-fileupload` | CVE-2020-35613 | 1.2.1 | >=1.4.0 |

## The Hidden Break

jsonwebtoken v9 drops the async callback API. Three files use `jwt.verify(token, secret, opts, callback)` — all break after the upgrade. Agents must also add `algorithms: ['HS256']` to all `verify()` calls (required in v9).

## Starter State

- Tests: 6/12 pass (auth tests all pass with v8 callbacks, but break after upgrade)
- Audit: 3 critical/high CVEs

## Expected Scores

| Agent Type | Expected Score |
|------------|---------------|
| Oracle (best-case single pass) | 0.50 (clean audit but 0/12 tests after naive upgrade) |
| Single-pass team | 0.67 (clean audit + 8/12 tests) |
| Multi-turn (2 rounds) | 1.00 (clean audit + 12/12 tests) |

First-pass failure: agents upgrade packages (audit passes) but forget to migrate the 3 callback-using files. Round 2 catches the failing auth tests.

## Scoring

```
score = 0.5 * (audit_clean ? 1 : 0) + 0.5 * (passing_tests / 12)
```

## Stopping Condition

Score = 1.0 (clean audit AND all 12 tests pass). Maximum 2 rounds recommended.

## Running

```bash
cd workspace
npm install
npm audit --production
npm test
```

Or use the grader:

```bash
bash grader.sh
```

## Files

```
workspace/
  src/
    app.js
    auth/
      jwt.js          # verifyToken() uses v8 callback — must migrate to v9 sync API
      middleware.js   # authenticateRequest() uses v8 callback
      refresh.js      # refreshToken() uses v8 callback
    utils/
      transform.js    # mergeUserConfig() needs proto-pollution sanitization
    upload/
      handler.js      # filename not sanitized, safeFileNames not set
  test/integration/
    auth.test.js      # 5 tests
    transform.test.js # 4 tests
    upload.test.js    # 3 tests
  package.json        # pinned vulnerable versions
```
