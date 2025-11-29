# Lab 8: Distributed Tracing with Jaeger

## 📚 Overview

This lab introduces **distributed tracing** with Jaeger to visualize and debug request flows across your microservices architecture. You'll learn how to trace requests from the API gateway through User Service, Product Service, and Order Service.

**Duration:** 45-60 minutes  
**Difficulty:** Intermediate  
**Prerequisites:** Lab 7 (Microservices Architecture)

---

## 🎯 Learning Objectives

After completing this lab, you will:

1. Understand distributed tracing concepts and terminology
2. Configure OpenTelemetry instrumentation for multiple languages
3. Visualize request flows across microservices
4. Identify performance bottlenecks using trace data
5. Debug complex distributed system issues
6. Understand span relationships and context propagation

---

## 📖 Concepts

### What is Distributed Tracing?

**Distributed tracing** tracks requests as they flow through multiple services, creating a complete picture of:
- Request path and timing
- Service dependencies
- Performance bottlenecks
- Error propagation

### Key Terminology

| Term | Definition |
|------|------------|
| **Trace** | Complete journey of a request through all services |
| **Span** | Single operation within a trace (e.g., database query) |
| **Context Propagation** | Passing trace information between services |
| **Trace ID** | Unique identifier for the entire request journey |
| **Span ID** | Unique identifier for a single operation |
| **Parent Span** | The span that initiated a child operation |

### Architecture

```
Client Request
    │
    ▼
[Nginx Reverse Proxy]
    │
    ├──▶ [User Service (Python)]
    │       ├─▶ [PostgreSQL Query]
    │       └─▶ [Redis Cache]
    │
    ├──▶ [Product Service (Node.js)]
    │       ├─▶ [PostgreSQL Query]
    │       └─▶ [Redis Cache]
    │
    └──▶ [Order Service (Go)]
            ├─▶ [PostgreSQL Query]
            ├─▶ [Redis Cache]
            └─▶ [User Service Call]  ← Service-to-service
            
All services send traces to:
    ▼
[Jaeger Collector]
    ▼
[Jaeger Storage]
    ▼
[Jaeger UI (Port 16686)]
```

---

## 🚀 Getting Started

### Step 1: Verify Jaeger is Running

```bash
# Check Jaeger container
docker ps | grep jaeger

# Check Jaeger health
curl http://localhost:16686
```

**Expected:** Jaeger UI should be accessible at http://localhost:16686

### Step 2: Access Jaeger UI

Open your browser and navigate to:
```
http://localhost:16686
```

You should see the Jaeger UI with a service dropdown menu.

---

## 🔬 Exercises

### Exercise 1: Generate Sample Traces

**Objective:** Create traces by making API requests

```bash
# 1. Get all users (User Service)
curl -k https://localhost/api/v1/users

# 2. Get a specific user
curl -k https://localhost/api/v1/users/1

# 3. Get all products (Product Service)
curl -k https://localhost/api/v1/products

# 4. Get products by category
curl -k "https://localhost/api/v1/products?category=Electronics"

# 5. Create an order (Order Service)
curl -k -X POST https://localhost/api/v1/orders \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "product_id": 2,
    "quantity": 2
  }'

# 6. Get order statistics
curl -k https://localhost/api/v1/orders/stats
```

**Task:** Make at least 10-15 requests across all three services.

---

### Exercise 2: View Traces in Jaeger

**Objective:** Learn to navigate and analyze traces

1. **Open Jaeger UI** at http://localhost:16686

2. **Select a Service:**
   - Choose `user-service` from the "Service" dropdown
   - Click "Find Traces"

3. **Explore a Trace:**
   - Click on any trace in the results
   - Observe the timeline view
   - Expand spans to see details

4. **Questions to Answer:**
   - How many spans are in a typical GET request?
   - What's the total request duration?
   - How much time was spent on database queries?
   - How much time was spent on Redis operations?

---

### Exercise 3: Analyze Service Dependencies

**Objective:** Understand service relationships

1. **View System Architecture:**
   - In Jaeger UI, click "System Architecture" (graph icon)
   - Select service: `user-service`
   - Click "DAG" (Directed Acyclic Graph)

2. **Observations:**
   ```
   user-service → postgres
   user-service → redis
   
   product-service → postgres
   product-service → redis
   
   order-service → postgres
   order-service → redis
   order-service → user-service (potential)
   ```

