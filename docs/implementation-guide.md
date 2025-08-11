# Knowledge Harvest - Technical Implementation Guide

This guide provides detailed technical instructions for implementing the next critical features of the Knowledge Harvest MVP. It's intended for developers working on the project to ensure consistent implementation and code quality.

## 1. S3 Integration for Video Storage

### Requirements
- Store video recordings in S3 (LocalStack for development)
- Generate signed URLs for video retrieval
- Support for large file uploads (up to 100MB)
- Proper error handling and retry mechanisms

### Implementation Steps

#### 1.1 Update S3 Configuration in server.js
Uncomment and update the S3 configuration in server.js:

```javascript
// AWS S3 setup
const s3 = new AWS.S3({
  region: process.env.AWS_REGION,
  accessKeyId: process.env.AWS_ACCESS_KEY_ID,
  secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY,
  endpoint: process.env.AWS_ENDPOINT_URL,
  s3ForcePathStyle: true
});

// Create bucket if it doesn't exist (for LocalStack)
async function ensureBucketExists() {
  const bucketName = process.env.AWS_S3_BUCKET;
  try {
    await s3.headBucket({ Bucket: bucketName }).promise();
    console.log(`Bucket ${bucketName} exists`);
  } catch (error) {
    if (error.statusCode === 404) {
      console.log(`Creating bucket ${bucketName}`);
      await s3.createBucket({ Bucket: bucketName }).promise();
    } else {
      console.error('Error checking bucket:', error);
      throw error;
    }
  }
}

// Call this function during server startup
ensureBucketExists().catch(console.error);
```

#### 1.2 Implement File Upload to S3
Update the POST /api/recordings endpoint:

```javascript
// Upload recording
app.post('/api/recordings', upload.single('video'), async (req, res) => {
  try {
    const { title, description, tags, creator, duration } = req.body;
    const videoFile = req.file;
    
    if (!title || !videoFile) {
      return res.status(400).json({ error: 'Title and video file are required' });
    }
    
    // Generate a unique S3 key
    const s3Key = `recordings/${Date.now()}-${videoFile.originalname.replace(/[^a-zA-Z0-9.]/g, '-')}`;
    
    // Upload to S3
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
```

#### 1.3 Generate Signed URLs for Video Retrieval
Update the GET /api/recordings/:id endpoint:

```javascript
// Get single recording
app.get('/api/recordings/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const result = await pool.query('SELECT * FROM recordings WHERE id = $1', [id]);
    
    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Recording not found' });
    }
    
    const recording = result.rows[0];
    
    // Generate a signed URL for video access (expires in 1 hour)
    const signedUrlExpireSeconds = 60 * 60;
    const url = s3.getSignedUrl('getObject', {
      Bucket: process.env.AWS_S3_BUCKET,
      Key: recording.s3_key,
      Expires: signedUrlExpireSeconds
    });
    
    recording.video_url = url;
    
    res.json(recording);
  } catch (error) {
    console.error('Error fetching recording:', error);
    res.status(500).json({ error: 'Failed to fetch recording' });
  }
});
```

#### 1.4 Implement Video Deletion
Update the DELETE /api/recordings/:id endpoint:

```javascript
// Delete recording
app.delete('/api/recordings/:id', async (req, res) => {
  try {
    const { id } = req.params;
    
    const selectResult = await pool.query('SELECT s3_key FROM recordings WHERE id = $1', [id]);
    if (selectResult.rows.length === 0) {
      return res.status(404).json({ error: 'Recording not found' });
    }
    
    const { s3_key } = selectResult.rows[0];
    
    // Delete from S3
    await s3.deleteObject({
      Bucket: process.env.AWS_S3_BUCKET,
      Key: s3_key
    }).promise();
    
    // Delete from database
    await pool.query('DELETE FROM recordings WHERE id = $1', [id]);
    
    res.json({ message: 'Recording deleted successfully' });
  } catch (error) {
    console.error('Error deleting recording:', error);
    res.status(500).json({ error: 'Failed to delete recording' });
  }
});
```

## 2. Video Streaming Endpoint

### Requirements
- Support for range requests for efficient video streaming
- Proper content-type and content-length headers
- Error handling for missing files
- Support for different video formats

### Implementation Steps

#### 2.1 Create a Streaming Endpoint

Add a new endpoint for video streaming:

