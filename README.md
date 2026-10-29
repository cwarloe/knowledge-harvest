# Knowledge Harvest

**Transfer the know-how behind a growing company's success so employees can perform without unnecessary founder dependency.**

Knowledge Harvest is an emerging performance-consulting and technology concept for founder-led service businesses. It identifies work that still escalates to the founder, diagnoses **why** the team still needs that expertise, and transfers the capability using the smallest appropriate intervention — which may be a decision guide, job aid, practice, coaching, documentation, automation, AI support, or formal training.

The existing software in this repository explores one part of that larger problem: capturing and sharing tacit subject-matter-expert knowledge through screen recordings and related work artifacts.

> **Working principle:** Don't document the founder. Reproduce the capability.

### Business and research docs

- [Business hypothesis](docs/business-hypothesis.md)
- [Founder capability research](docs/founder-capability-research.md)
- [Entrepreneurship advisor pitch](docs/advisor-pitch.md)
- [MVP definition](docs/mvp-definition.md)

### Playbooks

- [Instructions → training video](playbooks/instructions-to-training-video/README.md): turn a written procedure (docx, PDF, slides, web page, notes) into a short captioned walkthrough video, with no screen recording. A way to reproduce a capability when the steps already exist in writing.

## Quick Start

```bash
git clone https://github.com/cwarloe/knowledge-harvest.git
cd knowledge-harvest
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
## Local Development

### Prerequisites
- Node.js v18+ & npm
- Docker & Docker Compose

### Setup

1. **Clone the repo**
   ```bash
   git clone https://github.com/cwarloe/knowledge-harvest.git
   cd knowledge-harvest
   ```

2. **Backend API** (in `services/`, Node/Express)
   ```bash
   cd services
   npm install
   npm run dev
   ```

3. **Frontend app** (in `web/`)
   ```bash
   cd web
   npm install
   npm start
   ```

4. **Database + local S3** (root `docker-compose.yml`)
   ```bash
   docker-compose up -d
   ```

5. **Testing**
   ```bash
   cd services && npm test
   ```

API -> http://localhost:3001/api/health
Frontend -> http://localhost:3000

### Env setup
Copy the example and fill in values:

```bash
cp .env.example .env
```
