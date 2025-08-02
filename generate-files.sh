#!/bin/bash

echo "🚀 Generating all Knowledge Harvest files..."

# Create directory structure
mkdir -p docs services web/src web/public

echo "📁 Created directory structure"

# =============================================================================
# DOCUMENTATION FILES
# =============================================================================

cat > docs/mvp-definition.md << 'EOF'
# Knowledge Harvest MVP Definition

## Executive Summary
Focus on proving core value through screen recording knowledge capture before investing in complex AI and microservices architecture.

## MVP Scope: Screen Recording Knowledge Capture

### Core Value Proposition
Enable SMEs to capture and share tacit knowledge through guided screen recordings with voice narration.

### MVP Features

#### 1. Screen Recording Capture
- Browser-based screen recording (WebRTC)
- Simultaneous audio capture
- Recording length limit: 15 minutes
- Basic recording controls (start/stop/pause)

#### 2. Simple Upload & Storage
- File upload to LocalStack S3
- Basic metadata capture (title, date, creator)
- Simple file management

#### 3. Basic Playback
- Web-based video player
- Timestamp navigation
- Download capability

#### 4. Minimal Organization
- Tag-based categorization
- Search by title/tags
- Creator filtering

## Technical Implementation

### Stack
- **Frontend**: React with WebRTC API
- **Backend**: Node.js/Express
- **Database**: PostgreSQL
- **Storage**: LocalStack S3 (development)
- **Deployment**: Docker Compose

### Success Criteria
- 10+ recordings created by 3+ SMEs
- Average recording length: 5-10 minutes
- 80% completion rate for recordings started

### Timeline (5 weeks)
- **Week 1-2**: Core screen recording functionality
- **Week 3**: Upload and storage system
- **Week 4**: Playback and basic organization
- **Week 5**: Testing and user feedback
EOF

cat > docs/development-setup.md << 'EOF'
# Development Setup Instructions

## Prerequisites
- Node.js 18+ and npm
- Docker Desktop
- Git

## Quick Start

```bash
git clone https://github.com/cwarloe/knowledge-harvest.git
cd knowledge-harvest
chmod +x generate-files.sh
./generate-files.sh
./setup.sh
```

## Access Application
- Frontend: http://localhost:3000
- API: http://localhost:3001
- Database: localhost:5432

## Development Commands
```bash
# View logs
docker-compose logs -f api
docker-compose logs -f web

# Stop services
docker-compose down

# Restart services
docker-compose up -d
```
EOF

# =============================================================================
# BACKEND FILES
# =============================================================================

cat > services/package.json << 'EOF'
{
  "name": "knowledge-harvest-api",
  "version": "1.0.0",
  "description": "Backend API for Knowledge Harvest",
  "main": "server.js",
  "scripts": {
    "start": "node server.js",
    "dev": "nodemon server.js",
    "test": "jest"
  },
"dependencies": {
  "express": "^4.18.2",
  "cors": "^2.8.5",
  "multer": "^1.4.5-lts.1",
  "pg": "^8.11.0",
  "aws-sdk": "^2.1470.0",
  "dotenv": "^16.3.1"
}
  "devDependencies": {
    "nodemon": "^2.0.20",
    "jest": "^29.3.1",
    "supertest": "^6.3.3"
  },
  "keywords": ["knowledge-management", "screen-recording"],
  "author": "Knowledge Harvest Team",
  "license": "MIT"
}
EOF

cat > services/.env << 'EOF'
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/knowledge_harvest
AWS_S3_BUCKET=knowledge-harvest-dev
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
AWS_ENDPOINT_URL=http://localstack:4566
PORT=3001
EOF

