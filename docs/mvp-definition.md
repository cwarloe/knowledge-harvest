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
