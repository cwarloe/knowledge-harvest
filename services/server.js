const express = require('express');
const cors = require('cors');
const multer = require('multer');
const { Pool } = require('pg');
const path = require('path');
const fs = require('fs');
require('dotenv').config();

const app = express();
const port = process.env.PORT || 3001;

// Database connection
const pool = new Pool({
  connectionString: process.env.DATABASE_URL
});

// Ensure uploads directory exists
const uploadsDir = path.join(__dirname, 'uploads');
if (!fs.existsSync(uploadsDir)) {
  fs.mkdirSync(uploadsDir, { recursive: true });
}

// Multer for local file uploads
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, uploadsDir);
  },
  filename: (req, file, cb) => {
    const uniqueName = `recording-${Date.now()}-${Math.random().toString(36).substring(7)}.webm`;
    cb(null, uniqueName);
  }
});

const upload = multer({
  storage: storage,
  limits: { fileSize: 100 * 1024 * 1024 } // 100MB limit
});

app.use(cors());
app.use(express.json());

// Serve uploaded files statically
app.use('/uploads', express.static(uploadsDir));

// Health check
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Get all recordings
app.get('/api/recordings', async (req, res) => {
  try {
    const { search, tag, creator } = req.query;
    let query = 'SELECT * FROM recordings WHERE 1=1';
    const params = [];

    if (search) {
      query += ' AND (title ILIKE $' + (params.length + 1) + ' OR description ILIKE $' + (params.length + 1) + ')';
      params.push(`%${search}%`);
    }

    if (tag) {
      query += ' AND $' + (params.length + 1) + ' = ANY(tags)';
      params.push(tag);
    }

    if (creator) {
      query += ' AND creator = $' + (params.length + 1);
      params.push(creator);
    }

    query += ' ORDER BY created_at DESC';

    const result = await pool.query(query, params);

    // Add video URLs to all recordings
    const recordings = result.rows.map(recording => ({
      ...recording,
      video_url: recording.s3_key ? `/uploads/${recording.s3_key}` : null
    }));

    res.json(recordings);
  } catch (error) {
    console.error('Error fetching recordings:', error);
    res.status(500).json({ error: 'Failed to fetch recordings' });
  }
});

// Get single recording
app.get('/api/recordings/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const result = await pool.query('SELECT * FROM recordings WHERE id = $1', [id]);

    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Recording not found' });
    }

    const recording = result.rows[0];

    // Generate local file URL
    if (recording.s3_key) {
      recording.video_url = `/uploads/${recording.s3_key}`;
    }

    res.json(recording);
  } catch (error) {
    console.error('Error fetching recording:', error);
    res.status(500).json({ error: 'Failed to fetch recording' });
  }
});

// Upload recording (saves to local filesystem)
app.post('/api/recordings', upload.single('video'), async (req, res) => {
  try {
    const { title, description, tags, creator, duration } = req.body;
    const videoFile = req.file;

    if (!title || !videoFile) {
      return res.status(400).json({ error: 'Title and video file are required' });
    }

    // File is already saved by multer, get the filename
    const fileName = videoFile.filename;
    const fileUrl = `/uploads/${fileName}`;

    // Save to database
    const tagsArray = tags ? tags.split(',').map(tag => tag.trim()) : [];
    const insertQuery = `
      INSERT INTO recordings (title, description, tags, creator, duration, s3_key, file_size, mime_type)
      VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
      RETURNING *
    `;

    const result = await pool.query(insertQuery, [
      title,
      description || null,
      tagsArray,
      creator || 'Anonymous',
      duration || null,
      fileName, // Store filename instead of s3_key
      videoFile.size,
      videoFile.mimetype
    ]);

    // Add video URL to response
    const recording = result.rows[0];
    recording.video_url = fileUrl;

    res.status(201).json(recording);
  } catch (error) {
    console.error('Error uploading recording:', error);
    res.status(500).json({ error: 'Failed to upload recording' });
  }
});

// Delete recording
app.delete('/api/recordings/:id', async (req, res) => {
  try {
    const { id } = req.params;

    const selectResult = await pool.query('SELECT s3_key FROM recordings WHERE id = $1', [id]);
    if (selectResult.rows.length === 0) {
      return res.status(404).json({ error: 'Recording not found' });
    }

    const fileName = selectResult.rows[0].s3_key;

    // Delete local file
    if (fileName) {
      const filePath = path.join(uploadsDir, fileName);
      if (fs.existsSync(filePath)) {
        fs.unlinkSync(filePath);
      }
    }

    // Delete from database
    await pool.query('DELETE FROM recordings WHERE id = $1', [id]);

    res.json({ message: 'Recording deleted successfully' });
  } catch (error) {
    console.error('Error deleting recording:', error);
    res.status(500).json({ error: 'Failed to delete recording' });
  }
});

app.listen(port, () => {
  console.log(`Knowledge Harvest API running on port ${port}`);
});