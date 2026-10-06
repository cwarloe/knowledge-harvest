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
## Local Development

### Prerequisites
- Node.js v18+ & npm
- Python 3.11+ & pip
- Docker & Docker Compose

### Setup

2.a Create and activate a virtual environment:
   ```
   cd services
   python3 -m venv ../venv
   source ../venv/bin/activate      # on Windows: venv\Scripts\activate
   ```

2.b Install dependencies and run:
   ```
   pip install --upgrade pip
   pip install -r requirements.txt
   export FLASK_APP=app.py
   python -m flask run --port 5000
   ```

1. **Clone the repo**
   ```bash
   git clone https://github.com/cwarloe/knowledge-harvest.git
   cd knowledge-harvest
   ```

2. **Backend services** (in `services/`)
   ```bash
   cd services
   pip install -r requirements.txt
   export FLASK_APP=app.py
   flask run --port 5000
   ```

3. **Frontend app** (in `web/`)
   ```bash
   cd web
   npm install
   npm start
   ```

4. **Infrastructure** (in `infra/`)
   ```bash
   cd infra
   docker-compose up -d
   ```

5. **Testing**
   ```bash
   pytest services/tests
   ```

Services -> http://localhost:5000
Frontend -> http://localhost:3000

### Env setup
Copy the example and fill in values:

```bash
cp .env.example .env
```