```javascript
// Stream video
app.get('/api/recordings/:id/stream', async (req, res) => {
  try {
    const { id } = req.params;
    const result = await pool.query('SELECT s3_key, mime_type, file_size FROM recordings WHERE id = $1', [id]);
    
    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Recording not found' });
    }
    
    const { s3_key, mime_type, file_size } = result.rows[0];
    
    // Handle range requests
    const range = req.headers.range;
    if (range) {
      const parts = range.replace(/bytes=/, '').split('-');
      const start = parseInt(parts[0], 10);
      const end = parts[1] ? parseInt(parts[1], 10) : file_size - 1;
      const chunkSize = (end - start) + 1;
      
      // Get the specified range from S3
      const params = {
        Bucket: process.env.AWS_S3_BUCKET,
        Key: s3_key,
        Range: `bytes=${start}-${end}`
      };
      
      const s3Stream = s3.getObject(params).createReadStream();
      
      res.writeHead(206, {
        'Content-Range': `bytes ${start}-${end}/${file_size}`,
        'Accept-Ranges': 'bytes',
        'Content-Length': chunkSize,
        'Content-Type': mime_type
      });
      
      s3Stream.pipe(res);
    } else {
      // Get the entire file
      const params = {
        Bucket: process.env.AWS_S3_BUCKET,
        Key: s3_key
      };
      
      const s3Stream = s3.getObject(params).createReadStream();
      
      res.writeHead(200, {
        'Content-Length': file_size,
        'Content-Type': mime_type
      });
      
      s3Stream.pipe(res);
    }
  } catch (error) {
    console.error('Error streaming video:', error);
    res.status(500).json({ error: 'Failed to stream video' });
  }
});
```

## 3. Video Playback Component

### Requirements
- Custom video player with standard controls
- Support for streaming video from the API
- Responsive design for different screen sizes
- Keyboard accessibility

### Implementation Steps

#### 3.1 Create a VideoPlayer Component

Create a new file `src/components/VideoPlayer.js`:

```jsx
import React, { useRef, useState, useEffect } from 'react';
import { Play, Pause, Volume2, VolumeX, Maximize, SkipBack, SkipForward } from 'lucide-react';

const VideoPlayer = ({ videoUrl, title }) => {
  const videoRef = useRef(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [isMuted, setIsMuted] = useState(false);
  const [volume, setVolume] = useState(1);
  const [isFullscreen, setIsFullscreen] = useState(false);
  
  useEffect(() => {
    const video = videoRef.current;
    
    const handleTimeUpdate = () => {
      setCurrentTime(video.currentTime);
    };
    
    const handleLoadedMetadata = () => {
      setDuration(video.duration);
    };
    
    const handlePlay = () => {
      setIsPlaying(true);
    };
    
    const handlePause = () => {
      setIsPlaying(false);
    };
    
    video.addEventListener('timeupdate', handleTimeUpdate);
    video.addEventListener('loadedmetadata', handleLoadedMetadata);
    video.addEventListener('play', handlePlay);
    video.addEventListener('pause', handlePause);
    
    return () => {
      video.removeEventListener('timeupdate', handleTimeUpdate);
      video.removeEventListener('loadedmetadata', handleLoadedMetadata);
      video.removeEventListener('play', handlePlay);
      video.removeEventListener('pause', handlePause);
    };
  }, []);
  
  const togglePlay = () => {
    const video = videoRef.current;
    if (isPlaying) {
      video.pause();
    } else {
      video.play();
    }
  };
  
  const toggleMute = () => {
    const video = videoRef.current;
    video.muted = !isMuted;
    setIsMuted(!isMuted);
  };
  
  const handleVolumeChange = (e) => {
    const newVolume = parseFloat(e.target.value);
    const video = videoRef.current;
    video.volume = newVolume;
    setVolume(newVolume);
    setIsMuted(newVolume === 0);
  };
  
  const handleSeek = (e) => {
    const newTime = parseFloat(e.target.value);
    const video = videoRef.current;
    video.currentTime = newTime;
    setCurrentTime(newTime);
  };
  
  const toggleFullscreen = () => {
    const videoContainer = document.getElementById('video-container');
    
    if (!document.fullscreenElement) {
      videoContainer.requestFullscreen().catch(err => {
        console.error(`Error attempting to enable fullscreen: ${err.message}`);
      });
    } else {
      document.exitFullscreen();
    }
  };
  
  const formatTime = (timeInSeconds) => {
    const minutes = Math.floor(timeInSeconds / 60);
    const seconds = Math.floor(timeInSeconds % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };
  
  const skipForward = () => {
    const video = videoRef.current;
    video.currentTime = Math.min(video.currentTime + 10, duration);
  };
  
  const skipBackward = () => {
    const video = videoRef.current;
    video.currentTime = Math.max(video.currentTime - 10, 0);
  };
  
  return (
    <div id="video-container" className="relative bg-black rounded-lg overflow-hidden">
      <video
        ref={videoRef}
        src={videoUrl}
        className="w-full h-auto"
        playsInline
      />
      
      <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-4">
        <div className="flex items-center mb-2">
          <input
            type="range"
            min="0"
            max={duration || 0}
            value={currentTime}
            onChange={handleSeek}
            className="w-full h-1 bg-gray-400 rounded-full appearance-none cursor-pointer"
            style={{
              background: `linear-gradient(to right, white ${(currentTime / duration) * 100}%, gray ${(currentTime / duration) * 100}%)`
            }}
          />
        </div>
        
        <div className="flex items-center justify-between text-white">
          <div className="flex items-center gap-3">
            <button
              onClick={togglePlay}
              className="p-2 hover:bg-white/20 rounded-full"
              aria-label={isPlaying ? "Pause" : "Play"}
            >
              {isPlaying ? <Pause size={20} /> : <Play size={20} />}
            </button>
            
            <button
              onClick={skipBackward}
              className="p-2 hover:bg-white/20 rounded-full"
              aria-label="Skip backward 10 seconds"
            >
              <SkipBack size={20} />
            </button>
            
            <button
              onClick={skipForward}
              className="p-2 hover:bg-white/20 rounded-full"
              aria-label="Skip forward 10 seconds"
            >
              <SkipForward size={20} />
            </button>
            
            <div className="flex items-center gap-2">
              <button
                onClick={toggleMute}
                className="p-2 hover:bg-white/20 rounded-full"
                aria-label={isMuted ? "Unmute" : "Mute"}
              >
                {isMuted ? <VolumeX size={20} /> : <Volume2 size={20} />}
              </button>
              
              <input
                type="range"
                min="0"
                max="1"
                step="0.01"
                value={volume}
                onChange={handleVolumeChange}
                className="w-20 h-1 bg-gray-400 rounded-full appearance-none cursor-pointer"
              />
            </div>
            
            <span className="text-sm">
              {formatTime(currentTime)} / {formatTime(duration)}
            </span>
          </div>
          
          <div>
            <button
              onClick={toggleFullscreen}
              className="p-2 hover:bg-white/20 rounded-full"
              aria-label="Toggle fullscreen"
            >
              <Maximize size={20} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default VideoPlayer;
```

