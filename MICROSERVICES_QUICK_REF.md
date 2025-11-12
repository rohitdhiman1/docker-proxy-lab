# Microservices Quick Reference

## 🚀 Quick Start
```bash
# Build and start all services
docker-compose up -d --build

# Check service status
docker-compose ps

# Run automated tests
./test-microservices.sh
```

## 📡 API Endpoints

### User Service (Port 5000)
```bash
# List all users
curl -k https://localhost/api/v1/users

# Get user by ID
curl -k https://localhost/api/v1/users/1

# Create user
curl -k -X POST https://localhost/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{"username":"john","email":"john@example.com"}'

# Get statistics
curl -k https://localhost/api/v1/users/stats

# Health check
curl -k https://localhost:5000/health
```

### Product Service (Port 3000 → 3001)
```bash
# List all products
curl -k https://localhost/api/v1/products

# Filter by category
curl -k "https://localhost/api/v1/products?category=Electronics"

# Get product by ID
curl -k https://localhost/api/v1/products/1

# Create product
curl -k -X POST https://localhost/api/v1/products \
  -H "Content-Type: application/json" \
  -d '{
    "name":"Laptop",
    "description":"Gaming laptop",
    "price":1499.99,
    "stock":10,
    "category":"Electronics"
  }'

# Update stock
curl -k -X PATCH https://localhost/api/v1/products/1/stock \
  -H "Content-Type: application/json" \
  -d '{"stock":50}'

# Get statistics
curl -k https://localhost/api/v1/products/stats

# Health check
curl -k http://localhost:3001/health
```

### Order Service (Port 8080 → 8086)
```bash
# List all orders
curl -k https://localhost/api/v1/orders

# Get order by ID
curl -k https://localhost/api/v1/orders/1

# Create order
curl -k -X POST https://localhost/api/v1/orders \
  -H "Content-Type: application/json" \
  -d '{
    "user_id":1,
    "product_id":2,
    "quantity":2,
    "total_price":1998.00
  }'

# Update order status
curl -k -X PATCH https://localhost/api/v1/orders/1/status \
  -H "Content-Type: application/json" \
  -d '{"status":"shipped"}'

# Get statistics
curl -k https://localhost/api/v1/orders/stats

# Health check
curl -k http://localhost:8086/health
```

## 🗄️ Database Commands

### Connect to PostgreSQL
```bash
docker exec -it postgres psql -U labuser -d labdb
```

### Useful SQL Queries
```sql
-- List all tables
\dt

-- View all users
SELECT * FROM users;

-- View products with stock
SELECT name, price, stock, category FROM products;

-- View orders with details
SELECT 
  o.id, 
  u.username, 
  p.name as product, 
  o.quantity, 
  o.total_price, 
  o.status
FROM orders o
JOIN users u ON o.user_id = u.id
JOIN products p ON o.product_id = p.id
ORDER BY o.created_at DESC;

-- Exit
\q
```

## 🔴 Redis Commands

### Connect to Redis
```bash
docker exec -it redis redis-cli
```

### Useful Redis Commands
```redis
# List all keys
KEYS *

# Check key TTL
TTL users:all
TTL products:1
TTL orders:all

# Get cached value
GET users:1
GET products:2

# Delete cache
DEL users:all
FLUSHDB

# Exit
exit
```

## 🔍 Monitoring & Logs

### View Service Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f user-service
docker-compose logs -f product-service
docker-compose logs -f order-service
docker-compose logs -f postgres
docker-compose logs -f redis

# Last 50 lines
docker-compose logs --tail=50 user-service
```

### Check Service Status
```bash
# All services
docker-compose ps

# Specific service health
docker exec user-service curl -f http://localhost:5000/health
docker exec product-service wget -q -O- http://localhost:3000/health
docker exec order-service wget -q -O- http://localhost:8080/health
```

## 🛠️ Common Tasks

### Rebuild Specific Service
```bash
docker-compose up -d --build user-service
docker-compose up -d --build product-service
docker-compose up -d --build order-service
```

### Restart Services
```bash
docker-compose restart user-service
docker-compose restart product-service
docker-compose restart order-service
```

### View Resource Usage
```bash
docker stats
```

### Execute Commands in Containers
```bash
# Python shell in user-service
docker exec -it user-service python

# Node shell in product-service
docker exec -it product-service node

