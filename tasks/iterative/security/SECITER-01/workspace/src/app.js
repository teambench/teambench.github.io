'use strict';

const express = require('express');
const session = require('express-session');
const authRouter = require('./auth/login');

const app = express();

app.use(express.json());
app.use(express.urlencoded({ extended: false }));

// Session middleware — already configured, do not change.
app.use(session({
  secret: process.env.SESSION_SECRET || 'test-session-secret',
  resave: false,
  saveUninitialized: true,
  name: 'sessionId',
  cookie: {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    maxAge: 60 * 60 * 1000, // 1 hour
  },
}));

// Backward compat requirement: all auth routes under /api/v1/auth
app.use('/api/v1/auth', authRouter);

// Health check
app.get('/health', (req, res) => res.json({ status: 'ok' }));

module.exports = app;
