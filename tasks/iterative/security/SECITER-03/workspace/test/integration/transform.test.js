'use strict';

/**
 * SECITER-03: Transform Integration Tests
 * 4 tests — tests 1-2 currently pass, tests 3-4 FAIL (prototype pollution not blocked).
 *
 * Tests:
 *  1. mergeUserConfig merges normal objects correctly
 *  2. camelizeKeys converts snake_case keys
 *  3. mergeUserConfig blocks __proto__ pollution
 *  4. mergeUserConfig blocks constructor/prototype pollution
 */

const { mergeUserConfig, camelizeKeys, snakifyKeys } = require('../../src/utils/transform');

// ─── Test 1: Normal merge ─────────────────────────────────────────────────────

test('1. mergeUserConfig merges normal configuration objects', () => {
  const base = { timeout: 5000, retries: 3, debug: false };
  const overrides = { timeout: 10000, debug: true };

  const result = mergeUserConfig(base, overrides);

  expect(result.timeout).toBe(10000);
  expect(result.retries).toBe(3);
  expect(result.debug).toBe(true);
});

// ─── Test 2: camelizeKeys ─────────────────────────────────────────────────────

test('2. camelizeKeys converts snake_case object keys to camelCase', () => {
  const input = { user_name: 'alice', created_at: '2024-01-01', is_admin: false };
  const result = camelizeKeys(input);

  expect(result.userName).toBe('alice');
  expect(result.createdAt).toBe('2024-01-01');
  expect(result.isAdmin).toBe(false);
});

// ─── Test 3: Prototype pollution via __proto__ ────────────────────────────────

test('3. mergeUserConfig blocks __proto__ prototype pollution', () => {
  // Craft a malicious override that attempts prototype pollution
  const malicious = JSON.parse('{"__proto__": {"polluted": true}}');

  const base = { safe: 'value' };
  mergeUserConfig(base, malicious);

  // Object.prototype must NOT be polluted
  const freshObj = {};
  expect(freshObj.polluted).toBeUndefined();

  // The merge result must not carry __proto__ as an own property
  const result = mergeUserConfig(base, malicious);
  expect(Object.prototype.hasOwnProperty.call(result, '__proto__')).toBe(false);
});

// ─── Test 4: Prototype pollution via constructor ───────────────────────────────

test('4. mergeUserConfig blocks constructor/prototype key pollution', () => {
  const malicious = JSON.parse('{"constructor": {"prototype": {"hacked": true}}}');

  const base = { normal: 'config' };
  mergeUserConfig(base, malicious);

  // Object.prototype must NOT be polluted
  const freshObj = {};
  expect(freshObj.hacked).toBeUndefined();
});
