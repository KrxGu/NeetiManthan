#!/bin/bash

# NeetiManthan Startup Script

echo "🚀 Starting NeetiManthan AI Comment Analysis System..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Create environment file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from example..."
    cp env.example .env
    echo "✅ Created .env file. Please review and update as needed."
fi

# Create data directories
mkdir -p data/models data/uploads logs

echo "🐳 Starting services with Docker Compose..."

# Start the infrastructure services first
docker-compose up -d db redis minio

echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if services are healthy
echo "🔍 Checking service health..."

# Wait for PostgreSQL
echo "Waiting for PostgreSQL..."
until docker-compose exec db pg_isready -U postgres; do
    sleep 2
done

# Wait for Redis
echo "Waiting for Redis..."
until docker-compose exec redis redis-cli ping; do
    sleep 2
done

echo "✅ Infrastructure services are ready!"

# Start application services
echo "🚀 Starting application services..."
docker-compose up -d

echo "⏳ Waiting for application services to start..."
sleep 15

# Check API health
echo "🔍 Checking API health..."
curl -f http://localhost:8000/api/v1/health || echo "⚠️  API health check failed - services may still be starting"

echo ""
echo "🎉 NeetiManthan is starting up!"
echo ""
echo "📊 Services:"
echo "   • API Gateway: http://localhost:8000"
echo "   • API Docs: http://localhost:8000/docs"
echo "   • MinIO Console: http://localhost:9001 (admin/minioadmin123)"
echo ""
echo "🔧 Tool Services:"
echo "   • Ingest Tool: http://localhost:8001"
echo "   • Classify Tool: http://localhost:8002" 
echo "   • Clause Linker: http://localhost:8003"
echo ""
echo "📝 To view logs:"
echo "   docker-compose logs -f [service-name]"
echo ""
echo "🛑 To stop all services:"
echo "   docker-compose down"
echo ""
echo "Happy analyzing! 🎯"
