const express = require('express');
const cors = require('cors');
const multer = require('multer');
const { Pool } = require('pg');
const AWS = require('aws-sdk');
require('dotenv').config();

const app = express();
const port = process.env.PORT || 3001;

// Database connection
const pool = new Pool({
  connectionString: process.env.DATABASE_URL
});

// AWS S3 setup (LocalStack) - commented out for now
/*
const s3 = new AWS.S3({
  region: process.env.AWS_REGION,
  accessKeyId: process.env.AWS_ACCESS_KEY_ID,
  secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY,
  endpoint: process.env.AWS_ENDPOINT_URL,
  s3ForcePathStyle: true
});
*/

// Multer for file uploads
const upload = multer({ 
  storage: multer.memoryStorage(),
  limits: { fileSize: 100 * 1024 * 1024 }
});

app.use(cors());
app.use(express.json());

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
    res.json(result.rows);
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
    
    // Skip S3 URL generation for now
    // recording.video_url = 'placeholder-url';
    
    res.json(recording);
  } catch (error) {
    console.error('Error fetching recording:', error);
    res.status(500).json({ error: 'Failed to fetch recording' });
  }
});

// Upload recording (modified to skip S3)
app.post('/api/recordings', upload.single('video'), async (req, res) => {
  try {
    const { title, description, tags, creator, duration } = req.body;
    const videoFile = req.file;
    
    if (!title || !videoFile) {
      return res.status(400).json({ error: 'Title and video file are required' });
    }
    
    // Skip S3 upload - just save metadata
    const s3Key = `temp-recording-${Date.now()}.webm`;
    
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
      s3Key,
      videoFile.size,
      videoFile.mimetype
    ]);
    
    res.status(201).json(result.rows[0]);
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
    
    // Skip S3 deletion for now
    
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