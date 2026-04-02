# Security Tasks — Real-World Provenance

This document records the real-world sources, CVEs, and incidents that inspired the security tasks in this category.

---

## SECITER-01: Auth Bypass Chain

**Inspired by:** OWASP Top 10 2021 — A03 Injection and A07 Identification and Authentication Failures.

### Real-World References

| Vulnerability | Source |
|---------------|--------|
| SQL Injection (A03:2021) | [OWASP Top 10 2021 — A03](https://owasp.org/Top10/A03_2021-Injection/) |
| Session fixation | CVE-2021-41816 pattern — Ruby on Rails session fixation variant; see [NVD CVE-2021-41816](https://nvd.nist.gov/vuln/detail/CVE-2021-41816) |
| Mass assignment (Sequelize) | [GHSA-qm98-sqp4-q5j7](https://github.com/advisories/GHSA-qm98-sqp4-q5j7) — Sequelize mass-assignment via unguarded `create(req.body)` pattern |
| Authentication failures (A07:2021) | [OWASP Top 10 2021 — A07](https://owasp.org/Top10/A07_2021-Identification_and_Authentication_Failures/) |

### Design Notes

The hidden mass-assignment trap (`User.create(req.body)` in the register endpoint) directly mirrors the Sequelize advisory GHSA-qm98-sqp4-q5j7, where untrusted request bodies are passed directly to ORM `create()` calls, allowing attackers to set privileged fields such as `isAdmin`.

The session fixation bug follows the CVE-2021-41816 pattern: a session ID is allocated before authentication, and the same ID is reused after a successful login without regeneration, allowing an attacker who plants a known session ID to take over an authenticated session.

---

## SECITER-02: CORS/CSP Conflict

**Inspired by:** Real GitHub issue [helmetjs/helmet#236](https://github.com/helmetjs/helmet/issues/236) (CSP inline script conflicts with nonce-based policies) and the 2021 Stripe CSP misconfiguration postmortem pattern.

### Real-World References

| Source | Link |
|--------|------|
| helmetjs/helmet#236 — CSP inline script conflict | https://github.com/helmetjs/helmet/issues/236 |
| Stripe 2021 CSP misconfiguration postmortem pattern | Stripe engineering discussion on `unsafe-inline` fallback when nonce injection was missing from the server-side template pass |
| MDN — CSP nonce-based inline scripts | https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Security-Policy/script-src#unsafe_inline_script |

### Design Notes

The helmet#236 issue documents exactly the tension this task recreates: a strict `script-src` policy breaks third-party and analytics inline snippets that teams depend on. The standard resolution — per-request nonce generation with `<script nonce="...">` and matching `'nonce-{value}'` in the CSP header — is the canonical fix documented in that issue and the MDN spec.

The CORS misconfiguration (reflecting all origins) mirrors a common class of misconfiguration where `Access-Control-Allow-Origin` is set to `req.headers.origin` unconditionally, equivalent to `*` but bypassing the browser's credentialed-request restriction.

---

## SECITER-03: Dependency Upgrade Cascade

**Based on REAL published CVEs.** All three CVEs are documented in the NVD and have verified CVSS scores.

### CVE References

| Package | CVE | NVD Link | CVSS |
|---------|-----|----------|------|
| `lodash` 4.17.15 | CVE-2020-28500 | https://nvd.nist.gov/vuln/detail/CVE-2020-28500 | 7.5 High — prototype pollution via `_.merge()` |
| `jsonwebtoken` 8.5.1 | CVE-2022-23529 | https://nvd.nist.gov/vuln/detail/CVE-2022-23529 | 8.8 High — algorithm confusion / secret injection |
| `express-fileupload` 1.2.1 | CVE-2022-27261 | https://nvd.nist.gov/vuln/detail/CVE-2022-27261 | 7.5 High — path traversal via unsanitized filename |

### Design Notes

The jsonwebtoken v8 → v9 API break (dropping the async callback form of `jwt.verify()`) is the real breaking change introduced in the [jsonwebtoken 9.0.0 release](https://github.com/auth0/node-jsonwebtoken/blob/master/CHANGELOG.md) as a direct response to CVE-2022-23529. The fix required callers to switch to synchronous verification with an explicit `algorithms` allowlist, which is the hidden cascade this task tests.

The lodash prototype pollution chain (CVE-2020-28500) is exploitable when `_.merge()` receives attacker-controlled input without stripping `__proto__`, `constructor`, and `prototype` keys — the exact pattern in `src/utils/transform.js`.
