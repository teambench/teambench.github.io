'use strict';

/**
 * SECITER-01: Auth Security Tests
 * 8 tests total — currently 3 pass, 5 fail on the buggy starter code.
 *
 * Tests:
 *  1. SQL injection attempt returns 401 (not 200 or 500)
 *  2. Rate limiting: 6th request returns 429
 *  3. Successful login sets httpOnly cookie (not body token)
 *  4. Passwords stored as bcrypt hash (not MD5)
 *  5. Session ID regenerated after login (session fixation)
 *  6. Session ID changes after logout
 *  7. Register rejects mass-assignment fields (isAdmin, role)
 *  8. All routes accessible under /api/v1/auth/ prefix
 */

process.env.NODE_ENV = 'test';
process.env.JWT_SECRET = 'test-secret';
process.env.SESSION_SECRET = 'test-session-secret';

const request = require('supertest');
const app = require('../../src/app');
const { User, sequelize } = require('../../src/models/User');

let server;

beforeAll(async () => {
  await sequelize.sync({ force: true });
  server = app.listen(0);
});

afterAll(async () => {
  await sequelize.close();
  server.close();
});

beforeEach(async () => {
  await User.destroy({ where: {}, truncate: true });
});

// Helper: create a user directly via the register endpoint
async function registerUser(username, email, password, extra = {}) {
  const res = await request(app)
    .post('/api/v1/auth/register')
    .send({ username, email, password, ...extra });
  return res;
}

// Helper: log in and return the response
async function loginUser(username, password, agent) {
  const req = (agent || request(app))
    .post('/api/v1/auth/login')
    .send({ username, password });
  return req;
}

// ─── Test 1: SQL Injection ────────────────────────────────────────────────────

test('1. SQL injection in login returns 401, not 200 or 500', async () => {
  // First create a legit user
  await registerUser('alice', 'alice@example.com', 'safepassword123');

  // Attempt classic SQL injection payload
  const res = await request(app)
    .post('/api/v1/auth/login')
    .send({ username: "' OR '1'='1", password: "' OR '1'='1" });

  // Must NOT succeed (200) and must NOT crash (500)
  expect(res.status).toBe(401);
});

// ─── Test 2: Rate Limiting ────────────────────────────────────────────────────

test('2. Login rate limiter returns 429 after 5 failed attempts', async () => {
  await registerUser('bob', 'bob@example.com', 'correctpass');

  // Make 5 failed attempts (wrong password)
  for (let i = 0; i < 5; i++) {
    await request(app)
      .post('/api/v1/auth/login')
      .send({ username: 'bob', password: 'wrongpassword' });
  }

  // 6th attempt must be rate-limited
  const res = await request(app)
    .post('/api/v1/auth/login')
    .send({ username: 'bob', password: 'wrongpassword' });

  expect(res.status).toBe(429);
});

// ─── Test 3: JWT in httpOnly Cookie ──────────────────────────────────────────

test('3. Successful login sets httpOnly cookie, not body token', async () => {
  await registerUser('carol', 'carol@example.com', 'mypassword99');

  const res = await request(app)
    .post('/api/v1/auth/login')
    .send({ username: 'carol', password: 'mypassword99' });

  expect(res.status).toBe(200);

  // Token must NOT be in the response body
  expect(res.body.token).toBeUndefined();

  // Token must be set as an httpOnly cookie
  const cookies = res.headers['set-cookie'];
  expect(cookies).toBeDefined();
  const tokenCookie = cookies.find(c => c.includes('token='));
  expect(tokenCookie).toBeDefined();
  expect(tokenCookie.toLowerCase()).toContain('httponly');
});

// ─── Test 4: bcrypt Hashing ───────────────────────────────────────────────────

test('4. Passwords are stored as bcrypt hashes, not MD5', async () => {
  await registerUser('dave', 'dave@example.com', 'secretpass');

  const user = await User.findOne({ where: { username: 'dave' } });
  expect(user).not.toBeNull();

  const hash = user.password_hash;

  // bcrypt hashes start with $2b$ or $2a$
  expect(hash).toMatch(/^\$2[ab]\$/);

  // Must NOT be MD5 (32 hex chars)
  expect(hash).not.toMatch(/^[a-f0-9]{32}$/);
});