# Bash in any service
docker exec -it user-service bash
```

## 🐛 Debugging

### Check if PostgreSQL is Ready
```bash
docker exec postgres pg_isready -U labuser -d labdb
```

### Test Database Connection from Service
```bash
docker exec user-service python -c "
import psycopg2
conn = psycopg2.connect(
    host='postgres',
    database='labdb',
    user='labuser',
    password='labpass'
)
print('Connected!')
conn.close()
"
```

### Check Redis Connection
```bash
docker exec redis redis-cli PING
```

### Network Inspection
```bash
# List networks
docker network ls

# Inspect microservices network
docker network inspect docker-proxy-lab_microservices-network
```

### Volume Inspection
```bash
# List volumes
docker volume ls

# Inspect database volume
docker volume inspect docker-proxy-lab_postgres-data

# Inspect cache volume
docker volume inspect docker-proxy-lab_redis-data
```

## 🧪 Testing Scenarios

### Test Cache Performance
```bash
# First call (miss - slow)
time curl -k https://localhost/api/v1/users

# Second call (hit - fast)
time curl -k https://localhost/api/v1/users
```

### Test Cache Invalidation
```bash
# Populate cache
curl -k https://localhost/api/v1/users > /dev/null

# Verify cache exists
docker exec redis redis-cli GET users:all

# Create new user (invalidates cache)
curl -k -X POST https://localhost/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{"username":"test","email":"test@test.com"}'

# Verify cache is cleared
docker exec redis redis-cli GET users:all
```

### Test Foreign Key Validation
```bash
# Try to create order with invalid user_id
curl -k -X POST https://localhost/api/v1/orders \
  -H "Content-Type: application/json" \
  -d '{"user_id":9999,"product_id":1,"quantity":1,"total_price":99.99}'
```

## 🧹 Cleanup

### Stop Services
```bash
docker-compose stop
```

### Stop and Remove Containers
```bash
docker-compose down
```

### Remove with Volumes (DELETE DATA)
```bash
docker-compose down -v
```

### Remove Everything
```bash
docker-compose down -v --rmi all
```

## 📊 Sample Data

### Users (4 users)
- ID 1: alice (alice@example.com)
- ID 2: bob (bob@example.com)
- ID 3: charlie (charlie@example.com)
- ID 4: diana (diana@example.com)

### Products (10 products)
- ID 1: Laptop ($999.99, Electronics)
- ID 2: Smartphone ($699.99, Electronics)
- ID 3: Office Chair ($299.99, Furniture)
- ID 4: Desk Lamp ($49.99, Furniture)
- And 6 more...

### Orders (8 orders)
- Various combinations of users and products
- Statuses: pending, processing, shipped, completed

## 🔗 Useful URLs

- **Nginx Reverse Proxy**: https://localhost
- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **Kibana**: http://localhost:5601
- **User Service Direct**: http://localhost:5000
- **Product Service Direct**: http://localhost:3001
- **Order Service Direct**: http://localhost:8086

## 📚 Documentation

- **LAB_07_MICROSERVICES.md** - Complete lab exercises
- **MICROSERVICES_SUMMARY.md** - Implementation details
- **README.md** - Main documentation
- **ARCHITECTURE.md** - Architecture diagrams
- **ENHANCEMENT_ROADMAP.md** - Future enhancements

## 🎯 Common Workflows

### Create a Complete Order Flow
```bash
# 1. Create a user
curl -k -X POST https://localhost/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{"username":"newuser","email":"new@example.com"}'

# 2. Create a product
curl -k -X POST https://localhost/api/v1/products \
  -H "Content-Type: application/json" \
  -d '{"name":"New Product","price":99.99,"stock":100,"category":"Test"}'

# 3. Create an order (use IDs from previous responses)
curl -k -X POST https://localhost/api/v1/orders \
  -H "Content-Type: application/json" \
  -d '{"user_id":5,"product_id":11,"quantity":2,"total_price":199.98}'
```

### Monitor Order Status Changes
```bash
# Create order
ORDER_ID=$(curl -sk -X POST https://localhost/api/v1/orders \
  -H "Content-Type: application/json" \
  -d '{"user_id":1,"product_id":1,"quantity":1,"total_price":999.99}' \
  | jq -r '.id')

# Check status
curl -k https://localhost/api/v1/orders/$ORDER_ID | jq '.status'

# Update to processing
curl -k -X PATCH https://localhost/api/v1/orders/$ORDER_ID/status \
  -H "Content-Type: application/json" \
  -d '{"status":"processing"}'

# Update to shipped
curl -k -X PATCH https://localhost/api/v1/orders/$ORDER_ID/status \
  -H "Content-Type: application/json" \
  -d '{"status":"shipped"}'

# Final check
curl -k https://localhost/api/v1/orders/$ORDER_ID | jq '.'
```

---

**Keep this file handy for quick command reference!**
