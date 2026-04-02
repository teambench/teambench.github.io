'use strict';

const express = require('express');
const fileUpload = require('express-fileupload');
const path = require('path');
const fs = require('fs');

const router = express.Router();

const UPLOAD_DIR = path.join(__dirname, '..', '..', 'uploads');

// Ensure upload directory exists
if (!fs.existsSync(UPLOAD_DIR)) {
  fs.mkdirSync(UPLOAD_DIR, { recursive: true });
}

// VULNERABILITY: express-fileupload 1.2.1 has path traversal (CVE-2020-35613).
// Fix 1: Upgrade to >= 1.4.0 in package.json.
// Fix 2: Add { safeFileNames: true, preserveExtension: true } to the middleware options.
// Fix 3: Use path.basename() to sanitize the filename before calling .mv().
router.use(fileUpload({
  // Missing safeFileNames and preserveExtension options
  limits: { fileSize: 5 * 1024 * 1024 }, // 5MB limit
}));

/**
 * POST /upload
 * Accept a single file upload named "upload".
 */
router.post('/upload', async (req, res) => {
  if (!req.files || !req.files.upload) {
    return res.status(400).json({ error: 'No file uploaded. Use field name "upload".' });
  }

  const uploadedFile = req.files.upload;

  // VULNERABILITY: filename not sanitized — allows path traversal
  // e.g., name: "../../etc/passwd" would write outside UPLOAD_DIR
  // Fix: const safeName = path.basename(uploadedFile.name);
  const uploadPath = path.join(UPLOAD_DIR, uploadedFile.name);

  try {
    await uploadedFile.mv(uploadPath);
    return res.json({
      message: 'File uploaded successfully',
      filename: uploadedFile.name,
      size: uploadedFile.size,
      mimetype: uploadedFile.mimetype,
    });
  } catch (err) {
    console.error('Upload error:', err);
    return res.status(500).json({ error: 'Failed to save file' });
  }
});

/**
 * GET /uploads/:filename
 * Serve an uploaded file.
 */
router.get('/uploads/:filename', (req, res) => {
  // VULNERABILITY: filename param not sanitized either
  const filePath = path.join(UPLOAD_DIR, req.params.filename);
  if (!fs.existsSync(filePath)) {
    return res.status(404).json({ error: 'File not found' });
  }
  res.sendFile(filePath);
});

module.exports = router;
