# Lab Exercises and Challenges

This document contains hands-on exercises to deepen your understanding of the Docker Proxy Lab.

---

## Beginner Exercises

### Exercise 1: Basic Proxy Understanding
**Objective:** Understand the difference between forward and reverse proxy.

**Tasks:**
1. Draw a diagram showing the flow of a request through a forward proxy
2. Draw a diagram showing the flow of a request through a reverse proxy
3. List 3 use cases for each proxy type

**Validation:**
- Explain your diagrams to a peer or write a brief explanation
- Compare with the README's architecture section

---

### Exercise 2: SSL Certificate Inspection
**Objective:** Understand SSL/TLS certificates.

**Tasks:**
1. View the generated certificate details:
   ```bash
   openssl x509 -in certs/nginx-selfsigned.crt -text -noout
   ```
2. Note the expiration date, issuer, and subject
3. Access https://localhost in a browser and inspect the certificate warning
4. Add the certificate to your browser's trusted certificates

**Questions:**
- Why does the browser show a warning?
- What's the difference between self-signed and CA-signed certificates?
- What is the CN (Common Name) in the certificate?

---

### Exercise 3: Access Control Lists
**Objective:** Configure Squid ACLs.

**Tasks:**
1. Add a new blocked domain to `squid/squid.conf`
2. Restart Squid: `docker-compose restart squid-proxy`
3. Test that the domain is blocked
4. Create a whitelist ACL for your favorite websites

**Validation:**
```bash
docker exec client curl -x http://squid-proxy:3128 -I http://your-blocked-domain.com
```

---

## Intermediate Exercises

### Exercise 4: Load Balancing Experiments
**Objective:** Compare different load balancing algorithms.

**Tasks:**
1. **Test Round Robin:**
   - Keep default config
   - Make 20 requests and count hits per backend
   
2. **Test Least Connections:**
   - Change to `least_conn`
   - Restart nginx
   - Simulate slow backend (stop one server briefly)
   - Observe traffic distribution

3. **Test IP Hash:**
   - Change to `ip_hash`
   - Restart nginx
   - Make multiple requests from same client
   - Observe sticky behavior

**Record Results:**
Create a table showing request distribution for each algorithm.

---

### Exercise 5: Rate Limiting Configuration
**Objective:** Implement and test rate limiting.

**Tasks:**
1. Identify the current rate limit in `nginx.conf` (currently 10 req/sec)
2. Change it to 5 req/sec
3. Test with burst traffic:
   ```bash
   for i in {1..20}; do curl -k https://localhost -w "%{http_code}\n" -o /dev/null -s; sleep 0.1; done
   ```
4. Count how many requests were rate-limited (503 responses)
5. Adjust the `burst` parameter and observe differences

**Questions:**
- What HTTP status code indicates rate limiting?
- What's the difference between `rate` and `burst`?
- How would you implement per-user rate limiting?

---

### Exercise 6: Monitoring Dashboard Creation
**Objective:** Create custom Grafana dashboards.

**Tasks:**
1. Create a new dashboard in Grafana
2. Add these panels:
   - Request rate (requests per second)
   - Response time (p50, p95, p99)
   - Error rate (4xx and 5xx)
   - Active connections
   - Top requested paths
3. Set the time range to "Last 15 minutes"
4. Enable auto-refresh (10s)

**Bonus:**
- Add threshold alerts (e.g., error rate > 5%)
- Create variables for filtering by backend

---

### Exercise 7: Log Analysis with Kibana
**Objective:** Analyze access patterns in logs.

**Tasks:**
1. Generate diverse traffic:
   ```bash
   curl -k https://localhost/
   curl -k https://localhost/backend1/
   curl -k https://localhost/backend2/
   curl -k https://localhost/nonexistent
   ```

2. In Kibana, answer these questions:
   - How many total requests were made?
   - What's the average response time?
   - How many 404 errors occurred?
   - Which backend received the most traffic?
   - What are the top 5 user agents?

3. Create visualizations:
   - Pie chart of status codes
   - Line graph of requests over time
   - Bar chart of requests per backend
   - Table of slowest requests

