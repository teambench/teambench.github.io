'use strict';

const express = require('express');
const { authenticateRequest } = require('./auth/middleware');
const uploadRouter = require('./upload/handler');

const app = express();
app.use(express.json());

// Upload routes (fileupload middleware applied inside the router)
app.use('/', uploadRouter);

// Protected route: requires valid JWT
app.get('/api/protected', authenticateRequest, (req, res) => {
  res.json({ message: 'Access granted', user: req.user });
});

// Public route
app.get('/api/public', (req, res) => {
  res.json({ message: 'Public endpoint' });
});

// Health check
app.get('/health', (req, res) => res.json({ status: 'ok' }));

module.exports = app;
