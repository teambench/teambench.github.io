'use strict';

const express = require('express');
const path = require('path');
const { corsMiddleware, securityHeaders } = require('./middleware/security');

const app = express();

app.use(express.json());
app.use(corsMiddleware);
app.use(securityHeaders);

// Serve index.html with nonce substitution
app.get('/', (req, res) => {
  const fs = require('fs');
  const htmlPath = path.join(__dirname, '..', 'public', 'index.html');
  let html = fs.readFileSync(htmlPath, 'utf8');

  // Replace {{NONCE}} placeholder with res.locals.nonce (set by securityHeaders)
  const nonce = res.locals.nonce || '';
  html = html.replace(/\{\{NONCE\}\}/g, nonce);

  res.setHeader('Content-Type', 'text/html; charset=utf-8');
  res.send(html);
});

// Sample API endpoint
app.get('/api/data', (req, res) => {
  res.json({ message: 'Hello from the API', timestamp: Date.now() });
});

// Health check
app.get('/health', (req, res) => res.json({ status: 'ok' }));

module.exports = app;
