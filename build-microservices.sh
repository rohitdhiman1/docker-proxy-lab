#!/bin/bash

# Build and setup script for microservices lab
# This script helps students get started quickly

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=========================================="
echo "Docker Proxy Lab - Microservices Setup"
echo -e "==========================================${NC}"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}✗ Docker is not running${NC}"
    echo "Please start Docker Desktop and try again"
    exit 1
fi
echo -e "${GREEN}✓ Docker is running${NC}"

# Check if Docker Compose is available
if ! docker-compose version > /dev/null 2>&1; then
    echo -e "${RED}✗ Docker Compose is not available${NC}"
    echo "Please install Docker Compose and try again"
    exit 1
fi
echo -e "${GREEN}✓ Docker Compose is available${NC}"
echo ""

# Generate SSL certificates if they don't exist
if [ ! -f "certs/nginx-selfsigned.crt" ]; then
    echo -e "${YELLOW}Generating SSL certificates...${NC}"
    cd certs && bash generate-certs.sh && cd ..
    echo -e "${GREEN}✓ SSL certificates generated${NC}"
else
    echo -e "${GREEN}✓ SSL certificates already exist${NC}"
fi
echo ""

# Stop any running containers
echo -e "${BLUE}Stopping existing containers...${NC}"
docker-compose down > /dev/null 2>&1
echo -e "${GREEN}✓ Containers stopped${NC}"
echo ""

# Pull base images
echo -e "${BLUE}Pulling base images...${NC}"
docker-compose pull postgres redis elasticsearch logstash kibana prometheus grafana > /dev/null 2>&1
echo -e "${GREEN}✓ Base images pulled${NC}"
echo ""

# Build microservices
echo -e "${BLUE}Building microservices (this may take a few minutes)...${NC}"
echo ""

echo -e "${YELLOW}Building User Service (Python/Flask)...${NC}"
docker-compose build user-service
echo -e "${GREEN}✓ User Service built${NC}"
echo ""

echo -e "${YELLOW}Building Product Service (Node.js/Express)...${NC}"
docker-compose build product-service
echo -e "${GREEN}✓ Product Service built${NC}"
echo ""

echo -e "${YELLOW}Building Order Service (Go)...${NC}"
docker-compose build order-service
echo -e "${GREEN}✓ Order Service built${NC}"
echo ""

# Build other services
echo -e "${BLUE}Building remaining services...${NC}"
docker-compose build > /dev/null 2>&1
echo -e "${GREEN}✓ All services built${NC}"
echo ""

# Start services
echo -e "${BLUE}Starting all services...${NC}"
docker-compose up -d

# Wait for services to be healthy
echo ""
echo -e "${YELLOW}Waiting for services to become healthy (30 seconds)...${NC}"
sleep 30

# Check service status
echo ""
echo -e "${BLUE}Service Status:${NC}"
docker-compose ps

echo ""
echo -e "${GREEN}=========================================="
echo "✓ Setup Complete!"
echo -e "==========================================${NC}"
echo ""
echo -e "${BLUE}Access Points:${NC}"
echo "  • Nginx Reverse Proxy: https://localhost"
echo "  • User Service API: https://localhost/api/v1/users"
echo "  • Product Service API: https://localhost/api/v1/products"
echo "  • Order Service API: https://localhost/api/v1/orders"
echo "  • Grafana Dashboard: http://localhost:3000 (admin/admin)"
echo "  • Prometheus: http://localhost:9090"
echo "  • Kibana: http://localhost:5601"
echo ""
echo -e "${BLUE}Quick Tests:${NC}"
echo "  • Run automated tests: ./test-microservices.sh"
echo "  • Get all users: curl -k https://localhost/api/v1/users"
echo "  • Get all products: curl -k https://localhost/api/v1/products"
echo "  • Get all orders: curl -k https://localhost/api/v1/orders"
echo ""
echo -e "${BLUE}Documentation:${NC}"
echo "  • Complete Lab Guide: cat LAB_07_MICROSERVICES.md"
echo "  • Quick Reference: cat MICROSERVICES_QUICK_REF.md"
echo "  • Implementation Summary: cat MICROSERVICES_SUMMARY.md"
echo ""
echo -e "${BLUE}Database Access:${NC}"
echo "  • PostgreSQL: docker exec -it postgres psql -U labuser -d labdb"
echo "  • Redis: docker exec -it redis redis-cli"
echo ""
echo -e "${YELLOW}Note: If services show as 'starting', wait 1-2 minutes and check again with:${NC}"
echo "  docker-compose ps"
echo ""
