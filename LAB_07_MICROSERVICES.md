# Lab 7: Microservices Architecture

## Overview
This lab demonstrates a real-world microservices architecture with three services (User, Product, Order) backed by PostgreSQL database and Redis cache, all accessed through Nginx reverse proxy.

## Architecture

```
                           ┌─────────────────┐
                           │  Nginx Proxy    │
                           │  (Port 443)     │
                           └────────┬────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
            ┌───────▼──────┐ ┌─────▼──────┐ ┌─────▼──────┐
            │ User Service │ │  Product   │ │   Order    │
            │  (Flask)     │ │  Service   │ │  Service   │
            │  Port 5000   │ │ (Express)  │ │   (Go)     │
            └──────┬───────┘ │ Port 3000  │ └─────┬──────┘
                   │         └─────┬──────┘       │
                   │               │              │
                   └───────┬───────┴──────┬───────┘
                           │              │
                  ┌────────▼────┐    ┌────▼────┐
                  │  PostgreSQL │    │  Redis  │
                  │  Port 5432  │    │ Port    │
                  └─────────────┘    │  6379   │
                                     └─────────┘
```

## Services Overview

### 1. **User Service** (Python/Flask)
- **Purpose**: User management and authentication
- **Port**: 5000
- **Database**: PostgreSQL (users table)
- **Cache**: Redis (60s TTL for lists, 300s for individual users)
- **Endpoints**:
  - `GET /health` - Health check with DB and Redis status
  - `GET /api/v1/users` - List all users (cached)
  - `GET /api/v1/users/<id>` - Get user by ID (cached)
  - `POST /api/v1/users` - Create new user (invalidates cache)
  - `GET /api/v1/stats` - Service statistics

### 2. **Product Service** (Node.js/Express)
- **Purpose**: Product catalog and inventory management
- **Port**: 3000
- **Database**: PostgreSQL (products table)
- **Cache**: Redis (60s TTL for lists, 300s for individual products)
- **Endpoints**:
  - `GET /health` - Health check with DB and Redis status
  - `GET /api/v1/products` - List products (optional ?category=electronics)
  - `GET /api/v1/products/<id>` - Get product by ID (cached)
  - `POST /api/v1/products` - Create new product (invalidates cache)
  - `PATCH /api/v1/products/<id>/stock` - Update stock level
  - `GET /api/v1/stats` - Service statistics

