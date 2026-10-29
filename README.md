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

## Features

- WebRTC screen recording with audio
- File upload to LocalStack S3
- PostgreSQL database
- Search and tag filtering
- Docker development environment

## Architecture

- **Frontend**: React with Tailwind CSS
- **Backend**: Node.js/Express API
- **Database**: PostgreSQL
- **Storage**: LocalStack S3 (development)
- **Deployment**: Docker Compose

## Setup

### Prerequisites

You'll need Node.js v18 or later with npm, plus Docker and Docker Compose.

### Quick start

If you just want everything running, clone the repo and run the setup script:

```bash
git clone https://github.com/cwarloe/knowledge-harvest.git
cd knowledge-harvest
./setup.sh
```

When it finishes, open http://localhost:3000.

### Running each part yourself

If you'd rather run the pieces one at a time, start from the cloned repo.

1. **Start the database and local S3.** These come from the root `docker-compose.yml`.
   ```bash
   docker-compose up -d
   ```

2. **Start the backend API.** It lives in `services/` and runs on Node/Express.
   ```bash
   cd services
   npm install
   npm run dev
   ```

3. **Start the frontend app.** It lives in `web/`.
   ```bash
   cd web
   npm install
   npm start
   ```

Once everything is up, the API health check is at http://localhost:3001/api/health and the frontend is at http://localhost:3000.

### Environment variables

Copy the example file, then fill in your own values:

```bash
cp .env.example .env
```

### Running the tests

The backend tests run from `services/`:

```bash
cd services && npm test
```

### Day-to-day Docker commands

These are handy while you're working. To follow the logs:

```bash
docker-compose logs -f api
docker-compose logs -f web
```

To stop everything, run `docker-compose down`. To bring it back up, run `docker-compose up -d`.
