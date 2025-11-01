#!/bin/bash

# Docker Proxy Lab - Setup Script
# This script sets up the entire lab environment

set -e

echo "🚀 Docker Proxy Lab - Advanced Edition Setup"
echo "============================================="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop and try again."
    exit 1
fi

echo "✅ Docker is running"
echo ""

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose not found. Please install docker-compose."
    exit 1
fi

echo "✅ docker-compose is available"
echo ""

# Generate SSL certificates
echo "📜 Generating SSL certificates..."
cd certs

if [ ! -f nginx-selfsigned.crt ]; then
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
      -keyout nginx-selfsigned.key \
      -out nginx-selfsigned.crt \
      -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost" \
      > /dev/null 2>&1
    echo "✅ SSL certificates generated"
else
    echo "✅ SSL certificates already exist"
fi

cd ..
echo ""

# Pull Docker images
echo "📦 Pulling Docker images (this may take a few minutes)..."
docker-compose pull

echo ""
echo "✅ All images pulled successfully"
echo ""

# Start services
echo "🎯 Starting all services..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check service health
echo ""
echo "📊 Service Status:"
docker-compose ps

echo ""
echo "============================================="
echo "✅ Setup Complete!"
echo "============================================="
echo ""
echo "🌐 Access Points:"
echo "  • Reverse Proxy (HTTPS): https://localhost"
echo "  • Grafana:               http://localhost:3000 (admin/admin)"
echo "  • Prometheus:            http://localhost:9090"
echo "  • Kibana:                http://localhost:5601"
echo "  • Elasticsearch:         http://localhost:9200"
echo ""
echo "📚 Next Steps:"
echo "  1. Open README.md for detailed lab instructions"
echo "  2. Start with Lab 1: Forward Proxy"
echo "  3. Generate some traffic: curl -k https://localhost"
echo ""
echo "🧹 Cleanup:"
echo "  • Stop services:        docker-compose down"
echo "  • Remove volumes:       docker-compose down -v"
echo ""
echo "Happy Learning! 🚀"
