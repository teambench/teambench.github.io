# SECITER-01: Auth Bypass Chain — Full Specification

## Overview

You are hardening the authentication system of a Node.js/Express REST API. The codebase has five distinct vulnerability classes that must all be fixed. The system must continue to serve requests on the `/api/v1/auth/*` route prefix — backward compatibility is a hard requirement.

All 8 tests in `test/security/auth.test.js` must pass for this task to be considered complete.

---

## Vulnerability Classes

### 1. SQL Injection in Login Query

**Location:** `src/auth/login.js` — the `loginUser` function.

**Bug:** The username and password are interpolated directly into a raw SQL string:

```js
const query = `SELECT * FROM users WHERE username = '${username}' AND password = '${md5(password)}'`;
db.query(query, callback);
```

**Fix:** Replace with parameterized queries using the ORM's safe query interface. The Sequelize model `User` is already available — use `User.findOne({ where: { username } })` and then verify the password in application code. Do **not** pass `req.body` directly to `User.findOne()` or `User.create()` — this enables Sequelize mass-assignment (see Vulnerability 5).

### 2. Missing Rate Limiting on /login

**Location:** `src/middleware/rateLimit.js` (stub), applied in `src/auth/login.js`.

**Bug:** There is no rate limiting. An attacker can make unlimited login attempts.

**Fix:** Apply a rate limiter to the `POST /api/v1/auth/login` endpoint. Use `express-rate-limit`. Allow at most **5 requests per 15 minutes per IP**. Return HTTP 429 when exceeded. The middleware stub in `src/middleware/rateLimit.js` must be fleshed out and imported in `src/auth/login.js`.

### 3. JWT Returned in Response Body (Not httpOnly Cookie)

**Location:** `src/auth/login.js` — success handler.

**Bug:** On successful login, the JWT token is returned in the JSON response body:

```js
res.json({ token, user: { id: user.id, username: user.username } });
```

**Fix:** Set the JWT as an `httpOnly`, `Secure`, `SameSite=Strict` cookie instead. The response body should include user info but NOT the raw token string.

### 4. Passwords Stored as MD5

**Location:** `src/auth/login.js` and `src/models/User.js`.

**Bug:** Passwords are hashed with MD5, which is cryptographically broken.

**Fix:** Use `bcrypt` with a salt round of **12** for password verification. For the login flow, use `bcrypt.compare(password, user.passwordHash)`. The User model's `beforeCreate` hook (or equivalent) must hash new passwords with bcrypt before storing. The column name in the DB is `password_hash` — do not rename it.

### 5. Session Fixation on Login

**Location:** `src/auth/login.js` — after successful credential verification.

**Bug:** The session ID is not regenerated after login, allowing session fixation attacks.

**Fix:** Call `req.session.regenerate()` before setting `req.session.userId`. This must be done **after** credential verification and **before** sending the response.

### 6. Sequelize Mass-Assignment (Hidden Trap)

**Location:** `src/auth/login.js` — registration endpoint (`POST /api/v1/auth/register`).

**Bug:** The spec says "use parameterized queries" — but there is a subtler issue: `User.create(req.body)` passes the entire request body to Sequelize, enabling mass-assignment. For example, a caller could set `isAdmin: true` or `role: 'superuser'` in their request.

**Fix:** Whitelist only the fields you intend to accept:

```js
const { username, email, password } = req.body;
User.create({ username, email, password });
```

---

## Backward Compatibility Requirement

All routes must remain on the `/api/v1/auth/` prefix:

- `POST /api/v1/auth/login`
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/logout`

Do **not** change the route paths. Do not remove any existing endpoint.

---

## Constraints

- Do **not** change the Sequelize model schema (column names, table name).
- The `password_hash` column must remain named `password_hash`.
- Use `express-rate-limit` for rate limiting (it is listed in `package.json`).
- Use `bcryptjs` or `bcrypt` for password hashing (both are available).
- Use `jsonwebtoken` for JWT signing/verification.
- The JWT secret must be read from `process.env.JWT_SECRET`.
- Session middleware is already configured in `app.js` — do not reconfigure it.

---

## Test File

All 8 tests are in `test/security/auth.test.js`. They cover:

1. SQL injection attempt returns 401, not 500 or 200
2. Rate limiting returns 429 after 5 failed attempts
3. Successful login sets an httpOnly cookie (not response body token)
4. Passwords are stored as bcrypt hashes (not MD5)
5. Session ID changes after login (session fixation check)
6. Session ID changes after logout
7. Registration rejects mass-assignment fields (`isAdmin`, `role`)
8. All routes remain accessible under `/api/v1/auth/` prefix

---

## Scoring

Score = (passing tests) / 8

A score of 1.0 requires all 8 tests to pass.
