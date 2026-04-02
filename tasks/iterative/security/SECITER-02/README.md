# SECITER-02: CORS/CSP Conflict

## Description

Configure CORS and Content-Security-Policy headers so all 6 security tests AND all 4 functionality tests pass simultaneously. The core challenge is that the business requires an inline analytics script, which would normally be blocked by a strict CSP. Agents must discover and implement nonce-based CSP.

## The Conflict

- Strict CSP blocks `unsafe-inline` scripts — required for security
- Analytics snippet is an inline script — required for business
- Solution: generate a per-request nonce, inject into both the HTML `<script nonce="...">` and the CSP `'nonce-{value}'` directive

## Starter State

- 1/10 security tests pass (CORS allowed origin reflects — but reflects ALL origins, which is wrong)
- 3/10 functional tests fail (no nonce in HTML, no CSP header, nonce mismatch)

## Expected Scores

| Agent Type | Expected Score |
|------------|---------------|
| Oracle (best-case single pass) | 0.60 (6/10) |
| Single-pass team | 0.80 (8/10) |
| Multi-turn (2 rounds) | 1.00 (10/10) |

Typical first-pass failure: agents add CSP but forget to replace `{{NONCE}}` in the HTML, or they add `unsafe-inline` as a shortcut. The nonce/HTML sync (test 3) catches incomplete implementations.

## Stopping Condition

Score = 1.0 (all 10 tests pass). Maximum 2 rounds recommended.

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
    app.js                         # Serves index.html with nonce substitution
    middleware/security.js         # CORS + CSP — primary target
  public/
    index.html                     # Has inline analytics script with {{NONCE}} placeholder
  test/
    security/headers.test.js       # 6 security header tests
    functional/app.test.js         # 4 functionality tests
  package.json
```

## Real-World Provenance

This task is inspired by:
- **helmetjs/helmet#236** — CSP inline script conflicts with nonce-based policies:
  https://github.com/helmetjs/helmet/issues/236
- The **2021 Stripe CSP misconfiguration postmortem pattern** — `unsafe-inline` used as a shortcut when nonce injection was missing from the server-side template pass, creating a security regression.

The nonce-based CSP solution (`'nonce-{value}'` in header + `<script nonce="...">` in HTML) is the canonical resolution documented in the helmet issue and the [MDN CSP spec](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Security-Policy/script-src#unsafe_inline_script).

See [`../PROVENANCE.md`](../PROVENANCE.md) for full details.