#### 3.2 Update App.js to Use the VideoPlayer Component

Modify the App.js file to use the VideoPlayer component when a user clicks "Watch" on a recording:

```jsx
// In App.js, add a new state for the selected recording
const [selectedRecording, setSelectedRecording] = useState(null);

// Add a function to handle watching a recording
const watchRecording = async (recording) => {
  try {
    setError(null);
    setLoading(true);
    
    const response = await fetch(`${API_BASE}/api/recordings/${recording.id}`);
    if (!response.ok) throw new Error('Failed to get recording details');
    
    const data = await response.json();
    setSelectedRecording({
      ...data,
      streamUrl: `${API_BASE}/api/recordings/${recording.id}/stream`
    });
    
    setCurrentView('watch');
  } catch (err) {
    setError('Failed to load recording: ' + err.message);
  } finally {
    setLoading(false);
  }
};

// Add a new view for watching recordings
{currentView === 'watch' && selectedRecording && (
  <div className="max-w-4xl mx-auto">
    <div className="mb-4">
      <button
        onClick={() => setCurrentView('browse')}
        className="text-blue-600 hover:text-blue-800 flex items-center gap-1"
      >
        <ArrowLeft size={16} />
        Back to recordings
      </button>
    </div>
    
    <h2 className="text-2xl font-bold mb-2">{selectedRecording.title}</h2>
    
    <p className="text-gray-600 mb-4">
      By {selectedRecording.creator} • {new Date(selectedRecording.created_at).toLocaleDateString()}
    </p>
    
    <div className="mb-6">
      <VideoPlayer 
        videoUrl={selectedRecording.streamUrl} 
        title={selectedRecording.title} 
      />
    </div>
    
    {selectedRecording.description && (
      <div className="mb-6">
        <h3 className="text-lg font-semibold mb-2">Description</h3>
        <p className="text-gray-700">{selectedRecording.description}</p>
      </div>
    )}
    
    {selectedRecording.tags && selectedRecording.tags.length > 0 && (
      <div>
        <h3 className="text-lg font-semibold mb-2">Tags</h3>
        <div className="flex flex-wrap gap-2">
          {selectedRecording.tags.map(tag => (
            <span key={tag} className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm">
              {tag}
            </span>
          ))}
        </div>
      </div>
    )}
  </div>
)}

// Update the "Watch" button in the recording card to call watchRecording
<button 
  onClick={() => watchRecording(recording)}
  className="flex-1 bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700 flex items-center justify-center gap-2"
>
  <Play size={16} />
  Watch
</button>
```

