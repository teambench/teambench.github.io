# SECITER-03: Dependency Upgrade Cascade — Full Specification

## Overview

You must resolve three critical/high CVEs in the project's dependencies while keeping all 12 integration tests passing. The challenge is that one of the upgrades (jsonwebtoken v8 → v9) introduces a **breaking API change** that affects multiple files using the old callback pattern.

---

## CVEs to Resolve

### CVE-1: lodash Prototype Pollution (CVE-2019-10744)

**Package:** `lodash` versions < 4.17.21  
**Current version in package.json:** `4.17.15`  
**Fix:** Upgrade to `lodash >= 4.17.21`

**Risk:** `_.merge()`, `_.set()`, and `_.zipObjectDeep()` allow prototype pollution via crafted keys like `__proto__`. The affected code in `src/utils/transform.js` uses `_.merge()` to merge user-supplied configuration objects.

**Code impact:** No API changes between 4.17.15 and 4.17.21 — a version bump in `package.json` is sufficient. However, you must also audit `src/utils/transform.js` to ensure `_.merge()` is not called with unsanitized user input. The function `mergeUserConfig` must sanitize the input by removing `__proto__`, `constructor`, and `prototype` keys before calling `_.merge()`.

### CVE-2: jsonwebtoken Algorithm Confusion (CVE-2022-23529 / jsonwebtoken v9)

**Package:** `jsonwebtoken` versions < 9.0.0  
**Current version in package.json:** `8.5.1`  
**Fix:** Upgrade to `jsonwebtoken >= 9.0.0`

**Breaking change:** jsonwebtoken v9 removes the callback-style API for `jwt.verify()` when used asynchronously. Code using:

```js
jwt.verify(token, secret, options, (err, decoded) => { ... })
```

must be migrated to Promise-based usage:

```js
try {
  const decoded = jwt.verify(token, secret, options);
  // synchronous — throws on error
} catch (err) {
  // handle error
}
```

Or use `util.promisify` if you prefer async/await.

**Files affected by this breaking change:**

- `src/auth/jwt.js` — `verifyToken()` function uses callback
- `src/auth/middleware.js` — `authenticateRequest()` middleware uses callback
- `src/auth/refresh.js` — `refreshToken()` function uses callback

All three files must be updated to use the synchronous `jwt.verify()` or a promisified equivalent.

**Additional v9 requirement:** The `algorithms` option must be explicitly specified in all `jwt.verify()` calls:

```js
jwt.verify(token, secret, { algorithms: ['HS256'] })
```

Omitting `algorithms` in v9 throws a validation error.

### CVE-3: express-fileupload Path Traversal (CVE-2020-35613)

**Package:** `express-fileupload` versions < 1.4.0  
**Current version in package.json:** `1.2.1`  
**Fix:** Upgrade to `express-fileupload >= 1.4.0`

**Risk:** Path traversal via crafted `name` field in multipart uploads. An attacker can write files outside the intended upload directory.

**Code impact:** `src/upload/handler.js` uses `req.files.upload.mv()` without sanitizing the filename. After upgrading, you must also sanitize the filename:

```js
const path = require('path');
const safeName = path.basename(req.files.upload.name);  // strips directory components
const uploadPath = path.join(UPLOAD_DIR, safeName);
req.files.upload.mv(uploadPath, callback);
```

The `express-fileupload` options must also include `{ safeFileNames: true, preserveExtension: true }` when initializing the middleware.

---

## Audit Passing Criteria

Running `npm audit --production` must show **0 critical** and **0 high** severity vulnerabilities after your changes.

All 12 integration tests in `test/integration/` must continue to pass.

---

## Files to Modify

- `package.json` — bump `lodash`, `jsonwebtoken`, `express-fileupload` versions
- `src/utils/transform.js` — sanitize prototype pollution keys before `_.merge()`
- `src/auth/jwt.js` — migrate `verifyToken()` from callback to sync/Promise API
- `src/auth/middleware.js` — migrate `authenticateRequest()` from callback to sync API
- `src/auth/refresh.js` — migrate `refreshToken()` from callback to sync API
- `src/upload/handler.js` — sanitize filename, add `safeFileNames` option

Do **not** modify test files.

---

## Constraints

- Do not downgrade any other dependency.
- Do not remove any endpoint or function signature visible to tests.
- The JWT secret is read from `process.env.JWT_SECRET` (default `'test-secret'` in tests).
- Algorithm is always `HS256`.
- Upload directory is `uploads/` relative to the project root.
- The `mergeUserConfig(base, overrides)` function signature must remain unchanged.
- The `verifyToken(token)` function must return a Promise that resolves to the decoded payload.
- The `authenticateRequest` middleware must call `next()` on success and `res.status(401).json(...)` on failure — same behavior as before, just not using callbacks.

---

## Test Files

- `test/integration/auth.test.js` — 5 tests covering token sign/verify/refresh
- `test/integration/transform.test.js` — 4 tests covering merge and prototype pollution
- `test/integration/upload.test.js` — 3 tests covering file upload and path traversal

---

## Scoring

Score = 0.5 × (audit_clean ? 1 : 0) + 0.5 × (passing_tests / 12)

A perfect score of 1.0 requires both: clean audit AND all 12 tests passing.