3. **Questions:**
   - Which service has the most dependencies?
   - Are there any circular dependencies?
   - What's the maximum depth of the call chain?

---

### Exercise 4: Compare Cached vs Uncached Requests

**Objective:** See the performance impact of caching

```bash
# 1. Make first request (cache miss)
time curl -k https://localhost/api/v1/users

# 2. Immediately make second request (cache hit)
time curl -k https://localhost/api/v1/users

# 3. Compare traces in Jaeger
# - First trace should have database span
# - Second trace should be faster (cache hit)
```

**Analysis in Jaeger:**
1. Find both traces (sort by time)
2. Compare total durations
3. Notice missing database span in cached request
4. Calculate time savings

**Expected Results:**
- First request: ~50-200ms (database + cache write)
- Second request: ~5-20ms (cache only)
- Speedup: 10-40x faster

---

### Exercise 5: Identify Performance Bottlenecks

**Objective:** Find slow operations

```bash
# Create a complex order that requires multiple lookups
curl -k -X POST https://localhost/api/v1/orders \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "product_id": 5,
    "quantity": 10
  }'
```

**In Jaeger:**
1. Find the trace for POST /api/v1/orders
2. Look at the flame graph
3. Identify the slowest span
4. Check if it's:
   - Database query
   - Redis operation
   - HTTP request
   - Business logic

**Performance Metrics to Note:**
```
Total Duration:     ___ ms
Database Time:      ___ ms (___ %)
Redis Time:         ___ ms (___ %)
Business Logic:     ___ ms (___ %)
```

---

### Exercise 6: Trace Error Propagation

**Objective:** See how errors appear in traces

```bash
# 1. Try to create order with invalid user
curl -k -X POST https://localhost/api/v1/orders \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 99999,
    "product_id": 1,
    "quantity": 1
  }'

# 2. Try to get non-existent user
curl -k https://localhost/api/v1/users/99999

# 3. Try to create user with duplicate email
curl -k -X POST https://localhost/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "john.doe@example.com"
  }'
```

