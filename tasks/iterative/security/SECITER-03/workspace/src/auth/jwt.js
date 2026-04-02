'use strict';

const jwt = require('jsonwebtoken');

const JWT_SECRET = process.env.JWT_SECRET || 'test-secret';
const JWT_ALGORITHM = 'HS256';
const JWT_EXPIRY = process.env.JWT_EXPIRY || '1h';

/**
 * Sign a new JWT token.
 * @param {object} payload
 * @returns {string} signed token
 */
function signToken(payload) {
  return jwt.sign(payload, JWT_SECRET, {
    algorithm: JWT_ALGORITHM,
    expiresIn: JWT_EXPIRY,
  });
}

/**
 * Verify a JWT token and return the decoded payload.
 *
 * VULNERABILITY (breaking change): Uses jsonwebtoken v8 callback API.
 * In jsonwebtoken v9, the callback-based async verify is removed.
 * Additionally, v9 requires `algorithms` to be explicitly specified.
 *
 * Current (broken after v9 upgrade):
 *   jwt.verify(token, secret, options, callback)  ← v8 callback pattern
 *
 * Fix: Use synchronous jwt.verify() wrapped in a try/catch, returned as a Promise.
 *   return new Promise((resolve, reject) => {
 *     try {
 *       const decoded = jwt.verify(token, JWT_SECRET, { algorithms: [JWT_ALGORITHM] });
 *       resolve(decoded);
 *     } catch (err) {
 *       reject(err);
 *     }
 *   });
 *
 * @param {string} token
 * @returns {Promise<object>} decoded payload
 */
function verifyToken(token) {
  return new Promise((resolve, reject) => {
    // VULNERABILITY: v8 callback pattern — breaks in jsonwebtoken v9
    jwt.verify(token, JWT_SECRET, { algorithm: JWT_ALGORITHM }, (err, decoded) => {
      if (err) return reject(err);
      resolve(decoded);
    });
  });
}

module.exports = { signToken, verifyToken };
