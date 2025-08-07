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
## Local Development

### Prerequisites
- Node.js v18+ & npm
- Python 3.11+ & pip
- Docker & Docker Compose

### Setup

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