## 4. Project Structure Improvements

### Requirements
- Organize frontend code into components, hooks, and utilities
- Improve code maintainability and reusability
- Follow best practices for React application structure

### Implementation Steps

#### 4.1 Create a Component Structure

Reorganize the frontend code into the following structure:

```
src/
  components/
    Layout/
      Header.js
      Footer.js
    Recording/
      RecordingForm.js
      RecordingControls.js
    VideoPlayer/
      VideoPlayer.js
      VideoControls.js
    RecordingList/
      RecordingCard.js
      RecordingGrid.js
    SearchFilter/
      SearchBar.js
      TagFilter.js
  hooks/
    useRecording.js
    useVideoPlayer.js
    useApi.js
  utils/
    formatters.js
    validators.js
  contexts/
    RecordingContext.js
  pages/
    HomePage.js
    RecordPage.js
    WatchPage.js
  App.js
  index.js
```

#### 4.2 Create Custom Hooks

Create a custom hook for the recording functionality:

```jsx
// src/hooks/useRecording.js
import { useState, useRef, useCallback, useEffect } from 'react';

export const useRecording = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [recordedBlob, setRecordedBlob] = useState(null);
  const [recordingTime, setRecordingTime] = useState(0);
  const [error, setError] = useState(null);
  
  const mediaRecorderRef = useRef(null);
  const streamRef = useRef(null);
  const intervalRef = useRef(null);
  const chunksRef = useRef([]);
  
  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      streamRef.current?.getTracks().forEach(track => track.stop());
      clearInterval(intervalRef.current);
      setIsRecording(false);
      setIsPaused(false);
    }
  }, [isRecording]);
  
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
  }, [stopRecording]);
  
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
  
  useEffect(() => {
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);
  
  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };
  
  return {
    isRecording,
    isPaused,
    recordedBlob,
    recordingTime,
    error,
    startRecording,
    stopRecording,
    pauseRecording,
    formatTime,
    setRecordedBlob,
    setError
  };
};
```

## 5. Testing Strategy

### Requirements
- Unit tests for backend API endpoints
- Unit tests for React components
- End-to-end tests for critical user flows

### Implementation Steps

#### 5.1 Backend API Tests

Create a test file for the API endpoints:

```javascript
// services/tests/api.test.js
const request = require('supertest');
const express = require('express');
const { Pool } = require('pg');
const AWS = require('aws-sdk');
const multer = require('multer');
const fs = require('fs');
const path = require('path');

// Mock dependencies
jest.mock('pg');
jest.mock('aws-sdk');

// Import server
const app = require('../server');

describe('API Endpoints', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('GET /api/health', () => {
    it('should return status ok', async () => {
      const response = await request(app).get('/api/health');
      expect(response.statusCode).toBe(200);
      expect(response.body).toHaveProperty('status', 'ok');
      expect(response.body).toHaveProperty('timestamp');
    });
  });

  describe('GET /api/recordings', () => {
    it('should return all recordings', async () => {
      // Mock the database query
      const mockRows = [
        { id: 1, title: 'Test Recording 1' },
        { id: 2, title: 'Test Recording 2' }
      ];
      
      Pool.prototype.query.mockResolvedValueOnce({ rows: mockRows });
      
      const response = await request(app).get('/api/recordings');
      
      expect(response.statusCode).toBe(200);
      expect(response.body).toEqual(mockRows);
      expect(Pool.prototype.query).toHaveBeenCalledWith(
        'SELECT * FROM recordings WHERE 1=1 ORDER BY created_at DESC',
        []
      );
    });
    
    it('should filter recordings by search term', async () => {
      // Mock the database query
      const mockRows = [{ id: 1, title: 'Test Recording 1' }];
      
      Pool.prototype.query.mockResolvedValueOnce({ rows: mockRows });
      
      const response = await request(app).get('/api/recordings?search=Test');
      
      expect(response.statusCode).toBe(200);
      expect(response.body).toEqual(mockRows);
      expect(Pool.prototype.query).toHaveBeenCalledWith(
        'SELECT * FROM recordings WHERE 1=1 AND (title ILIKE $1 OR description ILIKE $1) ORDER BY created_at DESC',
        ['%Test%']
      );
    });
  });

  // Add more tests for other endpoints
});
```

