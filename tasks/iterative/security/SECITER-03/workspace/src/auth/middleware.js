'use strict';

const jwt = require('jsonwebtoken');

const JWT_SECRET = process.env.JWT_SECRET || 'test-secret';
const JWT_ALGORITHM = 'HS256';

/**
 * Express middleware: authenticate request via Bearer token.
 *
 * VULNERABILITY (breaking change): Uses jsonwebtoken v8 callback API.
 * In v9, passing a callback to jwt.verify() with an async signature is no longer supported.
 * The middleware must be rewritten to use synchronous jwt.verify() inside a try/catch.
 *
 * Current behavior (broken after v9 upgrade):
 *   jwt.verify(token, secret, {}, callback)  ← no longer works in v9
 *
 * Fix:
 *   try {
 *     const decoded = jwt.verify(token, JWT_SECRET, { algorithms: [JWT_ALGORITHM] });
 *     req.user = decoded;
 *     next();
 *   } catch (err) {
 *     return res.status(401).json({ error: 'Invalid or expired token' });
 *   }
 */
function authenticateRequest(req, res, next) {
  const authHeader = req.headers['authorization'];

  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ error: 'Authorization header missing or malformed' });
  }

  const token = authHeader.slice(7);

  // VULNERABILITY: v8 callback pattern — breaks silently or throws in jsonwebtoken v9
  jwt.verify(token, JWT_SECRET, { algorithm: JWT_ALGORITHM }, (err, decoded) => {
    if (err) {
      return res.status(401).json({ error: 'Invalid or expired token' });
    }
    req.user = decoded;
    next();
  });
}

/**
 * Optional middleware: allow unauthenticated access but attach user if token present.
 */
function optionalAuth(req, res, next) {
  const authHeader = req.headers['authorization'];
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return next();
  }

  const token = authHeader.slice(7);
  // VULNERABILITY: same v8 callback pattern
  jwt.verify(token, JWT_SECRET, { algorithm: JWT_ALGORITHM }, (err, decoded) => {
    if (!err) req.user = decoded;
    next();
  });
}

module.exports = { authenticateRequest, optionalAuth };
