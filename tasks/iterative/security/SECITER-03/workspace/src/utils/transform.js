'use strict';

const _ = require('lodash');

/**
 * Merge user-supplied overrides into a base configuration object.
 *
 * VULNERABILITY: No sanitization of prototype-polluting keys.
 * An attacker can send { "__proto__": { "admin": true } } and pollute
 * Object.prototype for all subsequent objects in the process.
 *
 * Fix: Strip __proto__, constructor, and prototype keys from overrides
 * before calling _.merge().
 *
 * @param {object} base - Base config object
 * @param {object} overrides - User-supplied overrides (untrusted)
 * @returns {object} Merged config
 */
function mergeUserConfig(base, overrides) {
  // VULNERABILITY: passing user input directly to _.merge() allows prototype pollution
  // lodash 4.17.15 is affected by CVE-2019-10744
  return _.merge({}, base, overrides);
}

/**
 * Deeply transform keys of an object using a mapping function.
 * @param {object} obj
 * @param {Function} keyFn
 * @returns {object}
 */
function transformKeys(obj, keyFn) {
  if (typeof obj !== 'object' || obj === null) return obj;
  if (Array.isArray(obj)) return obj.map(item => transformKeys(item, keyFn));

  return Object.keys(obj).reduce((acc, key) => {
    const newKey = keyFn(key);
    acc[newKey] = transformKeys(obj[key], keyFn);
    return acc;
  }, {});
}

/**
 * Camel-case all keys in an object (for API response normalization).
 */
function camelizeKeys(obj) {
  return transformKeys(obj, key => _.camelCase(key));
}

/**
 * Snake-case all keys in an object (for DB writes).
 */
function snakifyKeys(obj) {
  return transformKeys(obj, key => _.snakeCase(key));
}

/**
 * Pick only allowed fields from an object.
 */
function pickAllowed(obj, allowedFields) {
  return _.pick(obj, allowedFields);
}

module.exports = { mergeUserConfig, transformKeys, camelizeKeys, snakifyKeys, pickAllowed };
