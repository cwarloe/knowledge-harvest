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
