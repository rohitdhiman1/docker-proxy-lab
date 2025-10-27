# Docker Proxy Lab - Advanced Edition

This comprehensive lab provides hands-on experience with **forward proxy**, **reverse proxy**, **security**, **monitoring**, and **logging** using Docker containers. Perfect for learning modern web infrastructure patterns and DevOps practices.

---

## 📋 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [Quick Start](#quick-start)
4. [Lab 1: Forward Proxy with Squid](#lab-1-forward-proxy-with-squid)
5. [Lab 2: Reverse Proxy with Nginx](#lab-2-reverse-proxy-with-nginx)
6. [Lab 3: Security & Authentication](#lab-3-security--authentication)
7. [Lab 4: Advanced Proxy Features](#lab-4-advanced-proxy-features)
8. [Lab 5: Monitoring with Prometheus & Grafana](#lab-5-monitoring-with-prometheus--grafana)
9. [Lab 6: Centralized Logging with ELK Stack](#lab-6-centralized-logging-with-elk-stack)
10. [Troubleshooting](#troubleshooting)
11. [Cleanup](#cleanup)

---

## Architecture Overview

### Services Deployed

- **Forward Proxy**: Squid proxy with ACLs and caching
- **Reverse Proxy**: Nginx with SSL/TLS, load balancing, and rate limiting
- **Backend Servers**: 4 nginx servers for load balancing demonstration
- **Monitoring**: Prometheus + Grafana + Nginx Exporter
- **Logging**: ELK Stack (Elasticsearch, Logstash, Kibana)

### Network Architecture

```
Client → Squid Proxy → Internet (Forward Proxy)
Client → Nginx (HTTPS) → Backend Servers (Reverse Proxy)
All services → Prometheus → Grafana (Monitoring)
All services → Logstash → Elasticsearch → Kibana (Logging)
```

---

## Prerequisites

- Docker Desktop or Docker Engine installed
- Docker Compose v3.8+
- At least 4GB RAM available for Docker
- Ports available: 80, 443, 3000, 3128, 5601, 8080-8085, 9090, 9200

---

## Quick Start

### 1. Clone and Setup

```bash
git clone <repo-url>
cd docker-proxy-lab
```

### 2. Generate SSL Certificates

```bash
cd certs
chmod +x generate-certs.sh
./generate-certs.sh
cd ..
```

### 3. Start All Services

```bash
docker-compose up -d
```

### 4. Verify Services

```bash
docker-compose ps
```

All services should show as "Up" and "healthy".

---

## Lab 1: Forward Proxy with Squid

### Learning Objectives
- Understand forward proxy concepts
- Configure ACLs to block/allow domains
- Demonstrate caching for performance

### Step-by-Step Instructions

#### Step 1: Verify Squid is Running

```bash
docker ps | grep squid-proxy
```

#### Step 2: Access the Client Container

```bash
docker exec -it client sh
```

#### Step 3: Test Proxy Access to Allowed Domain

```bash
curl -x http://squid-proxy:3128 http://web-server
```

**Expected**: You should see the nginx welcome page.

#### Step 4: Test Blocked Domain

```bash
curl -x http://squid-proxy:3128 http://www.facebook.com
```

**Expected**: Access denied (403 Forbidden).

#### Step 5: Test Allowed External Domain

```bash
curl -x http://squid-proxy:3128 -I https://www.google.com
```

**Expected**: Successful response with headers.

#### Step 6: View Cache Statistics

```bash
docker exec squid-proxy squidclient mgr:info
```

#### Step 7: Test Caching

Make the same request twice and observe cache hits:

```bash
# First request (cache MISS)
curl -x http://squid-proxy:3128 -I http://web-server

# Second request (cache HIT)
curl -x http://squid-proxy:3128 -I http://web-server
```

#### Step 8: Check Squid Logs

```bash
docker exec squid-proxy tail -f /var/log/squid/access.log
```

### Key Learnings

✅ Forward proxy controls **outbound** traffic  
✅ ACLs provide domain-level access control  
✅ Caching improves performance and reduces bandwidth  
✅ Clients must be configured to use the proxy

---

## Lab 2: Reverse Proxy with Nginx

### Learning Objectives
- Understand reverse proxy patterns
- Configure SSL/TLS termination
- Implement load balancing

### Step-by-Step Instructions

#### Step 1: Test HTTP to HTTPS Redirect

```bash
curl -I http://localhost
```

**Expected**: 301 redirect to HTTPS.

#### Step 2: Test HTTPS Access (Accept Self-Signed Cert)

```bash
curl -k https://localhost
```

**Expected**: See one of the backend server responses (load balanced).

#### Step 3: Test Load Balancing

Run multiple requests to see different backends:

```bash
for i in {1..8}; do curl -k https://localhost 2>/dev/null | grep "Backend Server"; done
```

**Expected**: You'll see responses from different backend servers (1-4) due to load balancing.

#### Step 4: Test Specific Backend Access

```bash
curl -k https://localhost/backend1/
curl -k https://localhost/backend2/
curl -k https://localhost/backend3/
curl -k https://localhost/backend4/
```

#### Step 5: View in Browser

Open your browser and navigate to:
- `https://localhost` (accept the self-signed certificate warning)

Refresh multiple times to see different backends responding.

#### Step 6: Check Nginx Status

```bash
docker exec reverse-proxy curl http://localhost/nginx_status
```

### Key Learnings

✅ Reverse proxy handles **inbound** traffic  
✅ SSL/TLS termination at proxy layer  
✅ Clients don't know about backend servers  
✅ Load balancing distributes traffic across backends

---

## Lab 3: Security & Authentication

### Learning Objectives
- Implement SSL/TLS with self-signed certificates
- Configure HTTP Basic Authentication
- Apply security headers
- Implement rate limiting

### Step-by-Step Instructions

#### Step 1: Verify SSL Certificate

```bash
openssl s_client -connect localhost:443 -showcerts < /dev/null
```

**Expected**: See certificate details with CN=localhost.

#### Step 2: Enable Basic Authentication

Edit `nginx/nginx.conf` and uncomment these lines:

```nginx
auth_basic "Restricted Access";
auth_basic_user_file /etc/nginx/.htpasswd;
```

Restart nginx:

```bash
docker-compose restart reverse-proxy
```

#### Step 3: Test Authentication

Without credentials:
```bash
curl -k https://localhost
```

**Expected**: 401 Unauthorized.

With credentials:
```bash
curl -k -u admin:admin123 https://localhost
```

**Expected**: Successful response.

#### Step 4: Test Rate Limiting

Send rapid requests to trigger rate limit:

```bash
for i in {1..30}; do curl -k https://localhost -w "%{http_code}\n" -o /dev/null -s; done
```

**Expected**: You'll see some 503 (Service Unavailable) responses when rate limit is exceeded.

#### Step 5: Check Security Headers

```bash
curl -k -I https://localhost
```

Look for these headers:
- `Strict-Transport-Security`
- `X-Frame-Options`
- `X-Content-Type-Options`
- `X-XSS-Protection`

### Key Learnings

✅ Self-signed certificates for testing (use CA-signed in production)  
✅ Basic Auth provides simple authentication  
✅ Security headers protect against common attacks  
✅ Rate limiting prevents abuse and DDoS

---

## Lab 4: Advanced Proxy Features

### Learning Objectives
- Understand load balancing algorithms
- Implement health checks
- Configure sticky sessions
- Monitor upstream server health

### Step-by-Step Instructions

#### Step 1: View Current Load Balancing Algorithm

The nginx config uses `least_conn` (least connections). Check the config:

```bash
docker exec reverse-proxy cat /etc/nginx/nginx.conf | grep -A 5 "upstream backend_pool"
```

#### Step 2: Test Load Balancing Distribution

```bash
for i in {1..20}; do 
  curl -k -s https://localhost | grep -o "Backend Server [0-9]"
  sleep 0.5
done
```

**Expected**: Relatively even distribution across all 4 backends.

#### Step 3: Simulate Backend Failure

Stop one backend:

```bash
docker stop backend3
```

#### Step 4: Verify Health Check and Failover

```bash
for i in {1..10}; do 
  curl -k -s https://localhost | grep -o "Backend Server [0-9]"
done
```

**Expected**: No responses from backend3. Traffic distributed to healthy backends only.

#### Step 5: Restart Failed Backend

```bash
docker start backend3
```

Wait 30 seconds for health check to pass, then test again.

#### Step 6: Test Sticky Sessions (IP Hash)

```bash
for i in {1..5}; do 
  curl -k -s https://localhost/sticky/ | grep -o "Backend Server [0-9]"
done
```

**Expected**: Same backend for all requests from your IP.

#### Step 7: View Backend Health Status

```bash
docker-compose ps
```

Check the "State" column for health status.

#### Step 8: Check Upstream Statistics

```bash
docker exec reverse-proxy cat /var/log/nginx/access.log | tail -20
```

Look at the `urt` (upstream response time) values.

### Key Learnings

✅ **least_conn**: Routes to server with fewest active connections  
✅ **ip_hash**: Ensures same client always hits same backend (sticky sessions)  
✅ Health checks automatically remove failed backends  
✅ `max_fails` and `fail_timeout` configure failure detection

---

## Lab 5: Monitoring with Prometheus & Grafana

### Learning Objectives
- Collect metrics with Prometheus
- Visualize metrics with Grafana
- Monitor Nginx performance
- Set up dashboards

### Step-by-Step Instructions

#### Step 1: Access Prometheus

Open browser: `http://localhost:9090`

#### Step 2: Verify Targets

Navigate to: **Status → Targets**

**Expected**: All targets (nginx, backends, prometheus) should be "UP".

#### Step 3: Query Nginx Metrics

In the Prometheus query box, try:

```promql
nginx_http_requests_total
```

Click "Execute" and view the graph.

#### Step 4: More Useful Queries

**Request rate (per second)**:
```promql
rate(nginx_http_requests_total[1m])
```

**Active connections**:
```promql
nginx_connections_active
```

**Response times** (from logs):
```promql
histogram_quantile(0.95, rate(nginx_http_request_duration_seconds_bucket[5m]))
```

#### Step 5: Access Grafana

Open browser: `http://localhost:3000`

**Credentials**: 
- Username: `admin`
- Password: `admin`

#### Step 6: Import Nginx Dashboard

1. Click "+" → "Import"
2. Enter dashboard ID: `12708` (Nginx Prometheus Exporter)
3. Click "Load"
4. Select "Prometheus" as data source
5. Click "Import"

#### Step 7: Generate Traffic for Metrics

```bash
for i in {1..100}; do 
  curl -k https://localhost -w "\n" -o /dev/null -s
  sleep 0.1
done
```

#### Step 8: View Real-Time Metrics

Refresh the Grafana dashboard to see:
- Request rate
- Response times
- Active connections
- HTTP status codes distribution

#### Step 9: Create Custom Dashboard

1. Click "+" → "Dashboard"
2. Click "Add new panel"
3. Enter query: `rate(nginx_http_requests_total[1m])`
4. Customize visualization
5. Click "Apply" and "Save"

### Key Learnings

✅ Prometheus scrapes metrics from exporters  
✅ PromQL is powerful for querying time-series data  
✅ Grafana provides beautiful visualizations  
✅ Pre-built dashboards save time

---

## Lab 6: Centralized Logging with ELK Stack

### Learning Objectives
- Collect logs with Logstash
- Store logs in Elasticsearch
- Visualize logs with Kibana
- Create log queries and dashboards

### Step-by-Step Instructions

#### Step 1: Verify ELK Stack is Running

```bash
docker-compose ps | grep -E "elasticsearch|logstash|kibana"
```

**Expected**: All three services should be "Up" and "healthy".

#### Step 2: Check Elasticsearch Health

```bash
curl http://localhost:9200/_cluster/health?pretty
```

**Expected**: `"status": "yellow"` or `"green"`.

#### Step 3: Access Kibana

Open browser: `http://localhost:5601`

**Note**: Kibana may take 2-3 minutes to fully start.

#### Step 4: Generate Log Data

```bash
for i in {1..50}; do 
  curl -k https://localhost
  sleep 0.2
done
```

#### Step 5: Create Index Pattern

1. In Kibana, go to **Management → Stack Management**
2. Click **Index Patterns** (under Kibana)
3. Click **Create index pattern**
4. Enter pattern: `logs-*`
5. Click **Next step**
6. Select time field: `@timestamp`
7. Click **Create index pattern**

#### Step 6: Explore Logs

1. Click **Discover** (left menu)
2. Select `logs-*` index pattern
3. You should see nginx access logs

#### Step 7: Filter Logs

Try these filters:

**Show only successful requests:**
```
status: 200
```

**Show errors:**
```
status >= 400
```

**Show specific backend:**
```
message: *backend1*
```

#### Step 8: Create Visualizations

**Request Status Pie Chart:**
1. Click **Visualize** → **Create visualization**
2. Choose **Pie chart**
3. Select `logs-*` index
4. Buckets: Add bucket → Split slices
5. Aggregation: Terms, Field: status.keyword
6. Click **Update**
7. Save visualization

**Requests Over Time:**
1. Create new visualization → **Line chart**
2. Y-axis: Count
3. X-axis: Date Histogram, Field: @timestamp
4. Click **Update**
5. Save visualization

#### Step 9: Create Dashboard

1. Click **Dashboard** → **Create dashboard**
2. Click **Add** → Select your saved visualizations
3. Arrange and resize panels
4. Click **Save**

#### Step 10: View Log Details

Click on any log entry to see:
- Remote IP
- Request method and path
- Response status
- Response time
- User agent
- Referrer

### Key Learnings

✅ Logstash parses and enriches log data  
✅ Elasticsearch provides fast log search  
✅ Kibana enables log visualization and analysis  
✅ Centralized logging essential for troubleshooting

---

## Port Reference

| Service | Port | Purpose |
|---------|------|---------|
| Nginx HTTP | 80 | HTTP (redirects to HTTPS) |
| Nginx HTTPS | 443 | SSL/TLS terminated reverse proxy |
| Squid Proxy | 3128 | Forward proxy |
| Grafana | 3000 | Monitoring dashboards |
| Kibana | 5601 | Log visualization |
| Web Server | 8080 | Test web server |
| Backend 1 | 8082 | Direct backend access |
| Backend 2 | 8083 | Direct backend access |
| Backend 3 | 8084 | Direct backend access |
| Backend 4 | 8085 | Direct backend access |
| Prometheus | 9090 | Metrics collection |
| Nginx Exporter | 9113 | Nginx metrics |
| Elasticsearch | 9200 | Log storage |

---

## File Structure

```
.
├── docker-compose.yml          # Main orchestration file
├── README.md                   # This file
├── .gitignore                  # Git ignore rules
├── certs/
│   ├── generate-certs.sh       # SSL certificate generator
│   ├── .htpasswd              # Basic auth credentials
│   ├── nginx-selfsigned.crt   # Generated SSL cert
│   └── nginx-selfsigned.key   # Generated SSL key
├── nginx/
│   └── nginx.conf             # Reverse proxy configuration
├── squid/
│   └── squid.conf             # Forward proxy configuration
├── backend1/
│   └── index.html             # Backend 1 content
├── backend2/
│   └── index.html             # Backend 2 content
├── backend3/
│   └── index.html             # Backend 3 content
├── backend4/
│   └── index.html             # Backend 4 content
├── prometheus/
│   └── prometheus.yml         # Prometheus configuration
├── grafana/
│   └── datasource.yml         # Grafana data source
└── logstash/
    └── logstash.conf          # Logstash pipeline
```

---

## Troubleshooting

### Issue: Containers won't start

**Solution:**
```bash
docker-compose down
docker-compose up -d
docker-compose logs -f
```

### Issue: Port already in use

**Solution:**
```bash
# Check what's using the port
lsof -i :443
# Kill the process or change the port in docker-compose.yml
```

### Issue: SSL certificate errors

**Solution:**
```bash
cd certs
./generate-certs.sh
docker-compose restart reverse-proxy
```

### Issue: ELK Stack consuming too much memory

**Solution:** Reduce memory limits in docker-compose.yml:
```yaml
ES_JAVA_OPTS: "-Xms256m -Xmx256m"
LS_JAVA_OPTS: "-Xms128m -Xmx128m"
```

### Issue: Health checks failing

**Solution:**
```bash
# Check container logs
docker-compose logs [service-name]

# Restart specific service
docker-compose restart [service-name]
```

### Issue: No logs in Kibana

**Solution:**
```bash
# Check logstash is processing logs
docker-compose logs logstash

# Verify elasticsearch has data
curl "http://localhost:9200/logs-*/_count?pretty"

# Refresh index pattern in Kibana
```

---

## Cleanup

### Stop all services:
```bash
docker-compose down
```

### Remove volumes (deletes all data):
```bash
docker-compose down -v
```

### Remove images:
```bash
docker-compose down --rmi all
```

### Complete cleanup:
```bash
docker-compose down -v --rmi all
rm -rf certs/*.crt certs/*.key
```

---

## Advanced Exercises

### Exercise 1: Implement Circuit Breaker
Modify nginx.conf to add circuit breaker pattern with upstream timeouts.

### Exercise 2: Add More Security
- Implement fail2ban for brute force protection
- Add CORS headers
- Configure Content Security Policy

### Exercise 3: Custom Metrics
- Add custom application metrics
- Create alerting rules in Prometheus
- Set up Grafana alerts

### Exercise 4: Log Analysis
- Create complex Kibana queries
- Set up log-based alerts
- Analyze response time patterns

### Exercise 5: Multi-Environment Setup
- Create separate configs for dev/staging/prod
- Use environment variables for configuration
- Implement blue-green deployment

---

## References

- [Nginx Documentation](https://nginx.org/en/docs/)
- [Squid Proxy Documentation](http://www.squid-cache.org/Doc/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Elastic Stack Documentation](https://www.elastic.co/guide/)
- [Docker Compose Reference](https://docs.docker.com/compose/)

---

## Contributing

Feel free to submit issues and enhancement requests!

## License

MIT License - feel free to use this for learning and teaching.

---

**Happy Learning! 🚀**

