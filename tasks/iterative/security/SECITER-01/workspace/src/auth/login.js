'use strict';

const express = require('express');
const jwt = require('jsonwebtoken');
const md5 = require('md5');
const { User, sequelize } = require('../models/User');

const router = express.Router();

const JWT_SECRET = process.env.JWT_SECRET || 'test-secret';

// VULNERABILITY 2: No rate limiting applied to login endpoint.
// The rateLimit middleware exists as a stub but is not used here.
// Fix: import and apply the rate limiter from ../middleware/rateLimit

// VULNERABILITY 1: SQL injection via raw string interpolation.
// The login query builds a raw SQL string using template literals.
// Fix: use User.findOne({ where: { username } }) and verify password in app code.
async function findUserByCredentials(username, password) {
  // Raw SQL with string interpolation — injectable!
  const rawQuery = `SELECT * FROM users WHERE username = '${username}' AND password_hash = '${md5(password)}'`;
  const [results] = await sequelize.query(rawQuery);
  return results[0] || null;
}

// POST /api/v1/auth/login
router.post('/login', async (req, res) => {
  try {
    const { username, password } = req.body;

    if (!username || !password) {
      return res.status(400).json({ error: 'Username and password required' });
    }

    // VULNERABILITY 1: SQL injection inside findUserByCredentials
    const user = await findUserByCredentials(username, password);

    if (!user) {
      return res.status(401).json({ error: 'Invalid credentials' });
    }

    // VULNERABILITY 5: Session fixation — session ID not regenerated after login.
    // Fix: call req.session.regenerate() here before setting session data.
    req.session.userId = user.id;
    req.session.username = user.username;

    const token = jwt.sign(
      { sub: user.id, username: user.username, role: user.role },
      JWT_SECRET,
      { expiresIn: '1h', algorithm: 'HS256' }
    );

    // VULNERABILITY 3: JWT returned in response body instead of httpOnly cookie.
    // Fix: use res.cookie('token', token, { httpOnly: true, secure: true, sameSite: 'strict' })
    //      and do NOT include token in the JSON body.
    return res.json({
      token,
      user: { id: user.id, username: user.username, role: user.role },
    });
  } catch (err) {
    console.error('Login error:', err);
    return res.status(500).json({ error: 'Internal server error' });
  }
});

// POST /api/v1/auth/register
router.post('/register', async (req, res) => {
  try {
    // VULNERABILITY 6: Mass assignment — req.body passed directly to User.create().
    // An attacker can set isAdmin: true or role: 'superuser' in the request body.
    // Fix: destructure only { username, email, password } from req.body.
    //
    // Note: we map password -> password_hash so the beforeCreate hook picks it up.
    // The mass-assignment bug is that ALL of req.body is spread in (including isAdmin, role).
    const { username, email, password, ...extra } = req.body;
    const newUser = await User.create({
      username,
      email,
      password_hash: password, // beforeCreate will hash this
      // VULNERABILITY: spread the rest of req.body including isAdmin, role, etc.
      ...extra,
    });

    return res.status(201).json({
      user: { id: newUser.id, username: newUser.username, email: newUser.email },
    });
  } catch (err) {
    if (err.name === 'SequelizeUniqueConstraintError') {
      return res.status(409).json({ error: 'Username or email already exists' });
    }
    if (err.name === 'SequelizeValidationError') {
      return res.status(400).json({ error: err.message });
    }
    console.error('Register error:', err);
    return res.status(500).json({ error: 'Internal server error' });
  }
});

// POST /api/v1/auth/logout
router.post('/logout', (req, res) => {
  // VULNERABILITY 5b: session not regenerated on logout either.
  // Fix: call req.session.regenerate() or req.session.destroy() before responding.
  req.session.destroy((err) => {
    if (err) {
      return res.status(500).json({ error: 'Could not log out' });
    }
    // VULNERABILITY 3b: no cookie cleared on logout.
    return res.json({ message: 'Logged out' });
  });
});

module.exports = router;