// ─── Test 5: Session Fixation on Login ───────────────────────────────────────

test('5. Session ID is regenerated after successful login', async () => {
  await registerUser('eve', 'eve@example.com', 'loginpass');

  const agent = request.agent(app);

  // Get a session ID before login
  const preRes = await agent.get('/health');
  const preCookies = preRes.headers['set-cookie'] || [];
  const preSession = preCookies.find(c => c.startsWith('sessionId='));

  // Log in
  const loginRes = await agent
    .post('/api/v1/auth/login')
    .send({ username: 'eve', password: 'loginpass' });

  expect(loginRes.status).toBe(200);

  const postCookies = loginRes.headers['set-cookie'] || [];
  const postSession = postCookies.find(c => c.startsWith('sessionId='));

  // If there was a pre-login session, the post-login session must differ
  if (preSession && postSession) {
    const preVal = preSession.split(';')[0];
    const postVal = postSession.split(';')[0];
    expect(preVal).not.toEqual(postVal);
  } else {
    // A new session must have been set after login
    expect(postSession).toBeDefined();
  }
});

// ─── Test 6: Session Cleared After Logout ────────────────────────────────────

test('6. Session cookie is cleared or regenerated after logout', async () => {
  await registerUser('frank', 'frank@example.com', 'logoutme');

  const agent = request.agent(app);

  // Log in first
  await agent
    .post('/api/v1/auth/login')
    .send({ username: 'frank', password: 'logoutme' });

  // Capture session after login
  const loginCheck = await agent.get('/health');
  const loginCookies = loginCheck.headers['set-cookie'] || [];
  const loginSession = loginCookies.find(c => c.startsWith('sessionId='));

  // Log out
  const logoutRes = await agent.post('/api/v1/auth/logout');
  expect(logoutRes.status).toBe(200);

  // After logout, session should be cleared
  const afterCookies = logoutRes.headers['set-cookie'] || [];
  const expiredSession = afterCookies.find(c =>
    c.startsWith('sessionId=') && c.includes('Expires=Thu, 01 Jan 1970')
  );

  // Either the cookie is expired/cleared, or a new session was created
  const sessionCleared = expiredSession !== undefined;
  const sessionChanged = (() => {
    if (!loginSession) return true;
    const afterSession = afterCookies.find(c => c.startsWith('sessionId='));
    if (!afterSession) return true;
    return loginSession.split(';')[0] !== afterSession.split(';')[0];
  })();

  expect(sessionCleared || sessionChanged).toBe(true);
});

// ─── Test 7: Mass-Assignment Prevention ──────────────────────────────────────

test('7. Register endpoint rejects mass-assignment of isAdmin and role', async () => {
  const res = await registerUser('grace', 'grace@example.com', 'mypassword', {
    isAdmin: true,
    role: 'superuser',
  });

  // Registration itself should succeed (the extra fields are ignored, not rejected with 400)
  expect([200, 201]).toContain(res.status);

  // But the user must NOT have admin privileges
  const user = await User.findOne({ where: { username: 'grace' } });
  expect(user).not.toBeNull();
  expect(user.isAdmin).toBe(false);
  expect(user.role).toBe('user');
});

// ─── Test 8: Backward Compatibility ──────────────────────────────────────────

test('8. All routes accessible under /api/v1/auth/ prefix', async () => {
  await registerUser('henry', 'henry@example.com', 'backcompat');

  // Login route exists
  const loginRes = await request(app)
    .post('/api/v1/auth/login')
    .send({ username: 'henry', password: 'backcompat' });
  expect([200, 401]).toContain(loginRes.status); // any valid auth response

  // Register route exists
  const regRes = await request(app)
    .post('/api/v1/auth/register')
    .send({ username: 'newguy', email: 'newguy@example.com', password: 'newpass' });
  expect([200, 201, 409]).toContain(regRes.status);

  // Logout route exists
  const logoutRes = await request(app).post('/api/v1/auth/logout');
  expect([200, 302]).toContain(logoutRes.status);
});
