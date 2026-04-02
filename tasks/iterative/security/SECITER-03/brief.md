# SECITER-03: Dependency Upgrade Cascade — Executor Brief

## Your Job

Fix 3 CVEs by upgrading pinned vulnerable dependencies, then fix any code broken by the upgrades. All 12 integration tests must pass AND `npm audit --production` must show 0 critical/high vulnerabilities.

## CVEs Summary

| Package | Current | Fix To | CVE |
|---------|---------|--------|-----|
| `lodash` | 4.17.15 | >=4.17.21 | Prototype pollution via `_.merge()` |
| `jsonwebtoken` | 8.5.1 | >=9.0.0 | Algorithm confusion |
| `express-fileupload` | 1.2.1 | >=1.4.0 | Path traversal via filename |

## The Hidden Break: jsonwebtoken v8 → v9

jsonwebtoken v9 drops the async callback API. These 3 files all use the old pattern and will break silently or throw at runtime:

| File | Old pattern (broken in v9) |
|------|---------------------------|
| `src/auth/jwt.js` | `jwt.verify(token, secret, opts, callback)` |
| `src/auth/middleware.js` | `jwt.verify(token, secret, opts, callback)` |
| `src/auth/refresh.js` | `jwt.verify(token, secret, opts, callback)` |

**Fix:** Switch to synchronous `jwt.verify(token, secret, { algorithms: ['HS256'] })` (throws on error) or wrap in try/catch. The `algorithms` option is **required** in v9.

## Files to Change

1. `package.json` — bump the 3 package versions
2. `src/utils/transform.js` — strip `__proto__`/`constructor`/`prototype` keys before `_.merge()`
3. `src/auth/jwt.js` — sync `verifyToken()`
4. `src/auth/middleware.js` — sync `authenticateRequest()` middleware
5. `src/auth/refresh.js` — sync `refreshToken()`
6. `src/upload/handler.js` — sanitize filename with `path.basename()`, add `safeFileNames: true`

## Running

```bash
npm install       # after editing package.json
npm audit --production
npm test
```

Tests are in `test/integration/` — 3 files, 12 tests total.

## Function Signatures (do not change)

- `verifyToken(token)` → returns `Promise<decoded>`
- `authenticateRequest(req, res, next)` → Express middleware
- `refreshToken(oldToken)` → returns `Promise<{ token, decoded }>`
- `mergeUserConfig(base, overrides)` → returns merged object

## Real-World Provenance

All three CVEs in this task are **real published vulnerabilities** with NVD entries:

| Package | CVE | NVD Link |
|---------|-----|----------|
| `lodash` 4.17.15 | CVE-2020-28500 | https://nvd.nist.gov/vuln/detail/CVE-2020-28500 |
| `jsonwebtoken` 8.5.1 | CVE-2022-23529 | https://nvd.nist.gov/vuln/detail/CVE-2022-23529 |
| `express-fileupload` 1.2.1 | CVE-2022-27261 | https://nvd.nist.gov/vuln/detail/CVE-2022-27261 |

The jsonwebtoken v8 → v9 API break (dropping async callback `jwt.verify()`) is the real breaking change introduced in the [jsonwebtoken 9.0.0 release](https://github.com/auth0/node-jsonwebtoken/blob/master/CHANGELOG.md) as a direct response to CVE-2022-23529.

See [`../PROVENANCE.md`](../PROVENANCE.md) for full details.
