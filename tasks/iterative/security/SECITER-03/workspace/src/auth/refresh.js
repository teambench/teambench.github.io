'use strict';

const jwt = require('jsonwebtoken');

const JWT_SECRET = process.env.JWT_SECRET || 'test-secret';
const JWT_ALGORITHM = 'HS256';
const JWT_EXPIRY = process.env.JWT_EXPIRY || '1h';

/**
 * Refresh a JWT token: verify the old token and issue a new one.
 *
 * VULNERABILITY (breaking change): Uses jsonwebtoken v8 callback API.
 * Must be migrated to synchronous jwt.verify() for v9 compatibility.
 *
 * Note: expired tokens are also accepted for refresh (ignoreExpiration: true).
 * The `algorithms` option is REQUIRED in jsonwebtoken v9 — omitting it throws.
 *
 * @param {string} oldToken
 * @returns {Promise<{ token: string, decoded: object }>}
 */
function refreshToken(oldToken) {
  return new Promise((resolve, reject) => {
    // VULNERABILITY: v8 callback with ignoreExpiration — breaks in v9
    // Fix: jwt.verify(oldToken, JWT_SECRET, { algorithms: [JWT_ALGORITHM], ignoreExpiration: true })
    jwt.verify(
      oldToken,
      JWT_SECRET,
      { algorithm: JWT_ALGORITHM, ignoreExpiration: true },
      (err, decoded) => {
        if (err) return reject(new Error('Invalid token: ' + err.message));

        // Issue a fresh token with the same payload (minus JWT claims)
        const { iat, exp, nbf, jti, ...payload } = decoded;
        const newToken = jwt.sign(payload, JWT_SECRET, {
          algorithm: JWT_ALGORITHM,
          expiresIn: JWT_EXPIRY,
          jwtid: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
        });

        resolve({ token: newToken, decoded: payload });
      }
    );
  });
}

module.exports = { refreshToken };
