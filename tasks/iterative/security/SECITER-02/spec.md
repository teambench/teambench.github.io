# SECITER-02: CORS/CSP Conflict — Full Specification

## Overview

You are configuring HTTP security headers for a Node.js/Express web application. The goal is to make **all 6 security tests** AND **all 4 functionality tests** pass simultaneously.

The challenge: the business requires an analytics inline script that would normally be blocked by a strict CSP. The solution is nonce-based CSP — generate a per-request nonce, inject it into the HTML template, and include it in the `Content-Security-Policy` header.

---

## Requirements

### CORS

Configure CORS to:

1. Allow **only** these two origins:
   - `https://app.example.com`
   - `https://admin.example.com`
2. Allow methods: `GET, POST, PUT, DELETE, OPTIONS`
3. Allow headers: `Content-Type, Authorization, X-Request-ID`
4. Allow credentials (`Access-Control-Allow-Credentials: true`)
5. Reject all other origins with no CORS headers (do not reflect arbitrary origins)

### Content-Security-Policy

The CSP header must:

1. `default-src 'self'` — default fallback
2. `script-src 'self' https://cdn.example.com 'nonce-{nonce}'` — allow CDN scripts and nonce-tagged inline scripts
3. `style-src 'self' https://fonts.googleapis.com` — allow Google Fonts CSS
4. `connect-src 'self' wss://realtime.example.com` — allow WebSocket
5. `font-src 'self' https://fonts.gstatic.com` — allow Google Fonts assets
6. `img-src 'self' data: https:` — allow HTTPS images and data URIs
7. `frame-ancestors 'none'` — prevent clickjacking
8. `upgrade-insecure-requests` — force HTTPS

**No `unsafe-inline`** in `script-src`. The nonce is the only way inline scripts are permitted.

### Analytics Inline Script

`public/index.html` contains an analytics snippet:

```html
<script>
  window.__analytics = { id: 'UA-12345-1', env: 'production' };
  (function(w,d,s){ /* tracking stub */ })(window, document, 'script');
</script>
```

This script **cannot be removed** (business requirement). It must receive the nonce attribute so it passes CSP:

```html
<script nonce="{{NONCE}}">
  ...
</script>
```

The server must replace `{{NONCE}}` in the HTML with the per-request generated nonce value. The same nonce must appear in the `Content-Security-Policy` header.

### Additional Security Headers

Set these headers on all responses:

- `X-Frame-Options: DENY`
- `X-Content-Type-Options: nosniff`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: camera=(), microphone=(), geolocation=()`

### WebSocket

The application has a WebSocket endpoint at `/ws`. The CSP `connect-src` must permit `wss://realtime.example.com`. This is already included in the CSP spec above.

---

## Files to Modify

- `src/middleware/security.js` — CORS and CSP logic (primary target)
- `public/index.html` — add `nonce="{{NONCE}}"` to the inline analytics script tag

Do **not** modify the test files.

---

## Constraints

- The nonce must be cryptographically random — use `crypto.randomBytes(16).toString('base64')` or equivalent.
- A new nonce must be generated **per request**, not shared globally.
- The nonce must be stored on `res.locals.nonce` so the HTML renderer can access it.
- The HTML response for `GET /` must replace `{{NONCE}}` with the actual nonce value.
- Wildcard origins (`*`) are **not** allowed anywhere.
- Do not use `helmet` if it would override your custom CSP — configure CSP manually or configure helmet precisely.

---

## Test Files

### Security Tests (`test/security/headers.test.js`) — 6 tests

1. CORS: allowed origin receives proper CORS headers
2. CORS: disallowed origin receives no CORS headers
3. CSP: header present and contains `nonce-`
4. CSP: `script-src` does NOT contain `unsafe-inline`
5. X-Frame-Options: DENY present
6. Referrer-Policy header present

### Functionality Tests (`test/functional/app.test.js`) — 4 tests

1. `GET /` returns 200 and HTML
2. Analytics inline script tag has a `nonce` attribute in the response HTML
3. Nonce in HTML matches nonce in CSP header
4. `GET /api/data` returns JSON with CORS headers for allowed origin

---

## Scoring

Score = (passing tests) / 10

A score of 1.0 requires all 10 tests to pass.
