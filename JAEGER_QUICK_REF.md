# Jaeger Distributed Tracing - Quick Reference

## 🎯 Quick Access

| Service | URL | Purpose |
|---------|-----|---------|
| **Jaeger UI** | http://localhost:16686 | Web interface for viewing traces |
| **Collector HTTP** | http://localhost:14268/api/traces | HTTP endpoint for trace submission |
| **Collector gRPC** | localhost:14250 | gRPC endpoint for trace submission |
| **Agent UDP** | localhost:6831 | UDP endpoint (Thrift compact) |
| **Zipkin Compatible** | http://localhost:9411 | Zipkin API compatibility |

---

## 📊 Key Concepts

### Trace Hierarchy
```
Trace (Complete request journey)
  └─ Span 1 (HTTP Request)
      └─ Span 2 (Database Query)
      └─ Span 3 (Redis Operation)
      └─ Span 4 (External API Call)
          └─ Span 5 (HTTP Request in another service)
```

### Span Attributes
- **Trace ID**: Unique ID for the entire request journey
- **Span ID**: Unique ID for this specific operation
- **Parent Span ID**: Links to the calling span
- **Duration**: Time taken for the operation
- **Tags**: Key-value metadata (http.method, db.statement, etc.)
- **Logs**: Timestamped events within the span

---

## 🚀 Generate Traces

### Automated Script
```bash
./test-tracing.sh
```

### Manual Testing
```bash
# User Service traces
curl -k https://localhost/api/v1/users
curl -k https://localhost/api/v1/users/1
curl -k https://localhost/api/v1/stats

# Product Service traces
curl -k https://localhost/api/v1/products
curl -k "https://localhost/api/v1/products?category=Electronics"
curl -k https://localhost/api/v1/products/1

# Order Service traces
curl -k https://localhost/api/v1/orders
curl -k https://localhost/api/v1/orders/1
curl -k https://localhost/api/v1/orders/stats

# Create order (cross-service trace)
curl -k -X POST https://localhost/api/v1/orders \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "product_id": 2, "quantity": 2}'
```

---

## 🔍 Jaeger UI Navigation

### 1. Search Traces
```
Service:    [Select: user-service, product-service, order-service]
Operation:  [Auto-populated based on service]
Tags:       http.status_code=200, error=true, etc.
Lookback:   Last hour / Last 2 hours / Custom
Min/Max:    Filter by duration
```

### 2. View Trace Details
- **Timeline View**: Horizontal bars showing span durations
- **Flame Graph**: Hierarchical view of nested spans
- **Span Details**: Click any span to see:
  - Tags (metadata)
  - Logs (events)
  - Process info
  - References (parent/child)

### 3. Service Dependencies
- Click **"System Architecture"** (graph icon)
- Select service to see dependencies
- View as DAG (Directed Acyclic Graph)

### 4. Compare Traces
- Select multiple traces (checkboxes)
- Click **"Compare"**
- View side-by-side timelines

---

## 📈 Common Search Patterns

### Find Slow Requests
```
Service: user-service
Operation: GET /api/v1/users/{id}
Min Duration: 100ms
```

### Find Errors
```
Tags: error=true
OR
Tags: http.status_code=500
```

### Find Database Heavy Operations
```
Service: user-service
Tags: db.system=postgresql
Min Duration: 50ms
```

### Find Cache Misses
```
Service: user-service
Tags: cache.hit=false
```

---

## 🎯 Performance Analysis

### Typical Request Breakdown

**Fast Request (Cache Hit):**
```
Total: 10ms
├─ HTTP Handler:     2ms (20%)
├─ Redis GET:        1ms (10%)
└─ Response:         7ms (70%)
```

**Slow Request (Cache Miss):**
```
Total: 85ms
├─ HTTP Handler:     5ms (6%)
├─ Redis GET:        1ms (1%)  ← Cache miss
├─ Database Query:   60ms (71%)
├─ Redis SET:        2ms (2%)
└─ Response:         17ms (20%)
```

### Identify Bottlenecks
1. Look for longest spans (dark/thick bars)
2. Check P95/P99 latencies
3. Compare similar operations
4. Look for sequential vs parallel operations

---

## 🐛 Debugging Workflows

### Workflow 1: Find the Root Cause of Slow Request
1. Search for traces with `Min Duration: 500ms`
2. Click on slowest trace
3. Expand all spans
4. Identify the longest span(s)
5. Check span tags for details:
   - `db.statement` - What query?
   - `db.rows_affected` - How many rows?
   - `http.url` - Which endpoint?

### Workflow 2: Debug Failed Request
1. Search with `Tags: error=true`
2. Look for red spans (errors)
3. Click error span
4. Check **Logs** tab for error messages
5. Trace back to see where it originated
6. Check parent spans for context

### Workflow 3: Understand Cross-Service Flow
1. Create an order to trigger multiple services
2. Find the trace in Jaeger
3. Expand all spans
4. Notice:
   - order-service → validates user
   - May call user-service HTTP endpoint
   - Each service has its own DB/Redis spans

---

