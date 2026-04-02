'use strict';

/**
 * SECITER-02: Functional Tests
 * 4 tests — currently 1 passes (GET / returns 200), 3 fail.
 *
 * Tests:
 *  1. GET / returns 200 with HTML
 *  2. Analytics inline script has a nonce attribute in the HTML
 *  3. Nonce in HTML matches nonce in CSP header
 *  4. GET /api/data returns JSON with CORS headers for allowed origin
 */

const request = require('supertest');
const app = require('../../src/app');

// ─── Test 1: GET / returns 200 HTML ──────────────────────────────────────────

test('1. GET / returns 200 and HTML content', async () => {
  const res = await request(app).get('/');

  expect(res.status).toBe(200);
  expect(res.headers['content-type']).toMatch(/text\/html/);
  expect(res.text).toContain('<html');
});

// ─── Test 2: Analytics script has nonce attribute ────────────────────────────

test('2. Analytics inline script tag has a nonce attribute in the HTML', async () => {
  const res = await request(app).get('/');

  expect(res.status).toBe(200);

  // The {{NONCE}} placeholder must have been replaced with an actual nonce value
  expect(res.text).not.toContain('{{NONCE}}');

  // The analytics script tag must have a nonce="..." attribute
  // Match <script nonce="..."> pattern
  expect(res.text).toMatch(/<script\s[^>]*nonce="[A-Za-z0-9+/=]+"[^>]*>/);
});

// ─── Test 3: Nonce in HTML matches CSP header ────────────────────────────────

test('3. Nonce value in HTML script tag matches the nonce in CSP header', async () => {
  const res = await request(app).get('/');

  // Extract nonce from the HTML
  const nonceInHtml = (() => {
    const match = res.text.match(/nonce="([A-Za-z0-9+/=]+)"/);
    return match ? match[1] : null;
  })();

  expect(nonceInHtml).not.toBeNull();

  // Extract nonce from CSP header
  const csp = res.headers['content-security-policy'] || '';
  const nonceInCsp = (() => {
    const match = csp.match(/'nonce-([A-Za-z0-9+/=]+)'/);
    return match ? match[1] : null;
  })();

  expect(nonceInCsp).not.toBeNull();

  // They must be equal
  expect(nonceInHtml).toBe(nonceInCsp);
});

// ─── Test 4: /api/data returns JSON with CORS ────────────────────────────────

test('4. GET /api/data returns JSON with CORS headers for allowed origin', async () => {
  const res = await request(app)
    .get('/api/data')
    .set('Origin', 'https://admin.example.com');

  expect(res.status).toBe(200);
  expect(res.headers['content-type']).toMatch(/application\/json/);
  expect(res.body).toHaveProperty('message');

  // CORS headers must be set for allowed origin
  expect(res.headers['access-control-allow-origin']).toBe('https://admin.example.com');
});
