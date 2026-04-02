# SECITER-02: CORS/CSP Conflict — Executor Brief

## Your Job

Configure CORS and Content-Security-Policy headers so all 6 security tests AND all 4 functionality tests pass. Currently 4 pass and 6 fail.

## The Core Conflict

The `public/index.html` page has an inline analytics script (business requirement — cannot be removed). A strict CSP would block it. The solution is **nonce-based CSP**: generate a per-request cryptographic nonce, inject it into the HTML `<script nonce="...">` tag, and include `'nonce-{value}'` in the CSP `script-src`.

## Files to Touch

| File | What to do |
|------|-----------|
| `src/middleware/security.js` | Fix CORS (too broad), add full CSP with nonce, add security headers |
| `public/index.html` | Add `nonce="{{NONCE}}"` to the inline `<script>` tag |

## CORS Requirements

- Allowed origins: `https://app.example.com` and `https://admin.example.com` ONLY
- Methods: GET, POST, PUT, DELETE, OPTIONS
- Headers: Content-Type, Authorization, X-Request-ID
- Credentials: true
- No wildcard (`*`) anywhere

## CSP Requirements

```
default-src 'self';
script-src 'self' https://cdn.example.com 'nonce-{nonce}';
style-src 'self' https://fonts.googleapis.com;
connect-src 'self' wss://realtime.example.com;
font-src 'self' https://fonts.gstatic.com;
img-src 'self' data: https:;
frame-ancestors 'none';
upgrade-insecure-requests
```

No `unsafe-inline` in script-src.

## Nonce Pattern

```js
const crypto = require('crypto');
// Per-request:
const nonce = crypto.randomBytes(16).toString('base64');
res.locals.nonce = nonce;
// In CSP header: script-src 'self' https://cdn.example.com 'nonce-' + nonce
// In HTML: replace {{NONCE}} with nonce value
```

## Running Tests

```bash
npm install
npm test
```

Security tests: `test/security/headers.test.js` (6 tests)
Functional tests: `test/functional/app.test.js` (4 tests)