#### 5.2 Frontend Component Tests

Create a test file for the VideoPlayer component:

```javascript
// web/src/components/VideoPlayer/VideoPlayer.test.js
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import VideoPlayer from './VideoPlayer';

// Mock the video element
HTMLMediaElement.prototype.play = jest.fn();
HTMLMediaElement.prototype.pause = jest.fn();

describe('VideoPlayer', () => {
  const mockProps = {
    videoUrl: 'https://example.com/video.mp4',
    title: 'Test Video'
  };
  
  beforeEach(() => {
    jest.clearAllMocks();
  });
  
  it('renders the video player', () => {
    render(<VideoPlayer {...mockProps} />);
    
    const videoElement = screen.getByRole('video');
    expect(videoElement).toBeInTheDocument();
    expect(videoElement).toHaveAttribute('src', mockProps.videoUrl);
  });
  
  it('toggles play/pause when button is clicked', () => {
    render(<VideoPlayer {...mockProps} />);
    
    const playButton = screen.getByLabelText('Play');
    fireEvent.click(playButton);
    
    expect(HTMLMediaElement.prototype.play).toHaveBeenCalledTimes(1);
    
    // Now it should be a pause button
    const pauseButton = screen.getByLabelText('Pause');
    fireEvent.click(pauseButton);
    
    expect(HTMLMediaElement.prototype.pause).toHaveBeenCalledTimes(1);
  });
  
  // Add more tests for other functionality
});
```

## 6. Deployment Configuration

### Requirements
- Production-ready Docker Compose configuration
- Environment variable management
- Secure S3 configuration

### Implementation Steps

#### 6.1 Create Production Docker Compose File

Create a `docker-compose.prod.yml` file:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./services/schema.sql:/docker-entrypoint-initdb.d/schema.sql
    restart: always
    networks:
      - knowledge-harvest-network

  api:
    build:
      context: ./services
      dockerfile: Dockerfile.prod
    environment:
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}
      AWS_S3_BUCKET: ${AWS_S3_BUCKET}
      AWS_REGION: ${AWS_REGION}
      AWS_ACCESS_KEY_ID: ${AWS_ACCESS_KEY_ID}
      AWS_SECRET_ACCESS_KEY: ${AWS_SECRET_ACCESS_KEY}
      PORT: 3001
      NODE_ENV: production
    depends_on:
      - postgres
    restart: always
    networks:
      - knowledge-harvest-network

  web:
    build:
      context: ./web
      dockerfile: Dockerfile.prod
      args:
        - REACT_APP_API_URL=${API_URL}
    restart: always
    networks:
      - knowledge-harvest-network

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/conf.d/default.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - api
      - web
    restart: always
    networks:
      - knowledge-harvest-network

networks:
  knowledge-harvest-network:

volumes:
  postgres_data:
```

#### 6.2 Create Production Dockerfiles

Create `Dockerfile.prod` for the API service:

```dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./

RUN npm ci --only=production

COPY . .

EXPOSE 3001

CMD ["node", "server.js"]
```

Create `Dockerfile.prod` for the web service:

```dockerfile
# Build stage
FROM node:18-alpine as build

WORKDIR /app

COPY package*.json ./

RUN npm ci

COPY . .

ARG REACT_APP_API_URL
ENV REACT_APP_API_URL=$REACT_APP_API_URL

RUN npm run build

# Production stage
FROM nginx:alpine

COPY --from=build /app/build /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

#### 6.3 Create Nginx Configuration

Create `nginx/nginx.conf`:

```nginx
server {
    listen 80;
    server_name _;
    
    location / {
        root /usr/share/nginx/html;
        index index.html index.htm;
        try_files $uri $uri/ /index.html;
    }
    
    location /api {
        proxy_pass http://api:3001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        
        # For large file uploads
        client_max_body_size 100M;
    }
}
```

#### 6.4 Create Environment Variables Template

Create a `.env.example` file:

```
# Database
DB_NAME=knowledge_harvest
DB_USER=postgres
DB_PASSWORD=secure_password_here

# AWS S3
AWS_S3_BUCKET=knowledge-harvest-prod
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key

# API
API_URL=https://your-domain.com/api
```