### 3. **Order Service** (Go)
- **Purpose**: Order processing and management
- **Port**: 8080
- **Database**: PostgreSQL (orders table with foreign keys to users and products)
- **Cache**: Redis (60s TTL for lists, 300s for individual orders)
- **Endpoints**:
  - `GET /health` - Health check with DB and Redis status
  - `GET /api/v1/orders` - List all orders (cached)
  - `GET /api/v1/orders/<id>` - Get order by ID (cached)
  - `POST /api/v1/orders` - Create new order (validates user and product, invalidates cache)
  - `PATCH /api/v1/orders/<id>/status` - Update order status
  - `GET /api/v1/stats` - Service statistics

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Products Table
```sql
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    stock INTEGER NOT NULL DEFAULT 0,
    category VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Orders Table
```sql
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    product_id INTEGER REFERENCES products(id),
    quantity INTEGER NOT NULL,
    total_price DECIMAL(10,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Lab Exercises

### Exercise 1: Start the Microservices Stack

1. **Build and start all services:**
   ```bash
   docker-compose up -d --build
   ```

2. **Verify all services are running:**
   ```bash
   docker-compose ps
   ```
   You should see 17 services running including postgres, redis, and the three microservices.

3. **Check service logs:**
   ```bash
   # User service logs
   docker-compose logs -f user-service
   
   # Product service logs
   docker-compose logs -f product-service
   
   # Order service logs
   docker-compose logs -f order-service
   ```

### Exercise 2: Test User Service

1. **Check health status:**
   ```bash
   curl -k https://localhost/api/v1/users
   ```

2. **Get all users:**
   ```bash
   curl -k https://localhost/api/v1/users
   ```
   Expected output: JSON array with 4 sample users (Alice, Bob, Charlie, Diana)

3. **Get specific user:**
   ```bash
   curl -k https://localhost/api/v1/users/1
   ```

4. **Create a new user:**
   ```bash
   curl -k -X POST https://localhost/api/v1/users \
     -H "Content-Type: application/json" \
     -d '{
       "username": "eddie",
       "email": "eddie@example.com"
     }'
   ```

5. **Verify cache behavior:**
   ```bash
   # First call - hits database
   time curl -k https://localhost/api/v1/users
   
   # Second call - hits cache (should be faster)
   time curl -k https://localhost/api/v1/users
   ```

6. **Check service statistics:**
   ```bash
   curl -k https://localhost/api/v1/users/stats
   ```

### Exercise 3: Test Product Service

1. **Get all products:**
   ```bash
   curl -k https://localhost/api/v1/products
   ```
   Expected output: JSON array with 10 sample products

2. **Filter by category:**
   ```bash
   curl -k "https://localhost/api/v1/products?category=Electronics"
   ```

3. **Get specific product:**
   ```bash
   curl -k https://localhost/api/v1/products/1
   ```

4. **Create a new product:**
   ```bash
   curl -k -X POST https://localhost/api/v1/products \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Smart Watch",
       "description": "Fitness tracking smartwatch",
       "price": 299.99,
       "stock": 75,
       "category": "Electronics"
     }'
   ```

5. **Update product stock:**
   ```bash
   curl -k -X PATCH https://localhost/api/v1/products/1/stock \
     -H "Content-Type: application/json" \
     -d '{
       "stock": 45
     }'
   ```

6. **Verify stock was updated:**
   ```bash
   curl -k https://localhost/api/v1/products/1 | jq '.stock'
   ```

### Exercise 4: Test Order Service

1. **Get all orders:**
   ```bash
   curl -k https://localhost/api/v1/orders
   ```
   Expected output: JSON array with 8 sample orders

2. **Get specific order:**
   ```bash
   curl -k https://localhost/api/v1/orders/1
   ```

3. **Create a new order:**
   ```bash
   curl -k -X POST https://localhost/api/v1/orders \
     -H "Content-Type: application/json" \
     -d '{
       "user_id": 1,
       "product_id": 2,
       "quantity": 2,
       "total_price": 1998.00
     }'
   ```

4. **Update order status:**
   ```bash
   curl -k -X PATCH https://localhost/api/v1/orders/1/status \
     -H "Content-Type: application/json" \
     -d '{
       "status": "shipped"
     }'
   ```

5. **Verify status was updated:**
   ```bash
   curl -k https://localhost/api/v1/orders/1 | jq '.status'
   ```

### Exercise 5: Database Interactions

1. **Connect to PostgreSQL:**
   ```bash
   docker exec -it postgres psql -U labuser -d labdb
   ```

2. **View all tables:**
   ```sql
   \dt
   ```

3. **Query users:**
   ```sql
   SELECT * FROM users;
   ```

4. **Query products by category:**
   ```sql
   SELECT name, price, stock FROM products WHERE category = 'Electronics';
   ```

5. **Query orders with user and product details:**
   ```sql
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
   ```

6. **Exit PostgreSQL:**
   ```sql
   \q
   ```

### Exercise 6: Redis Cache Inspection

1. **Connect to Redis:**
   ```bash
   docker exec -it redis redis-cli
   ```

2. **List all keys:**
   ```redis
   KEYS *
   ```

3. **Check TTL of a key:**
   ```redis
   TTL users:all
   TTL products:all
   TTL orders:all
   ```

4. **Get cached value:**
   ```redis
   GET users:all
   GET products:1
   ```

5. **Manually invalidate cache:**
   ```redis
   DEL users:all
   ```

6. **Exit Redis:**
   ```redis
   exit
   ```

### Exercise 7: Test Cache Invalidation

1. **Get all users (populates cache):**
   ```bash
   curl -k https://localhost/api/v1/users
   ```

2. **Check cache in Redis:**
   ```bash
   docker exec -it redis redis-cli GET users:all
   ```

3. **Create a new user (should invalidate cache):**
   ```bash
   curl -k -X POST https://localhost/api/v1/users \
     -H "Content-Type: application/json" \
     -d '{
       "username": "frank",
       "email": "frank@example.com"
     }'
   ```

4. **Verify cache was invalidated:**
   ```bash
   docker exec -it redis redis-cli GET users:all
   # Should return (nil) or new data
   ```

5. **Get users again (repopulates cache):**
   ```bash
   curl -k https://localhost/api/v1/users
   ```

### Exercise 8: Service-to-Service Communication

1. **Create a complete order flow:**
   ```bash
   # Step 1: Create a user
   USER_RESPONSE=$(curl -sk -X POST https://localhost/api/v1/users \
     -H "Content-Type: application/json" \
     -d '{
       "username": "george",
       "email": "george@example.com"
     }')
   USER_ID=$(echo $USER_RESPONSE | jq -r '.id')
   
   # Step 2: Create a product
   PRODUCT_RESPONSE=$(curl -sk -X POST https://localhost/api/v1/products \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Test Product",
       "description": "Test description",
       "price": 99.99,
       "stock": 100,
       "category": "Test"
     }')
   PRODUCT_ID=$(echo $PRODUCT_RESPONSE | jq -r '.id')
   
   # Step 3: Create an order
   curl -k -X POST https://localhost/api/v1/orders \
     -H "Content-Type: application/json" \
     -d "{
       \"user_id\": $USER_ID,
       \"product_id\": $PRODUCT_ID,
       \"quantity\": 5,
       \"total_price\": 499.95
     }"
   ```

2. **Verify the complete flow in database:**
   ```bash
   docker exec -it postgres psql -U labuser -d labdb -c "
     SELECT 
       o.id as order_id,
       u.username,
       p.name as product,
       o.quantity,
       o.total_price,
       o.status
     FROM orders o
     JOIN users u ON o.user_id = u.id
     JOIN products p ON o.product_id = p.id
     WHERE u.username = 'george';"
   ```

### Exercise 9: Error Handling and Validation

1. **Test foreign key validation (invalid user_id):**
   ```bash
   curl -k -X POST https://localhost/api/v1/orders \
     -H "Content-Type: application/json" \
     -d '{
       "user_id": 9999,
       "product_id": 1,
       "quantity": 1,
       "total_price": 99.99
     }'
   ```
   Expected: Error message about invalid user_id

2. **Test invalid product_id:**
   ```bash
   curl -k -X POST https://localhost/api/v1/orders \
     -H "Content-Type: application/json" \
     -d '{
       "user_id": 1,
       "product_id": 9999,
       "quantity": 1,
       "total_price": 99.99
     }'
   ```
   Expected: Error message about invalid product_id

3. **Test duplicate username:**
   ```bash
   curl -k -X POST https://localhost/api/v1/users \
     -H "Content-Type: application/json" \
     -d '{
       "username": "alice",
       "email": "newalice@example.com"
     }'
   ```
   Expected: Error about duplicate username

4. **Test invalid order status:**
   ```bash
   curl -k -X PATCH https://localhost/api/v1/orders/1/status \
     -H "Content-Type: application/json" \
     -d '{
       "status": "invalid_status"
     }'
   ```

### Exercise 10: Performance Testing

1. **Test caching performance:**
   ```bash
   # Without cache (first call)
   time curl -k https://localhost/api/v1/products
   
   # With cache (second call)
   time curl -k https://localhost/api/v1/products
   ```

2. **Load test with Apache Bench:**
   ```bash
   # Install apache2-utils if needed
   # macOS: brew install httpd (ab comes with it)
   
   # Test User Service
   ab -n 1000 -c 10 -k https://localhost/api/v1/users
   
   # Test Product Service
   ab -n 1000 -c 10 -k https://localhost/api/v1/products
   ```

3. **Monitor service statistics during load:**
   ```bash
   # In another terminal, watch stats
   watch -n 1 'curl -sk https://localhost/api/v1/users/stats'
   ```

## Advanced Challenges

### Challenge 1: Implement User Authentication
- Add JWT token generation to User Service
- Require authentication token for Order creation
- Implement token validation middleware

### Challenge 2: Add Product Search
- Implement full-text search in Product Service
- Add search endpoint: `GET /api/v1/products/search?q=laptop`
- Use PostgreSQL full-text search or add Elasticsearch

### Challenge 3: Order Status Workflow
- Implement state machine for order status transitions
- Valid transitions: pending → processing → shipped → delivered
- Prevent invalid status changes

### Challenge 4: Real-time Notifications
- Add WebSocket support to Order Service
- Emit real-time updates when order status changes
- Create a simple web client to display notifications

### Challenge 5: API Rate Limiting per Service
- Implement rate limiting at the service level (not just Nginx)
- Add Redis-based rate limiting
- Return appropriate HTTP 429 responses

### Challenge 6: Distributed Tracing
- Add OpenTelemetry instrumentation to all services
- Set up Jaeger for distributed tracing
- Trace requests across User → Order → Product services

### Challenge 7: API Documentation
- Add Swagger/OpenAPI documentation to each service
- Create interactive API docs at `/api/docs`
- Document all endpoints, parameters, and responses

### Challenge 8: Implement Saga Pattern
- Create a complex order flow that updates product stock
- Implement compensating transactions for failures
- Handle rollback when order creation fails

## Monitoring Microservices

1. **Check service health through Nginx:**
   ```bash
   curl -k https://localhost/api/health
   ```

2. **Individual service health checks:**
   ```bash
   docker exec user-service curl -f http://localhost:5000/health
   docker exec product-service wget -q -O- http://localhost:3000/health
   docker exec order-service wget -q -O- http://localhost:8080/health
   ```

3. **View service metrics:**
   - Prometheus: http://localhost:9090
   - Grafana: http://localhost:3000
   - Add custom dashboards for microservices metrics

## Troubleshooting

### Services Won't Start
```bash
# Check logs
docker-compose logs user-service
docker-compose logs product-service
docker-compose logs order-service

# Check database connectivity
docker exec user-service curl -f http://localhost:5000/health
```

### Database Connection Issues
```bash
# Verify PostgreSQL is running
docker-compose ps postgres

# Check database logs
docker-compose logs postgres

# Test connection
docker exec postgres pg_isready -U labuser -d labdb
```

### Cache Not Working
```bash
# Check Redis status
docker exec redis redis-cli PING

# Monitor cache hits/misses
docker exec redis redis-cli MONITOR
```

### 502 Bad Gateway from Nginx
```bash
# Check if services are responding
docker exec -it reverse-proxy curl http://user-service:5000/health
docker exec -it reverse-proxy curl http://product-service:3000/health
docker exec -it reverse-proxy curl http://order-service:8080/health
```

## Cleanup

```bash
# Stop all services
docker-compose down

# Remove volumes (WARNING: deletes all data)
docker-compose down -v

# Remove images
docker-compose down --rmi all
```

## Key Learning Points

1. **Microservices Architecture**:
   - Service isolation and independence
   - API-based communication
   - Database per service pattern

2. **Caching Strategies**:
   - Time-based expiration (TTL)
   - Cache invalidation on writes
   - Performance optimization

3. **Database Design**:
   - Foreign key relationships
   - Indexes for performance
   - Data normalization

4. **API Design**:
   - RESTful conventions
   - Health check endpoints
   - Error handling and validation

5. **Technology Stack**:
   - Python/Flask (lightweight REST API)
   - Node.js/Express (async/await patterns)
   - Go (high-performance, concurrent)
   - PostgreSQL (relational data)
   - Redis (caching layer)

## Next Steps

- Complete Lab 1-6 for proxy, security, and monitoring foundations
- Experiment with the Advanced Challenges above
- Explore ENHANCEMENT_ROADMAP.md for additional features
- Consider adding message queues (RabbitMQ, Kafka) for async processing

---

**Lab 7 Complete!** You now have a fully functional microservices architecture with database, caching, and reverse proxy routing.
