#!/bin/bash
# Wait for Docker services to become healthy

set -e

TIMEOUT=30
POSTGRES_CONTAINER="universalapi_postgres"
REDIS_CONTAINER="universalapi_redis"

echo "⏳ Waiting for Docker containers to become healthy..."

# Function to check container health
check_health() {
    local container=$1
    local status=$(docker inspect --format='{{.State.Health.Status}}' "$container" 2>/dev/null || echo "not_found")
    echo "$status"
}

# Wait for PostgreSQL
echo "   Checking PostgreSQL..."
ELAPSED=0
while [ $ELAPSED -lt $TIMEOUT ]; do
    STATUS=$(check_health "$POSTGRES_CONTAINER")
    if [ "$STATUS" = "healthy" ]; then
        echo "   ✓ PostgreSQL is healthy"
        break
    fi
    sleep 1
    ELAPSED=$((ELAPSED + 1))
done

if [ $ELAPSED -ge $TIMEOUT ]; then
    echo "   ✗ Timeout waiting for PostgreSQL"
    exit 1
fi

# Wait for Redis
echo "   Checking Redis..."
ELAPSED=0
while [ $ELAPSED -lt $TIMEOUT ]; do
    STATUS=$(check_health "$REDIS_CONTAINER")
    if [ "$STATUS" = "healthy" ]; then
        echo "   ✓ Redis is healthy"
        break
    fi
    sleep 1
    ELAPSED=$((ELAPSED + 1))
done

if [ $ELAPSED -ge $TIMEOUT ]; then
    echo "   ✗ Timeout waiting for Redis"
    exit 1
fi

echo "✅ All Docker services are healthy"
exit 0
