# SECITER-01: Auth Bypass Chain — Executor Brief

## Your Job

Fix the authentication system. There are 8 tests in `test/security/auth.test.js`. Currently 3 pass and 5 fail. Make all 8 pass.

## Files You Need to Touch

| File | What's wrong |
|------|-------------|
| `src/auth/login.js` | SQL injection, MD5 passwords, JWT in body, no rate limit, no session regeneration, mass-assignment on register |
| `src/middleware/rateLimit.js` | Empty stub — needs real implementation |
| `src/models/User.js` | `beforeCreate` hook uses MD5 — needs bcrypt |

## Key Constraints

- **Do not change** the Sequelize schema (column names, table name stay the same)
- **Do not change** route paths — all routes stay under `/api/v1/auth/`
- `password_hash` column name stays as-is
- JWT must be stored in an `httpOnly` cookie, not returned in the response body
- Rate limit: 5 requests / 15 minutes / IP → HTTP 429
- Use bcrypt (salt rounds = 12) for all password operations
- Whitelist fields on `User.create()` — do NOT pass `req.body` directly

## Running Tests

```bash
npm install
npm test
```

The test file is `test/security/auth.test.js`. It uses Jest + supertest.

## Environment

- `JWT_SECRET` — env var for signing tokens (default: `'test-secret'` in test env)
- `SESSION_SECRET` — env var for session middleware
- SQLite in-memory DB used for tests (configured in `src/models/User.js`)

## Note on the ORM

User model uses Sequelize. The `User` model has these fields:
- `id` (INTEGER, PK, autoincrement)
- `username` (STRING, unique)
- `email` (STRING, unique)
- `password_hash` (STRING) — stores the hashed password
- `isAdmin` (BOOLEAN, default false)
- `role` (STRING, default 'user')

The `isAdmin` and `role` fields exist in the schema intentionally — but they must not be settable by end users via the register endpoint.