---

## Advanced Exercises

### Exercise 8: Health Check and Failover
**Objective:** Test automatic failover with health checks.

**Tasks:**
1. Monitor the load distribution:
   ```bash
   watch -n 1 'curl -k -s https://localhost | grep "Backend Server"'
   ```

2. In another terminal, stop a backend:
   ```bash
   docker stop backend2
   ```

3. Observe:
   - How long until traffic stops going to backend2?
   - Is there any downtime?
   - What happens in Prometheus metrics?

4. Restart backend2:
   ```bash
   docker start backend2
   ```

5. Observe:
   - How long until traffic resumes to backend2?
   - Check docker health status: `docker ps`

**Experiment:**
- Adjust health check intervals in docker-compose.yml
- Adjust `max_fails` and `fail_timeout` in nginx.conf

---

### Exercise 9: Security Hardening
**Objective:** Implement additional security measures.

**Tasks:**
1. **Enable Basic Authentication:**
   - Uncomment auth lines in nginx.conf
   - Test with correct and incorrect credentials

2. **Add Custom Security Headers:**
   ```nginx
   add_header X-Custom-Header "SecureLab" always;
   add_header Referrer-Policy "strict-origin-when-cross-origin" always;
   ```

3. **Implement Request Size Limits:**
   ```nginx
   client_max_body_size 10m;
   client_body_buffer_size 128k;
   ```

4. **Test Security:**
   - Use curl to verify all headers are present
   - Try uploading a large file
   - Test with different user agents

**Validation:**
```bash
curl -k -I https://localhost | grep -E "X-|Referrer"
```

---

### Exercise 10: Custom Metrics and Alerting
**Objective:** Create custom alerts in Prometheus.

**Tasks:**
1. Create alert rules in Prometheus
2. Define alerts for:
   - High error rate (>5% 5xx responses)
   - Slow response time (p95 > 1s)
   - Backend down (health check failures)
   - High memory usage

3. Create `prometheus/alerts.yml`:
   ```yaml
   groups:
     - name: nginx_alerts
       rules:
         - alert: HighErrorRate
           expr: rate(nginx_http_requests_total{status=~"5.."}[5m]) > 0.05
           for: 5m
           labels:
             severity: warning
           annotations:
             summary: "High error rate detected"
   ```

4. Update prometheus.yml to load alert rules
5. Test by simulating failures

---

### Exercise 11: Log Aggregation and Patterns
**Objective:** Implement structured logging.

**Tasks:**
1. Modify nginx log format to JSON:
   ```nginx
   log_format json_combined escape=json
     '{'
       '"time_local":"$time_local",'
       '"remote_addr":"$remote_addr",'
       '"request":"$request",'
       '"status": "$status",'
       '"body_bytes_sent":"$body_bytes_sent",'
       '"request_time":"$request_time",'
       '"upstream_response_time":"$upstream_response_time"'
     '}';
   ```

2. Update Logstash to parse JSON
3. Create Kibana visualization showing:
   - Average response time by endpoint
   - Request distribution by hour
   - Top 10 slowest requests
   - Geo-location of requests (if available)

---

### Exercise 12: Circuit Breaker Pattern
**Objective:** Implement circuit breaker for resilience.

**Tasks:**
1. Add circuit breaker config to nginx:
   ```nginx
   upstream backend_pool {
       server backend1:80 max_fails=3 fail_timeout=30s;
       server backend2:80 max_fails=3 fail_timeout=30s;
   }
   ```

2. Test the circuit breaker:
   - Stop all backends except one
   - Generate high traffic
   - Observe when circuit opens (stops sending traffic)
   - Start backends again
   - Observe recovery

3. Adjust parameters:
   - Reduce `max_fails` to 2
   - Increase `fail_timeout` to 60s
   - Test again and observe differences

---

### Exercise 13: Caching Strategy
**Objective:** Implement and optimize caching.

**Tasks:**
1. Configure Squid cache with specific settings:
   ```
   cache_mem 128 MB
   maximum_object_size 20 MB
   cache_dir ufs /var/spool/squid 200 16 256
   ```

