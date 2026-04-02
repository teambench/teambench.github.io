'use strict';

/**
 * SECITER-03: Auth Integration Tests
 * 5 tests — currently all pass with jsonwebtoken v8.
 * After naive upgrade to v9 without code fixes, all 5 FAIL.
 *
 * Tests:
 *  1. signToken creates a verifiable JWT
 *  2. verifyToken resolves with decoded payload
 *  3. verifyToken rejects with invalid token
 *  4. authenticateRequest middleware allows valid Bearer token
 *  5. refreshToken issues a new token from an old one
 */

process.env.JWT_SECRET = 'test-secret';
process.env.JWT_EXPIRY = '1h';

const request = require('supertest');
const app = require('../../src/app');
const { signToken, verifyToken } = require('../../src/auth/jwt');
const { refreshToken } = require('../../src/auth/refresh');

// ─── Test 1: signToken ────────────────────────────────────────────────────────

test('1. signToken creates a valid JWT string', () => {
  const token = signToken({ sub: 42, username: 'alice', role: 'user' });
  expect(typeof token).toBe('string');
  // JWT has 3 dot-separated parts
  expect(token.split('.')).toHaveLength(3);
});

// ─── Test 2: verifyToken resolves ─────────────────────────────────────────────

test('2. verifyToken resolves with the decoded payload', async () => {
  const token = signToken({ sub: 99, username: 'bob', role: 'admin' });
  const decoded = await verifyToken(token);

  expect(decoded).toBeDefined();
  expect(decoded.sub).toBe(99);
  expect(decoded.username).toBe('bob');
  expect(decoded.role).toBe('admin');
});

// ─── Test 3: verifyToken rejects ─────────────────────────────────────────────

test('3. verifyToken rejects with an invalid token', async () => {
  await expect(verifyToken('not.a.valid.token')).rejects.toThrow();
});

// ─── Test 4: authenticateRequest middleware ───────────────────────────────────

test('4. authenticateRequest allows requests with a valid Bearer token', async () => {
  const token = signToken({ sub: 1, username: 'carol', role: 'user' });

  const res = await request(app)
    .get('/api/protected')
    .set('Authorization', `Bearer ${token}`);

  expect(res.status).toBe(200);
  expect(res.body.user).toBeDefined();
  expect(res.body.user.username).toBe('carol');
});

// ─── Test 5: refreshToken ─────────────────────────────────────────────────────

test('5. refreshToken issues a new token from a valid old token', async () => {
  const originalToken = signToken({ sub: 5, username: 'dave', role: 'user' });
  const { token: newToken, decoded } = await refreshToken(originalToken);

  expect(typeof newToken).toBe('string');
  expect(newToken).not.toBe(originalToken);
  expect(decoded.username).toBe('dave');
  expect(decoded.sub).toBe(5);

  // New token must itself be verifiable
  const newDecoded = await verifyToken(newToken);
  expect(newDecoded.username).toBe('dave');
});
