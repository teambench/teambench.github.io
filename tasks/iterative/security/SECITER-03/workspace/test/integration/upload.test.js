'use strict';

/**
 * SECITER-03: Upload Integration Tests
 * 3 tests — test 1 currently passes, tests 2-3 FAIL (path traversal not blocked).
 *
 * Tests:
 *  1. POST /upload accepts a valid file
 *  2. POST /upload rejects path traversal filenames (../../etc/passwd style)
 *  3. Uploaded filename is sanitized (only the basename is stored)
 */

const request = require('supertest');
const path = require('path');
const fs = require('fs');
const os = require('os');
const app = require('../../src/app');

const UPLOAD_DIR = path.join(__dirname, '..', '..', 'uploads');

// Clean up uploads directory before each test
beforeEach(() => {
  if (fs.existsSync(UPLOAD_DIR)) {
    fs.readdirSync(UPLOAD_DIR).forEach(f => {
      try { fs.unlinkSync(path.join(UPLOAD_DIR, f)); } catch {}
    });
  }
});

// ─── Test 1: Valid file upload ────────────────────────────────────────────────

test('1. POST /upload accepts a valid file and returns 200', async () => {
  const res = await request(app)
    .post('/upload')
    .attach('upload', Buffer.from('hello world'), 'test.txt');

  expect(res.status).toBe(200);
  expect(res.body.message).toMatch(/success/i);
  expect(res.body.filename).toBeDefined();
});

// ─── Test 2: Path traversal rejected ────────────────────────────────────────

test('2. POST /upload does not write outside UPLOAD_DIR (path traversal)', async () => {
  // Attempt classic path traversal
  const traversalName = '../../tmp/evil.txt';

  await request(app)
    .post('/upload')
    .attach('upload', Buffer.from('evil content'), traversalName);

  // The file must NOT have been written outside UPLOAD_DIR
  const escapedPath = path.resolve(UPLOAD_DIR, traversalName);
  const outsideDir = !escapedPath.startsWith(path.resolve(UPLOAD_DIR));

  if (outsideDir) {
    // Verify the file was NOT created at the traversal target
    const targetPath = path.join(os.tmpdir(), 'evil.txt');
    // Either the upload was rejected OR the file doesn't exist outside uploads/
    const writtenOutside = fs.existsSync(targetPath) &&
      fs.readFileSync(targetPath, 'utf8') === 'evil content';
    expect(writtenOutside).toBe(false);
  }

  // The evil.txt file should either not exist or only exist inside UPLOAD_DIR
  const insidePath = path.join(UPLOAD_DIR, 'evil.txt');
  // If it was sanitized, it ends up as "evil.txt" inside uploads/ — that's acceptable
  // What's NOT acceptable is writing to ../../tmp/evil.txt
  const resolvedTarget = path.resolve(UPLOAD_DIR, traversalName);
  if (fs.existsSync(resolvedTarget)) {
    // The resolved path must be inside UPLOAD_DIR
    expect(resolvedTarget.startsWith(path.resolve(UPLOAD_DIR))).toBe(true);
  }
});

// ─── Test 3: Filename is sanitized to basename only ──────────────────────────

test('3. Uploaded filename is sanitized to basename (no directory components)', async () => {
  const traversalName = '../sneaky/secret.txt';

  const res = await request(app)
    .post('/upload')
    .attach('upload', Buffer.from('sneaky content'), traversalName);

  // If upload succeeded, the stored filename must be just "secret.txt", not "../sneaky/secret.txt"
  if (res.status === 200) {
    const storedFilename = res.body.filename;
    expect(storedFilename).toBeDefined();
    // Must not contain path separators
    expect(storedFilename).not.toContain('/');
    expect(storedFilename).not.toContain('\\');
    expect(storedFilename).not.toContain('..');
  } else {
    // Upload was rejected — also acceptable
    expect([400, 403, 422]).toContain(res.status);
  }

  // Verify no file was written outside uploads/
  const outsidePath = path.resolve(__dirname, '..', '..', 'sneaky', 'secret.txt');
  expect(fs.existsSync(outsidePath)).toBe(false);
});
