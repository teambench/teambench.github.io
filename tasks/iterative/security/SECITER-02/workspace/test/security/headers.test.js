'use strict';

/**
 * SECITER-02: Security Header Tests
 * 6 tests — currently 1 passes (CORS allowed-origin), 5 fail.
 *
 * Tests:
 *  1. Allowed origin receives CORS headers
 *  2. Disallowed origin does NOT receive CORS headers
 *  3. CSP header is present and contains 'nonce-'
 *  4. CSP script-src does NOT contain 'unsafe-inline'
 *  5. X-Frame-Options: DENY is set
 *  6. Referrer-Policy header is set
 */

const request = require('supertest');
const app = require('../../src/app');

// ─── Test 1: Allowed Origin Gets CORS Headers ─────────────────────────────────

test('1. Allowed origin receives Access-Control-Allow-Origin header', async () => {
  const res = await request(app)
    .get('/api/data')
    .set('Origin', 'https://app.example.com');

  expect(res.headers['access-control-allow-origin']).toBe('https://app.example.com');
  expect(res.headers['access-control-allow-credentials']).toBe('true');
});

// ─── Test 2: Disallowed Origin Gets No CORS Headers ───────────────────────────

test('2. Disallowed origin does not receive CORS headers', async () => {
  const res = await request(app)
    .get('/api/data')
    .set('Origin', 'https://evil.attacker.com');

  // Must NOT echo back the attacker origin
  const acao = res.headers['access-control-allow-origin'];
  expect(acao).not.toBe('https://evil.attacker.com');
  // Also must not be wildcard
  expect(acao).not.toBe('*');
});

// ─── Test 3: CSP Header with Nonce ───────────────────────────────────────────

test('3. Content-Security-Policy header is present and contains a nonce', async () => {
  const res = await request(app).get('/');

  const csp = res.headers['content-security-policy'];
  expect(csp).toBeDefined();

  // Must contain a nonce directive (nonce- followed by base64 characters)
  expect(csp).toMatch(/'nonce-[A-Za-z0-9+/=]+'/)
});

// ─── Test 4: No unsafe-inline in script-src ───────────────────────────────────

test("4. CSP script-src does not contain 'unsafe-inline'", async () => {
  const res = await request(app).get('/');

  const csp = res.headers['content-security-policy'];
  expect(csp).toBeDefined();

  // Parse out the script-src directive
  const directives = csp.split(';').map(d => d.trim());
  const scriptSrc = directives.find(d => d.startsWith('script-src'));

  expect(scriptSrc).toBeDefined();
  expect(scriptSrc).not.toContain("'unsafe-inline'");
});

// ─── Test 5: X-Frame-Options ─────────────────────────────────────────────────

test('5. X-Frame-Options: DENY is set', async () => {
  const res = await request(app).get('/');

  expect(res.headers['x-frame-options']).toBe('DENY');
});

// ─── Test 6: Referrer-Policy ─────────────────────────────────────────────────

test('6. Referrer-Policy header is set', async () => {
  const res = await request(app).get('/');

  expect(res.headers['referrer-policy']).toBeDefined();
  expect(res.headers['referrer-policy']).toBe('strict-origin-when-cross-origin');
});