cat > services/schema.sql << 'EOF'
-- Database schema for Knowledge Harvest
CREATE TABLE recordings (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    tags TEXT[] DEFAULT '{}',
    creator VARCHAR(100) NOT NULL DEFAULT 'Anonymous',
    duration INTERVAL,
    s3_key VARCHAR(500) NOT NULL,
    file_size BIGINT NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX idx_recordings_creator ON recordings(creator);
CREATE INDEX idx_recordings_created_at ON recordings(created_at DESC);
CREATE INDEX idx_recordings_tags ON recordings USING GIN(tags);

-- Insert sample data
INSERT INTO recordings (title, description, tags, creator, duration, s3_key, file_size, mime_type)
VALUES 
    (
        'API Integration Walkthrough',
        'Step-by-step guide for integrating external APIs',
        ARRAY['API', 'React', 'Integration'],
        'Sarah Chen',
        INTERVAL '8 minutes 42 seconds',
        'recordings/sample-api-walkthrough.webm',
        15728640,
        'video/webm'
    ),
    (
        'Security Onion Hunt Techniques',
        'Advanced threat hunting using custom Kibana queries',
        ARRAY['Security', 'Hunting', 'Kibana', 'SOC'],
        'Rachel Martinez',
        INTERVAL '12 minutes 30 seconds',
        'recordings/sample-security-hunt.webm',
        22456789,
        'video/webm'
    );
EOF

cat > services/server.js << 'EOF'
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

// AWS S3 setup (LocalStack)
const s3 = new AWS.S3({
  region: process.env.AWS_REGION,
  accessKeyId: process.env.AWS_ACCESS_KEY_ID,
  secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY,
  endpoint: process.env.AWS_ENDPOINT_URL,
  s3ForcePathStyle: true
});

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
    
    // Generate presigned URL for video access
    if (recording.s3_key) {
      const signedUrl = s3.getSignedUrl('getObject', {
        Bucket: process.env.AWS_S3_BUCKET,
        Key: recording.s3_key,
        Expires: 3600
      });
      recording.video_url = signedUrl;
    }
    
    res.json(recording);
  } catch (error) {
    console.error('Error fetching recording:', error);
    res.status(500).json({ error: 'Failed to fetch recording' });
  }
});