2. Test caching:
   ```bash
   # First request (MISS)
   docker exec client curl -x http://squid-proxy:3128 -I http://web-server
   
   # Second request (HIT)
   docker exec client curl -x http://squid-proxy:3128 -I http://web-server
   ```

3. Check cache statistics:
   ```bash
   docker exec squid-proxy squidclient mgr:info
   docker exec squid-proxy squidclient mgr:mem
   ```

4. Measure performance:
   - Compare response times for cached vs non-cached
   - Calculate cache hit ratio
   - Analyze bandwidth savings

---

### Exercise 14: Multi-Environment Configuration
**Objective:** Create environment-specific configs.

**Tasks:**
1. Create separate configs for dev/staging/prod:
   ```
   nginx/
     nginx.conf.dev
     nginx.conf.staging  
     nginx.conf.prod
   ```

2. Key differences:
   - **Dev:** No auth, verbose logging, no rate limiting
   - **Staging:** Basic auth, standard logging, moderate rate limiting
   - **Prod:** Full security, optimized logging, strict rate limiting

3. Create docker-compose override files:
   ```yaml
   # docker-compose.dev.yml
   # docker-compose.staging.yml
   # docker-compose.prod.yml
   ```

4. Test each environment:
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
   ```

---

### Exercise 15: Performance Benchmarking
**Objective:** Benchmark and optimize performance.

**Tasks:**
1. Install Apache Bench or wrk
2. Baseline test:
   ```bash
   ab -n 10000 -c 100 -k https://localhost/
   ```

3. Record metrics:
   - Requests per second
   - Average response time
   - Failed requests
   - Memory usage

4. Optimization attempts:
   - Increase worker connections
   - Adjust keepalive timeout
   - Tune backend timeouts
   - Add caching

5. Re-test after each change
6. Document improvements

**Bonus:**
- Compare different load balancing algorithms
- Test with different numbers of backend servers
- Profile memory and CPU usage

---

## Challenge Projects

### Challenge 1: Blue-Green Deployment
Implement a blue-green deployment strategy:
- Create "blue" and "green" backend sets
- Route traffic to active set
- Deploy updates to inactive set
- Switch traffic with zero downtime
- Create automation script

### Challenge 2: Geo-Location Routing
Implement location-based routing:
- Use GeoIP database
- Route users to nearest backend
- Log location data
- Create Kibana geo-map visualization

### Challenge 3: API Gateway
Transform the reverse proxy into an API gateway:
- Add API key authentication
- Implement request/response transformation
- Add CORS handling
- Create API documentation
- Implement versioning

### Challenge 4: Service Mesh Lite
Build a basic service mesh:
- Add sidecar proxies for each backend
- Implement service discovery
- Add distributed tracing
- Create service dependency graph

### Challenge 5: Auto-Scaling Simulation
Implement auto-scaling logic:
- Monitor request rate and response times
- Scale backends up/down based on load
- Create scaling policies
- Test with load testing tools

---

## Learning Objectives Checklist

After completing these exercises, you should be able to:

- [ ] Explain forward vs reverse proxy concepts
- [ ] Configure SSL/TLS certificates
- [ ] Implement access control with ACLs
- [ ] Configure different load balancing algorithms
- [ ] Implement rate limiting and security measures
- [ ] Create custom monitoring dashboards
- [ ] Analyze logs with ELK stack
- [ ] Implement health checks and failover
- [ ] Configure caching strategies
- [ ] Benchmark and optimize performance
- [ ] Implement security best practices
- [ ] Create environment-specific configurations
- [ ] Set up alerting and monitoring
- [ ] Troubleshoot common proxy issues

---

## Additional Resources

- [Nginx Documentation](https://nginx.org/en/docs/)
- [Squid Configuration Guide](http://www.squid-cache.org/Doc/config/)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/)
- [ELK Stack Tutorial](https://www.elastic.co/guide/index.html)
- [Docker Networking](https://docs.docker.com/network/)

---

**Happy Learning! 🚀**
