#!/bin/bash

# Quick Start Script for Nail Salon AI (Backend services only)
# This starts backend services in Docker and guides you to start the frontend separately

set -e

echo "🚀 Starting Nail Salon AI - Backend Services"
echo "=============================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cat > .env << EOF
POSTGRES_PASSWORD=mysecurepassword123
SECRET_KEY=your-super-secret-jwt-key-at-least-32-chars
GRAFANA_PASSWORD=admin
DEBUG=false
EOF
    echo "✅ Created .env file with default values"
    echo ""
fi

# Start backend services
echo "🐳 Starting backend services with Docker Compose..."
docker-compose -f docker-compose-backend.yml up -d

echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check if Ollama is running
if docker ps | grep -q nail-salon-ollama; then
    echo ""
    echo "🤖 Pulling Ollama model (this may take a few minutes on first run)..."
    docker exec nail-salon-ollama ollama pull llama2 || echo "Note: You may need to run this manually later"
fi

echo ""
echo "✅ Backend services are running!"
echo ""
echo "📊 Services:"
echo "  - Backend API: http://localhost:8000"
echo "  - API Docs: http://localhost:8000/docs"
echo "  - PostgreSQL: localhost:5432"
echo "  - Redis: localhost:6379"
echo "  - Ollama: localhost:11434"
echo "  - Prometheus: http://localhost:9090"
echo "  - Grafana: http://localhost:3000 (admin/admin)"
echo ""
echo "🎨 To start the FRONTEND:"
echo "  cd frontend/apps/web-antd"
echo "  pnpm vite --host 127.0.0.1 --port 5173"
echo ""
echo "  Then open: http://localhost:5173"
echo "  Login: admin / 123456"
echo ""
echo "📝 Useful commands:"
echo "  - View logs: docker-compose -f docker-compose-backend.yml logs -f"
echo "  - Stop all: docker-compose -f docker-compose-backend.yml down"
echo "  - Restart: docker-compose -f docker-compose-backend.yml restart"
echo ""

