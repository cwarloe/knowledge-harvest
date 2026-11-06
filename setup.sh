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

# Smoke test — match docker-compose PORT=3001 and server.js /api/health
sleep 3
if curl -sf http://localhost:3001/api/health >/dev/null; then
  echo "API OK"
else
  echo "API NOT READY (this is okay if API is not part of your stack yet)"
fi
