# Quick Reference Guide

## Quick Start Commands

```bash
# Initial setup
./setup.sh

# Run all tests
./test-labs.sh

# View logs
docker-compose logs -f [service-name]

# Restart a service
docker-compose restart [service-name]

# Stop everything
docker-compose down

# Complete cleanup
docker-compose down -v --rmi all
```

## Common Testing Commands

### Forward Proxy
```bash
# Test via proxy
docker exec client curl -x http://squid-proxy:3128 http://web-server

# Test blocked domain
docker exec client curl -x http://squid-proxy:3128 http://www.facebook.com

# View cache stats
docker exec squid-proxy squidclient mgr:info
```

### Reverse Proxy
```bash
# Test HTTPS
curl -k https://localhost

# Test load balancing
for i in {1..10}; do curl -k -s https://localhost | grep "Backend Server"; done

# Test specific backend
curl -k https://localhost/backend1/

# Test sticky sessions
curl -k https://localhost/sticky/
```

### Authentication
```bash
# With basic auth
curl -k -u admin:admin123 https://localhost

# View security headers
curl -k -I https://localhost
```

### Monitoring
```bash
# Access Prometheus
open http://localhost:9090

# Access Grafana
open http://localhost:3000
# Login: admin/admin

# View nginx metrics
curl http://localhost:9113/metrics
```

### Logging
```bash
# Access Kibana
open http://localhost:5601

# Check Elasticsearch
curl http://localhost:9200/_cluster/health?pretty

# View nginx logs
docker exec reverse-proxy tail -f /var/log/nginx/access.log

# Count logs in Elasticsearch
curl "http://localhost:9200/logs-*/_count?pretty"
```

## Useful PromQL Queries

```promql
# Request rate
rate(nginx_http_requests_total[1m])

# Active connections
nginx_connections_active

# 95th percentile response time
histogram_quantile(0.95, rate(nginx_http_request_duration_seconds_bucket[5m]))

# Error rate
rate(nginx_http_requests_total{status=~"5.."}[5m])
```

## Useful Kibana Queries (KQL)

```kql
# All 200 responses
status: 200

# Errors only
status >= 400

# Specific path
request: "/backend1*"

# Slow requests (>1s)
request_time > 1

# Specific IP
remote_addr: "172.20.0.1"
```

## Service Endpoints

| Service | URL | Credentials |
|---------|-----|-------------|
| Reverse Proxy | https://localhost | - |
| Grafana | http://localhost:3000 | admin/admin |
| Prometheus | http://localhost:9090 | - |
| Kibana | http://localhost:5601 | - |
| Elasticsearch | http://localhost:9200 | - |
| Squid Proxy | http://localhost:3128 | - |

## Troubleshooting Quick Fixes

```bash
# Service won't start
docker-compose restart [service]

# Out of memory
docker-compose down
docker system prune -a
docker-compose up -d

# Port conflict
docker-compose down
# Edit docker-compose.yml to change port
docker-compose up -d

# Reset certificates
cd certs
rm *.crt *.key
./generate-certs.sh
cd ..
docker-compose restart reverse-proxy

# View service health
docker-compose ps

# Check container resource usage
docker stats

# View all container logs
docker-compose logs

# Follow specific service logs
docker-compose logs -f nginx

# Restart all services
docker-compose restart
```

## Load Balancing Algorithms

Edit `nginx/nginx.conf` upstream block:

```nginx
# Round Robin (default)
upstream backend_pool {
    server backend1:80;
    server backend2:80;
}

# Least Connections
upstream backend_pool {
    least_conn;
    server backend1:80;
    server backend2:80;
}

# IP Hash (sticky sessions)
upstream backend_pool {
    ip_hash;
    server backend1:80;
    server backend2:80;
}

# Weighted load balancing
upstream backend_pool {
    server backend1:80 weight=3;
    server backend2:80 weight=1;
}
```

## Health Check Configuration

```nginx
# In upstream block
server backend1:80 max_fails=3 fail_timeout=30s;
server backend2:80 max_fails=3 fail_timeout=30s backup;
```

## Enable/Disable Basic Auth

Edit `nginx/nginx.conf`:

```nginx
# Enable
auth_basic "Restricted Access";
auth_basic_user_file /etc/nginx/.htpasswd;

# Disable (comment out)
# auth_basic "Restricted Access";
# auth_basic_user_file /etc/nginx/.htpasswd;
```

Then restart:
```bash
docker-compose restart reverse-proxy
```

## Generate More Traffic

```bash
# Sustained traffic
while true; do curl -k -s https://localhost > /dev/null; sleep 0.5; done

# Burst traffic
for i in {1..100}; do curl -k -s https://localhost > /dev/null & done

# Test rate limiting
for i in {1..50}; do curl -k https://localhost -w "%{http_code}\n" -o /dev/null -s; done
```

## Docker Compose Scale (for testing)

Note: Current setup uses specific container names, so scaling requires config changes.

## Performance Testing with Apache Bench

```bash
# Install Apache Bench first
# macOS: already included
# Linux: apt-get install apache2-utils

# Run load test
ab -n 1000 -c 10 -k https://localhost/
```

## Backup and Restore

```bash
# Backup volumes
docker run --rm \
  -v docker-proxy-lab_grafana-data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/grafana-backup.tar.gz /data

# Restore volumes
docker run --rm \
  -v docker-proxy-lab_grafana-data:/data \
  -v $(pwd):/backup \
  alpine tar xzf /backup/grafana-backup.tar.gz -C /
```
