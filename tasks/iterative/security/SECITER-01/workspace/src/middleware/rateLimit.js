'use strict';

// VULNERABILITY 2: This module is a stub. It exports a no-op middleware.
// Fix: implement a real rate limiter using express-rate-limit.
// Requirements:
//   - max: 5 requests per windowMs
//   - windowMs: 15 * 60 * 1000  (15 minutes)
//   - respond with HTTP 429 and JSON { error: 'Too many requests, please try again later.' }
//   - keyGenerator: req.ip (default is fine)

const loginRateLimiter = (req, res, next) => {
  // Stub: passes all requests through without limiting
  next();
};

module.exports = { loginRateLimiter };
