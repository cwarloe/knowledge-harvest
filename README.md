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
