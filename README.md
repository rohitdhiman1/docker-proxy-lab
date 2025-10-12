# Docker Proxy Lab

This lab helps you understand the concepts of **forward proxy** and **reverse proxy** using Docker containers. It provides hands-on experience with both proxy types, their configurations, and how they route traffic.

---

## What is Squid?

**Squid** is a high-performance caching and forwarding HTTP proxy server. It is widely used as a forward proxy to route client requests to the internet, providing features like web content caching, access control, and traffic filtering. Squid helps improve web performance, reduce bandwidth usage, and enhance security by controlling and monitoring outbound web traffic.

---

## Lab Architecture

### 1. Forward Proxy Lab
- **Components:**
  - `squid-proxy`: Squid forward proxy server
  - `client`: Curl-based client container
  - `web-server`: Public web server (nginx)
- **Flow:**
  - The client sends HTTP requests to the web server via the Squid proxy.

### 2. Reverse Proxy Lab
- **Components:**
  - `reverse-proxy`: Nginx reverse proxy
  - `backend1`, `backend2`: Two backend web servers (nginx with custom HTML)
- **Flow:**
  - The reverse proxy receives requests and forwards them to the appropriate backend based on the URL path.

---

## Setup Instructions

1. **Clone the repository and navigate to the project directory:**
   ```sh
   git clone <repo-url>
   cd docker-proxy-lab
   ```

2. **Start all services:**
   ```sh
   docker-compose up --build
   ```

---

## Forward Proxy: How to Test

1. **Access the client container:**
   ```sh
   docker exec -it client sh
   ```
2. **Test HTTP request via proxy:**
   ```sh
   curl -x http://squid-proxy:3128 http://web-server
   ```
   - You should see the default nginx welcome page (from `web-server`).

**What you learn:**
- A forward proxy sits between the client and the internet, forwarding client requests to external servers.
- The client must be configured to use the proxy.

---

## Reverse Proxy: How to Test

1. **Open your browser or use curl:**
   - `http://localhost:8081/` → Should show **Backend 1** page
   - `http://localhost:8081/backend2/` → Should show **Backend 2** page

**What you learn:**
- A reverse proxy sits in front of backend servers, routing external requests to the appropriate internal service.
- The client does not need to know about the backend servers.

---

## File Structure

```
docker-compose.yml
squid/
  squid.conf
nginx/
  nginx.conf
backend1/
  index.html
backend2/
  index.html
```

---

## Key Learnings

- **Forward Proxy:**
  - Used for outbound traffic (e.g., client to internet)
  - Common for content filtering, anonymity, and access control
  - Clients must be configured to use the proxy

- **Reverse Proxy:**
  - Used for inbound traffic (e.g., internet to internal services)
  - Common for load balancing, SSL termination, and hiding internal structure
  - Clients interact only with the proxy, not the backend servers

---

## Caveats & Tips

- **Networking:** All containers are on the same Docker network, so you can use service names as hostnames.
- **Ports:**
  - Squid proxy: `3128`
  - Web server: `8080`
  - Reverse proxy: `8081`
  - Backend1: `8082`, Backend2: `8083`
- **Persistence:** This setup is for learning/demo only. For production, use persistent storage and secure configurations.
- **Proxy Configs:**
  - The Squid config is open (`http_access allow all`) for demo purposes. Do not use as-is in production.
  - The Nginx config routes `/` to backend1 and `/backend2/` to backend2. You can expand this for more complex routing.
- **Client Container:** The `client` container runs `tail -f /dev/null` to stay alive. Use `docker exec` to run commands inside it.

---

## Cleanup

To stop and remove all containers:
```sh
docker-compose down
```

---

## References
- [Squid Proxy Documentation](http://www.squid-cache.org/Doc/)
- [Nginx Reverse Proxy Guide](https://docs.nginx.com/nginx/admin-guide/web-server/reverse-proxy/)
- [Docker Compose Docs](https://docs.docker.com/compose/)

---
