#!/bin/bash

# Health check script for the mining setup

set -e

echo "🔍 Checking Litecoin-Meowcoin AuxPoW Proxy Health..."
echo "================================================="

# Function to check service status
check_service() {
    local service=$1
    local status=$(docker-compose ps -q $service 2>/dev/null)
    
    if [ -z "$status" ]; then
        echo "❌ $service: Not running"
        return 1
    else
        local health=$(docker inspect --format='{{.State.Health.Status}}' $(docker-compose ps -q $service) 2>/dev/null || echo "no-health-check")
        if [ "$health" = "healthy" ]; then
            echo "✅ $service: Running and healthy"
        elif [ "$health" = "unhealthy" ]; then
            echo "⚠️  $service: Running but unhealthy"
        else
            echo "🟡 $service: Running (no health check)"
        fi
    fi
}

# Check Docker Compose services
echo "📋 Service Status:"
check_service "litecoin"
check_service "meowcoin" 
check_service "stratum-proxy"

echo ""
echo "🔗 Network Connectivity:"

# Check if services can communicate
if docker-compose exec -T stratum-proxy python -c "import socket; s=socket.socket(); s.settimeout(5); s.connect(('litecoin', 9332)); s.close(); print('✅ Proxy -> Litecoin RPC: OK')" 2>/dev/null; then
    :
else
    echo "❌ Proxy -> Litecoin RPC: Failed"
fi

if docker-compose exec -T stratum-proxy python -c "import socket; s=socket.socket(); s.settimeout(5); s.connect(('meowcoin', 8766)); s.close(); print('✅ Proxy -> Meowcoin RPC: OK')" 2>/dev/null; then
    :
else
    echo "❌ Proxy -> Meowcoin RPC: Failed"
fi

echo ""
echo "⛓️  Blockchain Status:"

# Check Litecoin sync status
LTC_INFO=$(docker-compose exec -T litecoin litecoin-cli getblockchaininfo 2>/dev/null || echo "error")
if [ "$LTC_INFO" != "error" ]; then
    LTC_BLOCKS=$(echo "$LTC_INFO" | grep -o '"blocks":[0-9]*' | cut -d: -f2)
    LTC_HEADERS=$(echo "$LTC_INFO" | grep -o '"headers":[0-9]*' | cut -d: -f2)
    if [ "$LTC_BLOCKS" = "$LTC_HEADERS" ]; then
        echo "✅ Litecoin: Synced ($LTC_BLOCKS blocks)"
    else
        echo "🔄 Litecoin: Syncing ($LTC_BLOCKS/$LTC_HEADERS blocks)"
    fi
else
    echo "❌ Litecoin: RPC Error"
fi

# Check Meowcoin sync status  
MEWC_INFO=$(docker-compose exec -T meowcoin meowcoin-cli getblockchaininfo 2>/dev/null || echo "error")
if [ "$MEWC_INFO" != "error" ]; then
    MEWC_BLOCKS=$(echo "$MEWC_INFO" | grep -o '"blocks":[0-9]*' | cut -d: -f2)
    MEWC_HEADERS=$(echo "$MEWC_INFO" | grep -o '"headers":[0-9]*' | cut -d: -f2)
    if [ "$MEWC_BLOCKS" = "$MEWC_HEADERS" ]; then
        echo "✅ Meowcoin: Synced ($MEWC_BLOCKS blocks)"
    else
        echo "🔄 Meowcoin: Syncing ($MEWC_BLOCKS/$MEWC_HEADERS blocks)"
    fi
else
    echo "❌ Meowcoin: RPC Error"
fi

echo ""
echo "🎯 Stratum Proxy:"

# Check if stratum port is accessible
if nc -z localhost 54321 2>/dev/null; then
    echo "✅ Stratum port 54321: Accessible"
else
    echo "❌ Stratum port 54321: Not accessible"
fi

echo ""
echo "📊 Recent Activity:"
echo "Last 5 proxy log entries:"
docker-compose logs --tail=5 stratum-proxy 2>/dev/null || echo "No recent logs available"

echo ""
echo "💡 Troubleshooting:"
echo "  Full logs:        docker-compose logs -f"
echo "  Restart all:      docker-compose restart" 
echo "  Rebuild proxy:    docker-compose up -d --build stratum-proxy"
echo "  Check config:     cat .env"