// Upload recording
app.post('/api/recordings', upload.single('video'), async (req, res) => {
  try {
    const { title, description, tags, creator, duration } = req.body;
    const videoFile = req.file;
    
    if (!title || !videoFile) {
      return res.status(400).json({ error: 'Title and video file are required' });
    }
    
    // Upload to S3
    const s3Key = `recordings/${Date.now()}-${videoFile.originalname}`;
    const uploadParams = {
      Bucket: process.env.AWS_S3_BUCKET,
      Key: s3Key,
      Body: videoFile.buffer,
      ContentType: videoFile.mimetype
    };
    
    await s3.upload(uploadParams).promise();
    
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
    
    const s3Key = selectResult.rows[0].s3_key;
    
    // Delete from S3
    if (s3Key) {
      await s3.deleteObject({
        Bucket: process.env.AWS_S3_BUCKET,
        Key: s3Key
      }).promise();
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
EOF

cat > services/Dockerfile << 'EOF'
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 3001
CMD ["npm", "run", "dev"]
EOF

# =============================================================================
# FRONTEND FILES
# =============================================================================

cat > web/package.json << 'EOF'
{
  "name": "knowledge-harvest-web",
  "version": "0.1.0",
  "private": true,
  "dependencies": {
    "@testing-library/jest-dom": "^5.16.4",
    "@testing-library/react": "^13.3.0",
    "@testing-library/user-event": "^13.5.0",
    "lucide-react": "^0.263.1",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-scripts": "5.0.1",
    "web-vitals": "^2.1.4"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  },
  "eslintConfig": {
    "extends": [
      "react-app",
      "react-app/jest"
    ]
  },
  "browserslist": {
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  }
}
EOF

cat > web/public/index.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="theme-color" content="#000000" />
    <meta name="description" content="Knowledge Harvest - Capture tacit knowledge through screen recordings" />
    <title>Knowledge Harvest</title>
    <script src="https://cdn.tailwindcss.com"></script>
  </head>
  <body>
    <noscript>You need to enable JavaScript to run this app.</noscript>
    <div id="root"></div>
  </body>
</html>
EOF

cat > web/src/index.js << 'EOF'
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
EOF

cat > web/src/App.js << 'EOF'
import React, { useState, useRef, useCallback, useEffect } from 'react';
import { Play, Square, Pause, Download, Upload, Search, Filter, AlertCircle } from 'lucide-react';

const KnowledgeHarvestApp = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [recordedBlob, setRecordedBlob] = useState(null);
  const [recordings, setRecordings] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [currentView, setCurrentView] = useState('browse');
  const [recordingTime, setRecordingTime] = useState(0);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedTags, setSelectedTags] = useState([]);
  const [showMetadataForm, setShowMetadataForm] = useState(false);
  const [metadata, setMetadata] = useState({ title: '', description: '', tags: '' });
  const [uploading, setUploading] = useState(false);

  const mediaRecorderRef = useRef(null);
  const streamRef = useRef(null);
  const intervalRef = useRef(null);
  const chunksRef = useRef([]);

  const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:3001';

  useEffect(() => {
    fetchRecordings();
  }, []);

  const fetchRecordings = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/api/recordings`);
      if (!response.ok) throw new Error('Failed to fetch recordings');
      const data = await response.json();
      setRecordings(data);
    } catch (err) {
      setError('Failed to load recordings: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const startRecording = useCallback(async () => {
    try {
      setError(null);
      const stream = await navigator.mediaDevices.getDisplayMedia({
        video: { mediaSource: 'screen' },
        audio: true
      });
      
      streamRef.current = stream;
      chunksRef.current = [];
      
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };
      
      mediaRecorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'video/webm' });
        setRecordedBlob(blob);
        setShowMetadataForm(true);
      };
      
      mediaRecorder.start();
      setIsRecording(true);
      setRecordingTime(0);
      
      intervalRef.current = setInterval(() => {
        setRecordingTime(prev => {
          if (prev >= 900) {
            stopRecording();
            return prev;
          }
          return prev + 1;
        });
      }, 1000);
      
    } catch (error) {
      setError('Error accessing screen: ' + error.message);
    }
  }, []);

  const pauseRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      if (isPaused) {
        mediaRecorderRef.current.resume();
        intervalRef.current = setInterval(() => {
          setRecordingTime(prev => prev + 1);
        }, 1000);
      } else {
        mediaRecorderRef.current.pause();
        clearInterval(intervalRef.current);
      }
      setIsPaused(!isPaused);
    }
  }, [isRecording, isPaused]);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      streamRef.current?.getTracks().forEach(track => track.stop());
      clearInterval(intervalRef.current);
      setIsRecording(false);
      setIsPaused(false);
    }
  }, [isRecording]);

  const uploadRecording = async () => {
    if (!recordedBlob || !metadata.title.trim()) {
      setError('Title is required');
      return;
    }

    try {
      setUploading(true);
      setError(null);

      const formData = new FormData();
      formData.append('video', recordedBlob, 'recording.webm');
      formData.append('title', metadata.title);
      formData.append('description', metadata.description);
      formData.append('tags', metadata.tags);
      formData.append('creator', 'Current User');
      formData.append('duration', formatTime(recordingTime));

      const response = await fetch(`${API_BASE}/api/recordings`, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error('Upload failed: ' + response.statusText);
      }

      const newRecording = await response.json();
      setRecordings(prev => [newRecording, ...prev]);
      
      setMetadata({ title: '', description: '', tags: '' });
      setShowMetadataForm(false);
      setRecordedBlob(null);
      setRecordingTime(0);
      setCurrentView('browse');
      
    } catch (err) {
      setError('Upload failed: ' + err.message);
    } finally {
      setUploading(false);
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const downloadRecording = async (recording) => {
    try {
      const response = await fetch(`${API_BASE}/api/recordings/${recording.id}`);
      if (!response.ok) throw new Error('Failed to get download URL');
      
      const data = await response.json();
      if (data.video_url) {
        const a = document.createElement('a');
        a.href = data.video_url;
        a.download = `${recording.title.replace(/[^a-z0-9]/gi, '_')}.webm`;
        a.click();
      }
    } catch (err) {
      setError('Download failed: ' + err.message);
    }
  };

  const filteredRecordings = recordings.filter(recording => {
    const matchesSearch = recording.title?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         recording.creator?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesTags = selectedTags.length === 0 || 
                       selectedTags.some(tag => recording.tags?.includes(tag));
    return matchesSearch && matchesTags;
  });

  const allTags = [...new Set(recordings.flatMap(r => r.tags || []))];

  if (showMetadataForm) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-2xl mx-auto bg-white rounded-lg shadow-lg p-6">
          <h2 className="text-2xl font-bold mb-6">Add Recording Details</h2>
          
          {error && (
            <div className="mb-4 p-3 bg-red-100 border border-red-300 rounded-lg flex items-center gap-2">
              <AlertCircle size={20} className="text-red-600" />
              <span className="text-red-800">{error}</span>
            </div>
          )}
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">Title *</label>
              <input
                type="text"
                value={metadata.title}
                onChange={(e) => setMetadata(prev => ({ ...prev, title: e.target.value }))}
                className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500"
                placeholder="Descriptive title for your recording"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-2">Description</label>
              <textarea
                value={metadata.description}
                onChange={(e) => setMetadata(prev => ({ ...prev, description: e.target.value }))}
                className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500"
                rows="3"
                placeholder="Brief description of what you recorded"
                maxLength="500"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-2">Tags</label>
              <input
                type="text"
                value={metadata.tags}
                onChange={(e) => setMetadata(prev => ({ ...prev, tags: e.target.value }))}
                className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500"
                placeholder="Comma-separated tags (e.g., API, React, Tutorial)"
              />
            </div>
            
            <div className="flex gap-3 pt-4">
              <button
                onClick={uploadRecording}
                disabled={uploading}
                className="flex-1 bg-blue-600 text-white py-3 px-6 rounded-lg hover:bg-blue-700 font-medium disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {uploading ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    Uploading...
                  </>
                ) : (
                  <>
                    <Upload size={20} />
                    Save Recording
                  </>
                )}
              </button>
              <button
                onClick={() => setShowMetadataForm(false)}
                disabled={uploading}
                className="px-6 py-3 border rounded-lg hover:bg-gray-50 disabled:opacity-50"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-gray-900">Knowledge Harvest</h1>
            <nav className="flex gap-4">
              <button
                onClick={() => setCurrentView('record')}
                className={`px-4 py-2 rounded-lg font-medium ${currentView === 'record' ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:text-gray-900'}`}
              >
                Record
              </button>
              <button
                onClick={() => setCurrentView('browse')}
                className={`px-4 py-2 rounded-lg font-medium ${currentView === 'browse' ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:text-gray-900'}`}
              >
                Browse
              </button>
            </nav>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {error && !showMetadataForm && (
          <div className="mb-6 p-3 bg-red-100 border border-red-300 rounded-lg flex items-center gap-2">
            <AlertCircle size={20} className="text-red-600" />
            <span className="text-red-800">{error}</span>
            <button 
              onClick={() => setError(null)}
              className="ml-auto text-red-600 hover:text-red-800"
            >
              ×
            </button>
          </div>
        )}

        {currentView === 'record' && (
          <div className="max-w-2xl mx-auto">
            <div className="bg-white rounded-lg shadow-lg p-8 text-center">
              <h2 className="text-2xl font-bold mb-6">Screen Recording</h2>
              
              {!isRecording ? (
                <div>
                  <p className="text-gray-600 mb-6">
                    Click start to begin recording your screen and audio. Maximum duration is 15 minutes.
                  </p>
                  <button
                    onClick={startRecording}
                    className="bg-red-600 hover:bg-red-700 text-white px-8 py-4 rounded-lg font-medium flex items-center gap-2 mx-auto"
                  >
                    <Play size={20} />
                    Start Recording
                  </button>
                </div>
              ) : (
                <div className="space-y-6">
                  <div className="text-4xl font-mono text-red-600">
                    {formatTime(recordingTime)}
                  </div>
                  
                  {recordingTime >= 780 && (
                    <div className="bg-orange-100 border border-orange-300 rounded-lg p-3">
                      <p className="text-orange-800">Recording will stop automatically at 15 minutes</p>
                    </div>
                  )}
                  
                  <div className="flex gap-4 justify-center">
                    <button
                      onClick={pauseRecording}
                      className="bg-yellow-600 hover:bg-yellow-700 text-white px-6 py-3 rounded-lg font-medium flex items-center gap-2"
                    >
                      <Pause size={20} />
                      {isPaused ? 'Resume' : 'Pause'}
                    </button>
                    <button
                      onClick={stopRecording}
                      className="bg-gray-600 hover:bg-gray-700 text-white px-6 py-3 rounded-lg font-medium flex items-center gap-2"
                    >
                      <Square size={20} />
                      Stop Recording
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {currentView === 'browse' && (
          <div>
            <div className="flex gap-4 mb-6">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-3 text-gray-400" size={20} />
                <input
                  type="text"
                  placeholder="Search recordings..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div className="relative">
                <select
                  value={selectedTags[0] || ''}
                  onChange={(e) => setSelectedTags(e.target.value ? [e.target.value] : [])}
                  className="pl-10 pr-8 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 appearance-none bg-white"
                >
                  <option value="">All Tags</option>
                  {allTags.map(tag => (
                    <option key={tag} value={tag}>{tag}</option>
                  ))}
                </select>
                <Filter className="absolute left-3 top-3 text-gray-400 pointer-events-none" size={20} />
              </div>
            </div>

            {loading && (
              <div className="flex justify-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              </div>
            )}

            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {filteredRecordings.map(recording => (
                <div key={recording.id} className="bg-white rounded-lg shadow-lg overflow-hidden">
                  <div className="aspect-video bg-gray-200 flex items-center justify-center">
                    <Play size={48} className="text-gray-400" />
                  </div>
                  <div className="p-4">
                    <h3 className="font-semibold text-lg mb-2">{recording.title}</h3>
                    <p className="text-gray-600 text-sm mb-3">
                      By {recording.creator} • {new Date(recording.created_at).toLocaleDateString()} • {recording.duration || 'Unknown'}
                    </p>
                    <div className="flex flex-wrap gap-1 mb-4">
                      {(recording.tags || []).map(tag => (
                        <span key={tag} className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs">
                          {tag}
                        </span>
                      ))}
                    </div>
                    <div className="flex gap-2">
                      <button className="flex-1 bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700 flex items-center justify-center gap-2">
                        <Play size={16} />
                        Watch
                      </button>
                      <button
                        onClick={() => downloadRecording(recording)}
                        className="p-2 border rounded hover:bg-gray-50"
                      >
                        <Download size={16} />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {!loading && filteredRecordings.length === 0 && (
              <div className="text-center py-12">
                <p className="text-gray-500 text-lg">No recordings found</p>
                <button
                  onClick={() => setCurrentView('record')}
                  className="mt-4 text-blue-600 hover:text-blue-700 font-medium"
                >
                  Create your first recording
                </button>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
};

export default KnowledgeHarvestApp;
EOF

cat > web/Dockerfile << 'EOF'
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 3000
CMD ["npm", "start"]
EOF

# =============================================================================
# DOCKER FILES
# =============================================================================

cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: knowledge_harvest
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./services/schema.sql:/docker-entrypoint-initdb.d/schema.sql

  api:
    build:
      context: ./services
      dockerfile: Dockerfile
    ports:
      - "3001:3001"
    environment:
      DATABASE_URL: postgresql://postgres:postgres@postgres:5432/knowledge_harvest
      AWS_S3_BUCKET: knowledge-harvest-dev
      AWS_REGION: us-east-1
      AWS_ACCESS_KEY_ID: test
      AWS_SECRET_ACCESS_KEY: test
      AWS_ENDPOINT_URL: http://localstack:4566
      PORT: 3001
    volumes:
      - ./services:/app
      - /app/node_modules
    depends_on:
      - postgres
      - localstack
    command: npm run dev

  web:
    build:
      context: ./web
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      REACT_APP_API_URL: http://localhost:3001
    volumes:
      - ./web:/app
      - /app/node_modules
    command: npm start

  localstack:
    image: localstack/localstack:latest
    ports:
      - "4566:4566"
    environment:
      SERVICES: s3
      DEBUG: 1
    volumes:
      - localstack_data:/tmp/localstack

volumes:
  postgres_data:
  localstack_data:
EOF

# =============================================================================
# SETUP SCRIPT
# =============================================================================

cat > setup.sh << 'EOF'
#!/bin/bash
echo "🚀 Setting up Knowledge Harvest development environment..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop."
    exit 1
fi

# Install backend dependencies
echo "📦 Installing backend dependencies..."
cd services && npm install && cd ..

# Install frontend dependencies  
echo "📦 Installing frontend dependencies..."
cd web && npm install && cd ..

# Build and start all services
echo "🏗️  Building containers..."
docker-compose build

echo "🚀 Starting services..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 15

# Setup S3 bucket in LocalStack
echo "📦 Setting up S3 bucket..."
docker-compose exec -T localstack awslocal s3 mb s3://knowledge-harvest-dev

echo "✅ Setup complete!"
echo ""
echo "🌐 Access your application:"
echo "  Frontend: http://localhost:3000"
echo "  API: http://localhost:3001/api/health"
echo "  Database: localhost:5432"
echo ""
echo "🛠️  Development commands:"
echo "  docker-compose logs -f api    # View API logs"
echo "  docker-compose logs -f web    # View React logs"
echo "  docker-compose down           # Stop all services"
echo ""
EOF

chmod +x setup.sh

# =============================================================================
# README
# =============================================================================

cat > README.md << 'EOF'
# Knowledge Harvest

Capture and share tacit subject-matter-expert knowledge through screen recordings.

## Quick Start

```bash
git clone https://github.com/cwarloe/knowledge-harvest.git
cd knowledge-harvest
chmod +x generate-files.sh
./generate-files.sh
./setup.sh
```

Access at: http://localhost:3000

## Features

- WebRTC screen recording with audio
- File upload to LocalStack S3
- PostgreSQL database
- Search and tag filtering
- Docker development environment

## Development

```bash
# View logs
docker-compose logs -f api
docker-compose logs -f web

# Stop services
docker-compose down

# Restart
docker-compose up -d
```

## Architecture

- **Frontend**: React with Tailwind CSS
- **Backend**: Node.js/Express API
- **Database**: PostgreSQL
- **Storage**: LocalStack S3 (development)
- **Deployment**: Docker Compose
EOF

echo ""
echo "✅ All files generated successfully!"
echo ""
echo "📁 Created files:"
echo "  📄 README.md"
echo "  📄 docker-compose.yml"
echo "  📄 setup.sh"
echo "  📁 docs/"
echo "    📄 mvp-definition.md"
echo "    📄 development-setup.md"
echo "  📁 services/"
echo "    📄 package.json"
echo "    📄 server.js"
echo "    📄 schema.sql"
echo "    📄 .env"
echo "    📄 Dockerfile"
echo "  📁 web/"
echo "    📄 package.json"
echo "    📄 src/App.js"
echo "    📄 src/index.js"
echo "    📄 public/index.html"
echo "    📄 Dockerfile"
echo ""
echo "🚀 Next steps:"
echo "  1. Run: ./setup.sh"
echo "  2. Open: http://localhost:3000"
echo ""