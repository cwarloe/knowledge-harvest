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

### Architecture Decision
Start with a monolithic architecture for faster development and deployment. Migrate to microservices after the concept is validated.

## Success Criteria

### Quantitative Metrics
- 10+ recordings created by 3+ SMEs
- Average recording length: 5-10 minutes
- 80% completion rate for recordings started

### Qualitative Validation
- SMEs find the recording process intuitive
- Knowledge consumers can find and use recordings effectively
- Technical performance meets usability standards

## Development Plan

### Timeline (5 weeks)
- **Week 1-2**: Core screen recording functionality
- **Week 3**: Upload and storage system
- **Week 4**: Playback and basic organization
- **Week 5**: Testing and user feedback

### Resource Requirements
- 1-2 full-stack developers
- UX feedback from 3-5 SMEs
- Basic cloud infrastructure budget

## Scope Boundaries

### Included in MVP
- Core screen recording workflow
- Basic content management
- Essential playback features

### Explicitly Excluded
- AI transcription/summarization
- Advanced workflow capture
- Microservices architecture
- After-action reflections
- Advanced analytics
- Complex user authentication (use basic auth)

## Risk Mitigation

### Technical Risks
- **Browser compatibility**: Target modern browsers initially
- **File size limits**: The 15-minute cap keeps storage costs down
- **Performance**: A single Docker Compose stack is enough for MVP scale

### User Adoption Risks
- **SME engagement**: Include SMEs in the design process
- **Content quality**: Provide recording guidelines
- **Discoverability**: Simple but effective search and tagging

## Post-MVP Evolution

### Immediate Next Steps (Weeks 6-12)
1. AI transcription integration
2. User authentication system
3. Enhanced metadata and search
4. Mobile-responsive improvements

### Future Roadmap (3+ months)
1. Microservices migration
2. Advanced AI features (summarization, insights)
3. Workflow templates and guided capture
4. Integration with existing knowledge systems

## Success Transition Criteria
Move to the next phase when:
- MVP metrics are achieved
- User feedback validates the core concept
- The technical architecture has proven stable
- Clear user engagement patterns are established
