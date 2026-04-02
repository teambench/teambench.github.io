# SECITER-01: Auth Bypass Chain

## Description

Harden a Node.js/Express authentication system that has 5 vulnerability classes baked in. Agents must find and fix all vulnerabilities to get all 8 tests passing.

## Vulnerability Classes

1. SQL injection via raw template literal query
2. Missing rate limiting on the login endpoint
3. JWT returned in response body instead of httpOnly cookie
4. Passwords hashed with MD5 instead of bcrypt
5. Session fixation (no session regeneration after login)

Hidden trap: Sequelize mass-assignment on `User.create(req.body)` in the register endpoint.

## Starter State

- 3/8 tests pass (SQL injection returns 401, logout clears session, backward compat routes exist)
- 5/8 tests fail (rate limit, JWT cookie, bcrypt, session fixation, mass-assignment)
- Baseline grader score: 0.3750

## Expected Scores

| Agent Type | Expected Score |
|------------|---------------|
| Oracle (best-case single pass) | 0.63 (5/8) |
| Single-pass team | 0.75 (6/8) |
| Multi-turn (2 rounds) | 1.00 (8/8) |

The mass-assignment bug (test 7) is the hidden trap that typically catches single-pass agents — they fix the obvious 5 but miss the subtle ORM issue. Multi-turn agents see the test 7 failure in round 1 and fix it in round 2.

## Stopping Condition

Score = 1.0 (all 8 tests pass). Maximum 2 rounds recommended.

## Running

```bash
cd workspace
npm install
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
    app.js                    # Express app (session middleware configured here)
    auth/login.js             # Main file with bugs — primary target
    middleware/rateLimit.js   # Stub rate limiter
    models/User.js            # Sequelize model with MD5 beforeCreate hook
  test/
    security/auth.test.js     # 8 security tests
  package.json
```

## Real-World Provenance

This task is based on **OWASP Top 10 2021** — specifically:
- [A03:2021 Injection](https://owasp.org/Top10/A03_2021-Injection/) — SQL injection via raw template literal query
- [A07:2021 Identification and Authentication Failures](https://owasp.org/Top10/A07_2021-Identification_and_Authentication_Failures/) — weak hashing, JWT in response body, missing rate limiting

**Session fixation** follows the **CVE-2021-41816** pattern (session ID not regenerated after login):
- NVD: https://nvd.nist.gov/vuln/detail/CVE-2021-41816

**Mass assignment hidden trap** mirrors **GitHub Security Advisory GHSA-qm98-sqp4-q5j7** (Sequelize `User.create(req.body)` without field allowlisting):
- Advisory: https://github.com/advisories/GHSA-qm98-sqp4-q5j7

See [`../PROVENANCE.md`](../PROVENANCE.md) for full details.