**In Jaeger:**
1. Find the error traces (they'll be marked in red)
2. Click on the error span
3. Examine the "Logs" tab
4. Look for error messages and stack traces

**Questions:**
- At what point did the error occur?
- Which service caught the error?
- Was the error propagated upstream?
- What HTTP status code was returned?

---

### Exercise 7: Monitor Request Latency Distribution

**Objective:** Understand performance patterns

```bash
# Generate load with mixed operations
for i in {1..50}; do
  curl -k https://localhost/api/v1/users/$((RANDOM % 4 + 1)) &
  curl -k https://localhost/api/v1/products?category=Electronics &
  curl -k https://localhost/api/v1/orders &
done
wait
```

**In Jaeger:**
1. Go to "Compare" view
2. Select `user-service` with operation `GET /api/v1/users/{id}`
3. View the latency distribution
4. Identify:
   - P50 (median): ___ ms
   - P95: ___ ms
   - P99: ___ ms
   - Max: ___ ms

---

## 🔍 Advanced Scenarios

### Scenario 1: Cross-Service Trace

**Create an order that requires user validation:**

```bash
# This should trigger: Order Service → User Service → Database
curl -k -X POST https://localhost/api/v1/orders \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 2,
    "product_id": 3,
    "quantity": 1
  }'
```

**Trace Analysis:**
```
order-service: POST /api/v1/orders
    ├─▶ order-service: validate_user
    │   └─▶ HTTP GET user-service/api/v1/users/2
    │       └─▶ user-service: database query
    ├─▶ order-service: validate_product
    │   └─▶ order-service: database query
    └─▶ order-service: create_order
        └─▶ order-service: database insert
```

---

### Scenario 2: High Load Testing

**Generate significant load and analyze:**

```bash
# Install apache bench (if not installed)
# macOS: brew install httpd
# Linux: apt-get install apache2-utils

# Load test user service
ab -n 1000 -c 10 -k https://localhost/api/v1/users

# Load test product service
ab -n 1000 -c 10 -k https://localhost/api/v1/products
```

**Jaeger Analysis:**
1. Filter traces by time range
2. Look for outliers (very slow requests)
3. Check for error rate spikes
4. Analyze resource saturation

---

### Scenario 3: Cache Warming

**See the impact of cache warming:**

```bash
# 1. Warm up the cache
for i in {1..4}; do
  curl -k https://localhost/api/v1/users/$i > /dev/null 2>&1
done

# 2. Generate load (should be fast due to cache)
ab -n 500 -c 10 -k https://localhost/api/v1/users/1

# 3. Compare with cold cache
docker exec redis redis-cli FLUSHALL

ab -n 500 -c 10 -k https://localhost/api/v1/users/1
```

**Comparison:**
- Warm cache P95: ___ ms
- Cold cache P95: ___ ms
- Improvement: ___ %

---

## 📊 Jaeger UI Features

### 1. Search & Filters

```
Service: user-service
Operation: GET /api/v1/users/{id}
Tags: http.status_code=200
Min Duration: 50ms
Max Duration: 500ms
Limit Results: 20
```

### 2. Trace Comparison

- Select multiple traces
- Click "Compare"
- View side-by-side timeline
- Identify differences

### 3. Span Details

Each span shows:
- **Duration:** Time taken
- **Tags:** Metadata (HTTP method, status, etc.)
- **Logs:** Events within the span
- **Process:** Service information
- **References:** Parent/child relationships

### 4. Deep Links

Share specific traces:
```
http://localhost:16686/trace/{trace-id}
```

---

## 🐛 Common Issues & Solutions

### Issue 1: No Traces Appearing

**Symptoms:** Jaeger UI is empty

**Solutions:**
```bash
# Check if services are sending traces
docker logs user-service | grep -i tracing
docker logs product-service | grep -i tracing
docker logs order-service | grep -i tracing

# Check Jaeger collector logs
docker logs jaeger

# Verify network connectivity
docker exec user-service ping -c 3 jaeger
```

### Issue 2: Incomplete Traces

**Symptoms:** Missing spans or broken traces

**Solutions:**
- Check that all services use the same trace context format
- Verify context propagation headers (traceparent, uber-trace-id)
- Ensure all HTTP clients propagate trace context

### Issue 3: High Sampling Rate Impact

**Symptoms:** Performance degradation

**Solution:** Adjust sampling rate in production
```python
# Python: Reduce sampling
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased
sampler = TraceIdRatioBased(0.1)  # Sample 10% of traces
```

---

## 🎓 Key Takeaways

1. **Trace Everything:** Instrument all service boundaries
2. **Context is King:** Always propagate trace context
3. **Tags Add Value:** Add meaningful tags to spans
4. **Sample Intelligently:** Not every request needs to be traced
5. **Error Traces Matter:** Always trace errors for debugging
6. **Performance Insight:** Use traces to find optimization opportunities

---

## 📝 Lab Questions

1. What's the average response time for GET /api/v1/users?
2. How much faster is a cached request vs uncached?
3. Which service has the highest latency?
4. What percentage of time is spent on database operations?
5. How many services does a typical order creation touch?
6. What happens when Redis is unavailable?
7. Can you identify any N+1 query problems?
8. What's the P99 latency for your slowest endpoint?

---

## 🚀 Next Steps

After completing this lab, you can:

1. **Add Custom Spans:**
   ```python
   with tracer.start_as_current_span("custom_operation"):
       # Your code here
       pass
   ```

2. **Add Span Attributes:**
   ```python
   span = trace.get_current_span()
   span.set_attribute("user.id", user_id)
   span.set_attribute("cache.hit", True)
   ```

3. **Implement Sampling Strategies:**
   - Always sample errors
   - Sample 100% of slow requests
   - Sample 1% of fast, successful requests

4. **Create Custom Dashboards:**
   - Export trace data
   - Build Grafana dashboards
   - Set up alerts

---

## 📚 Additional Resources

- [OpenTelemetry Documentation](https://opentelemetry.io/)
- [Jaeger Documentation](https://www.jaegertracing.io/docs/)
- [Distributed Tracing Best Practices](https://opentelemetry.io/docs/concepts/observability-primer/)
- [Instrumentation Guide](https://opentelemetry.io/docs/instrumentation/)

---

## 🎯 Challenge

**Build a Complete Request Journey:**

Create a single API request that:
1. Creates a new user (User Service)
2. Creates a new product (Product Service)  
3. Creates an order linking them (Order Service)
4. Verify the entire flow in Jaeger with one trace ID

**Bonus:** Add custom spans for business logic steps like "validate_inventory" or "calculate_discount"

---

**Congratulations!** 🎉 You've mastered distributed tracing with Jaeger!

**Next Lab:** Lab 9 - CI/CD Pipeline with GitHub Actions