## 📊 Metrics to Track

### Latency Percentiles
- **P50 (Median)**: What most users experience
- **P95**: What 5% of users experience (worse case)
- **P99**: Outliers (may indicate problems)
- **Max**: Absolute worst case

### Error Rate
```
error_traces / total_traces * 100
```

### Cache Hit Ratio
```
(cache_hits / total_requests) * 100
```

### Service Dependencies
- How many services does each request touch?
- Are there circular dependencies?
- Can we reduce hops?

---

## 🔧 Troubleshooting

### No Traces Appearing

```bash
# Check Jaeger is running
docker ps | grep jaeger

# Check Jaeger UI
curl http://localhost:16686

# Check service logs for tracing messages
docker logs user-service | grep -i "tracing initialized"
docker logs product-service | grep -i "tracing initialized"
docker logs order-service | grep -i "tracing initialized"

# Check network connectivity
docker exec user-service ping -c 1 jaeger
```

### Traces Missing Spans

**Problem:** Incomplete traces with missing operations

**Solutions:**
- Verify auto-instrumentation is enabled
- Check that HTTP clients propagate context
- Ensure database drivers are instrumented
- Look for errors in service logs

### High Latency on Tracing

**Problem:** Tracing adds too much overhead

**Solutions:**
```python
# Python: Reduce sampling
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased
sampler = TraceIdRatioBased(0.1)  # Sample 10%
```

```javascript
// Node.js: Batch configuration
const provider = new NodeSDK({
  spanProcessor: new BatchSpanProcessor(exporter, {
    maxQueueSize: 100,
    scheduledDelayMillis: 5000,
  }),
});
```

---

## 🎓 Best Practices

### DO ✅
- **Always propagate context** across service boundaries
- **Add meaningful tags** to spans (user_id, order_id, etc.)
- **Sample intelligently** in production (not 100%)
- **Always trace errors** for debugging
- **Use consistent naming** for operations
- **Add business context** (e.g., cart_value, payment_method)

### DON'T ❌
- **Don't log sensitive data** in spans (passwords, credit cards)
- **Don't trace every single operation** (too noisy)
- **Don't ignore context propagation** (breaks traces)
- **Don't use high sampling** in production (performance hit)
- **Don't forget to shut down** TracerProvider on exit

---

## 📝 Span Naming Conventions

### Good Names ✅
```
GET /api/v1/users/{id}
db.query.users.select
redis.get.user:123
http.client.user-service
validate_user_credentials
```

### Bad Names ❌
```
function_1
query
get
operation
request
```

---

## 🚀 Advanced Features

### Custom Attributes
```python
# Python
span = trace.get_current_span()
span.set_attribute("user.id", user_id)
span.set_attribute("cache.hit", True)
span.set_attribute("db.rows_returned", len(users))
```

### Span Events (Logs)
```python
# Python
span.add_event("cache_miss", {
    "key": cache_key,
    "ttl": 60
})
```

### Manual Span Creation
```python
# Python
with tracer.start_as_current_span("validate_order") as span:
    span.set_attribute("order.id", order_id)
    span.set_attribute("order.total", total_price)
    # Your validation logic
```

---

## 📊 Example Queries

### Find All Errors from Last Hour
```
Service: (Any)
Tags: error=true
Lookback: Last Hour
```

### Find Slow Database Queries
```
Service: user-service
Tags: db.system=postgresql
Min Duration: 100ms
```

### Find Requests from Specific User
```
Tags: user.id=1
```

### Find All POST Requests
```
Tags: http.method=POST
```

### Find Requests with Cache Misses
```
Tags: cache.hit=false
```

---

## 🎯 Common Trace Patterns

### Pattern 1: Read Through Cache
```
HTTP Request [50ms]
  ├─ Redis GET [1ms] ← Hit: Return cached
  └─ (No database span)
```

### Pattern 2: Cache Miss
```
HTTP Request [120ms]
  ├─ Redis GET [1ms] ← Miss
  ├─ Database SELECT [80ms]
  └─ Redis SET [2ms] ← Write to cache
```

### Pattern 3: Write Operation
```
HTTP POST [150ms]
  ├─ Validate Input [5ms]
  ├─ Database INSERT [100ms]
  └─ Redis DEL [2ms] ← Invalidate cache
```

### Pattern 4: Cross-Service Call
```
Order Service: POST /orders [200ms]
  ├─ Validate User [80ms]
  │   └─ HTTP GET user-service [75ms]
  │       └─ User Service: GET /users/1 [70ms]
  ├─ Database INSERT [100ms]
  └─ Response [20ms]
```

---

## 🔗 Useful Links

- **Jaeger UI**: http://localhost:16686
- **Lab Guide**: [LAB_08_DISTRIBUTED_TRACING.md](./LAB_08_DISTRIBUTED_TRACING.md)
- **Official Docs**: https://www.jaegertracing.io/docs/
- **OpenTelemetry**: https://opentelemetry.io/

---

**Quick Tip:** Press `Ctrl+K` in Jaeger UI to see keyboard shortcuts!
