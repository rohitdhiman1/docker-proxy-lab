# Architecture Diagrams

## Complete System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              DOCKER PROXY LAB                                    │
│                            Advanced Edition v2.0                                 │
└─────────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────────┐
│                           FORWARD PROXY LAB                                      │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   ┌─────────┐     ┌──────────────┐     ┌─────────────┐                         │
│   │ Client  │────▶│ Squid Proxy  │────▶│ Web Server  │                         │
│   │ (curl)  │     │   :3128      │     │   :8080     │                         │
│   └─────────┘     │              │     └─────────────┘                         │
│                   │ • ACLs       │                                              │
│                   │ • Caching    │                                              │
│                   │ • Filtering  │                                              │
│                   └──────────────┘                                              │
│                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────────┐
│                          REVERSE PROXY LAB                                       │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│                        ┌───────────────────────┐                                │
│                        │   Reverse Proxy       │                                │
│                        │   (Nginx)             │                                │
│       Clients          │   :80 (HTTP)          │                                │
│    ──────────────▶     │   :443 (HTTPS)        │                                │
│   (Browser/curl)       │                       │                                │
│                        │ • SSL/TLS             │                                │
│                        │ • Basic Auth          │                                │
│                        │ • Rate Limiting       │                                │
│                        │ • Load Balancing      │                                │
│                        │ • Health Checks       │                                │
│                        └───────────┬───────────┘                                │
│                                    │                                            │
│              ┌─────────────────────┼─────────────────────┐                      │
│              │                     │                     │                      │
│              ▼                     ▼                     ▼                      │
│      ┌──────────────┐      ┌──────────────┐     ┌──────────────┐              │
│      │  Backend 1   │      │  Backend 2   │     │  Backend 3   │              │
│      │    :8082     │      │    :8083     │     │    :8084     │              │
│      │  (Nginx)     │      │  (Nginx)     │     │  (Nginx)     │              │
│      └──────────────┘      └──────────────┘     └──────────────┘              │
│                                                                                  │
│                                    ▼                                            │
│                            ┌──────────────┐                                     │
│                            │  Backend 4   │                                     │
│                            │    :8085     │                                     │
│                            │  (Nginx)     │                                     │
│                            └──────────────┘                                     │
│                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────────┐
│                        MONITORING STACK                                          │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   ┌──────────────┐     ┌──────────────┐     ┌──────────────┐                  │
│   │   Nginx      │────▶│  Prometheus  │────▶│   Grafana    │                  │
│   │  Exporter    │     │    :9090     │     │    :3000     │                  │
│   │   :9113      │     │              │     │              │                  │
│   └──────────────┘     │ • Scraping   │     │ • Dashboards │                  │
│                        │ • Storage    │     │ • Alerts     │                  │
│                        │ • Queries    │     │ • Graphs     │                  │
│                        └──────────────┘     └──────────────┘                  │
│                                                                                  │
│   Metrics Flow: Nginx → Exporter → Prometheus → Grafana → User                 │
│                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────────┐
│                          LOGGING STACK (ELK)                                     │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   ┌──────────────┐     ┌──────────────┐     ┌──────────────┐                  │
│   │    Nginx     │────▶│  Logstash    │────▶│Elasticsearch │                  │
│   │   Logs       │     │    :5000     │     │    :9200     │                  │
│   │              │     │    :5044     │     │              │                  │
│   └──────────────┘     │              │     │ • Indexing   │                  │
│                        │ • Parsing    │     │ • Storage    │                  │
│                        │ • Enrichment │     │ • Search     │                  │
│                        │ • Filtering  │     └──────┬───────┘                  │
│                        └──────────────┘            │                            │
│                                                     │                            │
│                                                     ▼                            │
│                                             ┌──────────────┐                    │
│                                             │   Kibana     │                    │
│                                             │    :5601     │                    │
│                                             │              │                    │
│                                             │ • Discover   │                    │
│                                             │ • Visualize  │                    │
│                                             │ • Dashboard  │                    │
│                                             └──────────────┘                    │
│                                                                                  │
│   Log Flow: Nginx → Logstash → Elasticsearch → Kibana → User                   │
│                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────────┐
│                           NETWORK TOPOLOGY                                       │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   ┌────────────────────────────────────────────────────────────────────────┐   │
│   │  proxy-network (172.20.0.0/16)                                         │   │
│   │                                                                         │   │
│   │  • squid-proxy       • reverse-proxy    • backend1                     │   │
│   │  • web-server        • backend2         • backend3                     │   │
│   │  • client            • backend4                                        │   │
│   └────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│   ┌────────────────────────────────────────────────────────────────────────┐   │
│   │  monitoring-network                                                     │   │
│   │                                                                         │   │
│   │  • reverse-proxy     • nginx-exporter                                  │   │
│   │  • prometheus        • grafana                                         │   │
│   └────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│   ┌────────────────────────────────────────────────────────────────────────┐   │
│   │  logging-network                                                        │   │
│   │                                                                         │   │
│   │  • elasticsearch     • logstash         • kibana                       │   │
│   └────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────────┐
│                          DATA FLOW DIAGRAM                                       │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   REQUEST FLOW (Reverse Proxy):                                                 │
│   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                                                │
│                                                                                  │
│   1. Client → HTTPS Request (Port 443)                                          │
│   2. Nginx → SSL Termination                                                    │
│   3. Nginx → Basic Auth Check (optional)                                        │
│   4. Nginx → Rate Limit Check                                                   │
│   5. Nginx → Load Balancer (least_conn algorithm)                               │
│   6. Nginx → Health Check                                                       │
│   7. Nginx → Select Healthy Backend                                             │
│   8. Backend → Process Request                                                  │
│   9. Backend → Return Response                                                  │
│   10. Nginx → Add Security Headers                                              │
│   11. Nginx → Return to Client                                                  │
│                                                                                  │
│   METRICS FLOW:                                                                  │
│   ━━━━━━━━━━━━━                                                                 │
│                                                                                  │
│   Nginx → Stub Status → Nginx Exporter → Prometheus → Grafana → Dashboard      │
│                                                                                  │
│   LOGS FLOW:                                                                     │
│   ━━━━━━━━━━━                                                                   │
│                                                                                  │
│   Nginx → Access Log → Logstash → Parse/Enrich → Elasticsearch → Kibana        │
│                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────────┐
│                        SECURITY LAYERS                                           │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   Layer 1: Network Security                                                     │
│   ┌────────────────────────────────────────────────────────────────┐           │
│   │ • Segmented Networks (proxy, monitoring, logging)              │           │
│   │ • Docker Network Isolation                                     │           │
│   └────────────────────────────────────────────────────────────────┘           │
│                                                                                  │
│   Layer 2: Transport Security                                                   │
│   ┌────────────────────────────────────────────────────────────────┐           │
│   │ • SSL/TLS Encryption (HTTPS)                                   │           │
│   │ • TLS 1.2 and 1.3 only                                         │           │
│   │ • Strong cipher suites                                         │           │
│   └────────────────────────────────────────────────────────────────┘           │
│                                                                                  │
│   Layer 3: Authentication & Authorization                                       │
│   ┌────────────────────────────────────────────────────────────────┐           │
│   │ • HTTP Basic Authentication (optional)                         │           │
│   │ • .htpasswd file with hashed passwords                         │           │
│   └────────────────────────────────────────────────────────────────┘           │
│                                                                                  │
│   Layer 4: Application Security                                                 │
│   ┌────────────────────────────────────────────────────────────────┐           │
│   │ • Rate Limiting (10 req/sec + burst)                           │           │
│   │ • Security Headers (HSTS, X-Frame-Options, etc.)               │           │
│   │ • Access Control Lists (ACLs)                                  │           │
│   └────────────────────────────────────────────────────────────────┘           │
│                                                                                  │
│   Layer 5: Monitoring & Logging                                                 │
│   ┌────────────────────────────────────────────────────────────────┐           │
│   │ • Access Logging                                               │           │
│   │ • Error Logging                                                │           │
│   │ • Metrics Collection                                           │           │
│   │ • Health Monitoring                                            │           │
│   └────────────────────────────────────────────────────────────────┘           │
│                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────────┐
│                        LOAD BALANCING FLOW                                       │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   Algorithm: least_conn (Least Connections)                                     │
│                                                                                  │
│                        ┌─────────────────┐                                      │
│                        │ Reverse Proxy   │                                      │
│                        │                 │                                      │
│                        │  Load Balancer  │                                      │
│                        └────────┬────────┘                                      │
│                                 │                                               │
│                   ┌─────────────┼─────────────┐                                │
│                   │             │             │                                 │
│                   ▼             ▼             ▼                                 │
│            ┌──────────┐  ┌──────────┐  ┌──────────┐                            │
│            │Backend 1 │  │Backend 2 │  │Backend 3 │                            │
│            │          │  │          │  │          │                            │
│            │ Active   │  │ Active   │  │ Active   │                            │
│            │Conns: 2  │  │Conns: 1  │  │Conns: 3  │  ← Chooses B2            │
│            └──────────┘  └──────────┘  └──────────┘     (least connections)    │
│                                                                                  │
│                        ┌──────────┐                                             │
│                        │Backend 4 │                                             │
│                        │          │                                             │
│                        │ Active   │                                             │
│                        │Conns: 1  │                                             │
│                        └──────────┘                                             │
│                                                                                  │
│   Health Check Process:                                                         │
│   ━━━━━━━━━━━━━━━━━━━                                                          │
│                                                                                  │
│   Every 10s: wget http://backend/                                               │
│   ├─ Success (200 OK) → Mark as Healthy                                         │
│   └─ Failure (timeout/5xx) → Increment fail count                               │
│       └─ If fails >= max_fails (3) → Mark as Down for 30s                       │
│                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────────┐
│                     PERSISTENT STORAGE (Volumes)                                 │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   squid-cache           → Squid proxy cache data                                │
│   squid-logs            → Squid access and cache logs                           │
│   nginx-logs            → Nginx access and error logs                           │
│   prometheus-data       → Prometheus time-series database                       │
│   grafana-data          → Grafana dashboards and configuration                  │
│   elasticsearch-data    → Elasticsearch indices and logs                        │
│                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────┘
```

## Port Mapping Overview

```
┌──────────────────────────────────────────────────────────────────┐
│  EXTERNAL PORT  │  INTERNAL PORT  │  SERVICE           │  TYPE  │
├──────────────────────────────────────────────────────────────────┤
│      80         │       80        │  reverse-proxy     │  HTTP  │
│     443         │      443        │  reverse-proxy     │ HTTPS  │
│    3000         │     3000        │  grafana           │  HTTP  │
│    3128         │     3128        │  squid-proxy       │  Proxy │
│    5000         │     5000        │  logstash          │  TCP   │
│    5044         │     5044        │  logstash          │  Beats │
│    5601         │     5601        │  kibana            │  HTTP  │
│    8080         │       80        │  web-server        │  HTTP  │
│    8081         │       80        │  reverse-proxy     │  HTTP  │
│    8082         │       80        │  backend1          │  HTTP  │
│    8083         │       80        │  backend2          │  HTTP  │
│    8084         │       80        │  backend3          │  HTTP  │
│    8085         │       80        │  backend4          │  HTTP  │
│    9090         │     9090        │  prometheus        │  HTTP  │
│    9113         │     9113        │  nginx-exporter    │  HTTP  │
│    9200         │     9200        │  elasticsearch     │  HTTP  │
└──────────────────────────────────────────────────────────────────┘
```

## Service Dependencies

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│   reverse-proxy                                         │
│        ├─► backend1                                     │
│        ├─► backend2                                     │
│        ├─► backend3                                     │
│        └─► backend4                                     │
│                                                         │
│   nginx-exporter                                        │
│        └─► reverse-proxy                                │
│                                                         │
│   grafana                                               │
│        └─► prometheus                                   │
│                                                         │
│   logstash                                              │
│        └─► elasticsearch                                │
│                                                         │
│   kibana                                                │
│        └─► elasticsearch                                │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

**Legend:**
- `→` : HTTP/HTTPS Request Flow
- `►` : Dependency Relationship
- `━` : Network Boundary
- `┌─┐` : Service Container
- `▼` : Data Flow Direction
