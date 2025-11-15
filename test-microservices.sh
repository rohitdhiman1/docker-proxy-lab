#!/bin/bash

# Test script for microservices
# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "Testing Microservices Architecture"
echo "=========================================="
echo ""

# Function to test endpoint
test_endpoint() {
    local name=$1
    local url=$2
    local method=${3:-GET}
    local data=${4:-}
    
    echo -n "Testing $name... "
    
    if [ "$method" = "POST" ] || [ "$method" = "PATCH" ]; then
        response=$(curl -sk -X $method "$url" \
            -H "Content-Type: application/json" \
            -d "$data" \
            -w "\n%{http_code}" 2>/dev/null)
    else
        response=$(curl -sk "$url" -w "\n%{http_code}" 2>/dev/null)
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" -ge 200 ] && [ "$http_code" -lt 300 ]; then
        echo -e "${GREEN}✓ OK${NC} (HTTP $http_code)"
        return 0
    else
        echo -e "${RED}✗ FAILED${NC} (HTTP $http_code)"
        echo "Response: $body"
        return 1
    fi
}

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 5

echo ""
echo "=========================================="
echo "Lab 7: Microservices Tests"
echo "=========================================="
echo ""

# Test aggregated health endpoint
echo "--- Health Checks ---"
test_endpoint "Microservices Health" "https://localhost/api/health"
echo ""

# Test User Service
echo "--- User Service Tests ---"
test_endpoint "List Users" "https://localhost/api/v1/users"
test_endpoint "Get User #1" "https://localhost/api/v1/users/1"
test_endpoint "Get User Stats" "https://localhost/api/v1/users/stats"

# Create a new user
NEW_USER_DATA='{"username":"testuser_'$(date +%s)'","email":"test'$(date +%s)'@example.com"}'
test_endpoint "Create User" "https://localhost/api/v1/users" "POST" "$NEW_USER_DATA"
echo ""

# Test Product Service
echo "--- Product Service Tests ---"
test_endpoint "List Products" "https://localhost/api/v1/products"
test_endpoint "Get Product #1" "https://localhost/api/v1/products/1"
test_endpoint "Filter Electronics" "https://localhost/api/v1/products?category=Electronics"
test_endpoint "Get Product Stats" "https://localhost/api/v1/products/stats"

# Create a new product
NEW_PRODUCT_DATA='{"name":"Test Product","description":"Test description","price":99.99,"stock":50,"category":"Test"}'
test_endpoint "Create Product" "https://localhost/api/v1/products" "POST" "$NEW_PRODUCT_DATA"

# Update product stock
UPDATE_STOCK_DATA='{"stock":100}'
test_endpoint "Update Stock" "https://localhost/api/v1/products/1/stock" "PATCH" "$UPDATE_STOCK_DATA"
echo ""

# Test Order Service
echo "--- Order Service Tests ---"
test_endpoint "List Orders" "https://localhost/api/v1/orders"
test_endpoint "Get Order #1" "https://localhost/api/v1/orders/1"
test_endpoint "Get Order Stats" "https://localhost/api/v1/orders/stats"

# Create a new order
NEW_ORDER_DATA='{"user_id":1,"product_id":2,"quantity":2,"total_price":1998.00}'
test_endpoint "Create Order" "https://localhost/api/v1/orders" "POST" "$NEW_ORDER_DATA"

# Update order status
UPDATE_STATUS_DATA='{"status":"processing"}'
test_endpoint "Update Order Status" "https://localhost/api/v1/orders/1/status" "PATCH" "$UPDATE_STATUS_DATA"
echo ""

# Test caching behavior
echo "--- Cache Performance Test ---"
echo -n "First call (no cache): "
time curl -sk https://localhost/api/v1/users > /dev/null 2>&1
echo -n "Second call (cached): "
time curl -sk https://localhost/api/v1/users > /dev/null 2>&1
echo ""

# Test database connectivity
echo "--- Database Tests ---"
echo "Checking PostgreSQL..."
docker exec postgres pg_isready -U labuser -d labdb
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ PostgreSQL is ready${NC}"
else
    echo -e "${RED}✗ PostgreSQL is not ready${NC}"
fi

echo ""
echo "Checking Redis..."
docker exec redis redis-cli PING > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Redis is ready${NC}"
else
    echo -e "${RED}✗ Redis is not ready${NC}"
fi

echo ""
echo "--- Cache Inspection ---"
echo "Redis keys:"
docker exec redis redis-cli KEYS '*' 2>/dev/null | head -10

echo ""
echo "=========================================="
echo "Microservices Test Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. View detailed documentation: cat LAB_07_MICROSERVICES.md"
echo "2. Access Grafana: http://localhost:3000 (admin/admin)"
echo "3. Access Kibana: http://localhost:5601"
echo "4. Access Prometheus: http://localhost:9090"
echo ""
