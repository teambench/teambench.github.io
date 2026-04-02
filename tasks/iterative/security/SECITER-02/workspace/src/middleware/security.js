'use strict';

const crypto = require('crypto');

// VULNERABILITY: CORS configured too broadly — reflects any origin.
// Fix: whitelist only https://app.example.com and https://admin.example.com
const ALLOWED_ORIGINS = [
  'https://app.example.com',
  'https://admin.example.com',
  // BUG: wildcard effective because any origin is reflected below
];

function corsMiddleware(req, res, next) {
  const origin = req.headers.origin;

  // VULNERABILITY: reflects any origin unconditionally, defeating CORS protection
  if (origin) {
    res.setHeader('Access-Control-Allow-Origin', origin);
    res.setHeader('Access-Control-Allow-Credentials', 'true');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Request-ID');
  }

  if (req.method === 'OPTIONS') {
    return res.sendStatus(204);
  }

  next();
}

// VULNERABILITY: No CSP set at all. No security headers.
// Fix: add full CSP with nonce-based inline script support, plus X-Frame-Options, etc.
function securityHeaders(req, res, next) {
  // Placeholder — no security headers applied
  next();
}

module.exports = { corsMiddleware, securityHeaders };
