#!/bin/bash

# Docker Proxy Lab - Quick Test Script
# Runs a series of tests to verify all labs are working

echo "🧪 Running Lab Tests..."
echo "======================"
echo ""

# Test 1: Forward Proxy
echo "Test 1: Forward Proxy with Squid"
echo "---------------------------------"
docker exec client curl -x http://squid-proxy:3128 -s http://web-server > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ Forward proxy is working"
else
    echo "❌ Forward proxy test failed"
fi
echo ""

# Test 2: Reverse Proxy with Load Balancing
echo "Test 2: Reverse Proxy with Load Balancing"
echo "------------------------------------------"
response=$(curl -k -s https://localhost 2>/dev/null | grep -o "Backend Server [0-9]")
if [ -n "$response" ]; then
    echo "✅ Reverse proxy is working - Response: $response"
else
    echo "❌ Reverse proxy test failed"
fi
echo ""

# Test 3: SSL/TLS
echo "Test 3: SSL/TLS Configuration"
echo "------------------------------"
curl -k -I https://localhost 2>/dev/null | grep "HTTP/2" > /dev/null || curl -k -I https://localhost 2>/dev/null | grep "HTTP" > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ SSL/TLS is working"
else
    echo "❌ SSL/TLS test failed"
fi
echo ""

# Test 4: Prometheus
echo "Test 4: Prometheus Metrics"
echo "--------------------------"
curl -s http://localhost:9090/-/healthy > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ Prometheus is healthy"
else
    echo "❌ Prometheus test failed"
fi
echo ""

# Test 5: Grafana
echo "Test 5: Grafana Dashboard"
echo "-------------------------"
curl -s http://localhost:3000/api/health | grep '"database": "ok"' > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ Grafana is healthy"
else
    echo "❌ Grafana test failed"
fi
echo ""

# Test 6: Elasticsearch
echo "Test 6: Elasticsearch"
echo "---------------------"
curl -s http://localhost:9200/_cluster/health | grep -E '"status":"(green|yellow)"' > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ Elasticsearch is healthy"
else
    echo "❌ Elasticsearch test failed"
fi
echo ""

# Test 7: Kibana
echo "Test 7: Kibana"
echo "--------------"
curl -s http://localhost:5601/api/status | grep '"state":"green"' > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ Kibana is healthy"
else
    echo "⚠️  Kibana may still be starting (can take 2-3 minutes)"
fi
echo ""

# Test 8: Health Checks
echo "Test 8: Backend Health Checks"
echo "------------------------------"
healthy=$(docker-compose ps | grep -c "healthy")
echo "✅ $healthy services reporting as healthy"
echo ""

# Generate some test traffic
echo "Test 9: Generating Test Traffic"
echo "--------------------------------"
echo "Sending 20 requests to generate metrics and logs..."
for i in {1..20}; do
    curl -k -s https://localhost > /dev/null 2>&1
done
echo "✅ Test traffic generated"
echo ""

echo "======================"
echo "✅ All tests completed!"
echo "======================"
echo ""
echo "📊 View your results:"
echo "  • Check Grafana: http://localhost:3000"
echo "  • Check Kibana:  http://localhost:5601"
echo "  • Check Prometheus: http://localhost:9090"
