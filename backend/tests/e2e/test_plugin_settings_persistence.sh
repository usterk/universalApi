#!/bin/bash
# E2E Test: Plugin Settings Persistence Across Restart
#
# This script verifies that plugin settings persist in the database
# and are correctly loaded on application startup.
#
# Prerequisites:
# 1. PostgreSQL running on localhost:5432
# 2. Redis running on localhost:6379
# 3. Backend NOT running (script will start/stop it)
#
# Usage: ./test_plugin_settings_persistence.sh

set -e

BACKEND_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$BACKEND_DIR"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "=== E2E Test: Plugin Settings Persistence ==="
echo ""

# Function to start backend
start_backend() {
    echo "Starting backend..."
    poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/e2e_backend.log 2>&1 &
    BACKEND_PID=$!
    sleep 8

    # Check if started
    if ! curl -s http://localhost:8000/api/v1/auth/login -X POST \
         -H "Content-Type: application/json" \
         -d '{"email":"admin@example.com","password":"admin123"}' > /dev/null 2>&1; then
        echo -e "${RED}Failed to start backend${NC}"
        cat /tmp/e2e_backend.log
        exit 1
    fi
    echo "Backend started (PID: $BACKEND_PID)"
}

# Function to stop backend
stop_backend() {
    echo "Stopping backend..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
        wait $BACKEND_PID 2>/dev/null || true
    fi
    sleep 2
    echo "Backend stopped"
}

# Cleanup on exit
trap stop_backend EXIT

# Step 1: Start backend
start_backend

# Step 2: Login and get token
echo ""
echo "Step 1: Getting auth token..."
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"admin@example.com","password":"admin123"}' | \
    grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo -e "${RED}FAIL: Could not get auth token${NC}"
    exit 1
fi
echo -e "${GREEN}OK: Got auth token${NC}"

# Step 3: PUT settings
echo ""
echo "Step 2: Saving plugin settings..."
TEST_SETTINGS='{"settings": {"api_key": "e2e-test-'$(date +%s)'", "model": "whisper-large-v3", "language": "en"}}'
PUT_RESULT=$(curl -s -X PUT "http://localhost:8000/api/v1/plugins/audio_transcription/settings" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -d "$TEST_SETTINGS")

if echo "$PUT_RESULT" | grep -q '"status":"ok"'; then
    echo -e "${GREEN}OK: Settings saved${NC}"
    echo "  Response: $PUT_RESULT"
else
    echo -e "${RED}FAIL: Could not save settings${NC}"
    echo "  Response: $PUT_RESULT"
    exit 1
fi

# Step 4: GET settings to verify
echo ""
echo "Step 3: Verifying settings via GET..."
GET_RESULT=$(curl -s -X GET "http://localhost:8000/api/v1/plugins/audio_transcription/settings" \
    -H "Authorization: Bearer $TOKEN")

if echo "$GET_RESULT" | grep -q 'e2e-test-'; then
    echo -e "${GREEN}OK: Settings retrieved correctly${NC}"
    echo "  Response: $GET_RESULT"
else
    echo -e "${RED}FAIL: Settings not retrieved correctly${NC}"
    echo "  Response: $GET_RESULT"
    exit 1
fi

# Step 5: Restart backend
echo ""
echo "Step 4: Restarting backend..."
stop_backend
sleep 3
start_backend

# Step 6: Check startup logs for plugin_settings_loaded
echo ""
echo "Step 5: Checking startup logs..."
if grep -q "plugin_settings_loaded" /tmp/e2e_backend.log; then
    LOADED_COUNT=$(grep "plugin_settings_loaded" /tmp/e2e_backend.log | grep -o 'count=[0-9]*' | cut -d= -f2)
    if [ "$LOADED_COUNT" -ge 1 ]; then
        echo -e "${GREEN}OK: Settings loaded from database on startup (count=$LOADED_COUNT)${NC}"
    else
        echo -e "${RED}FAIL: No settings loaded on startup${NC}"
        exit 1
    fi
else
    echo -e "${RED}FAIL: No plugin_settings_loaded message in logs${NC}"
    exit 1
fi

# Step 7: Login again and GET settings after restart
echo ""
echo "Step 6: Getting new auth token..."
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"admin@example.com","password":"admin123"}' | \
    grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

echo ""
echo "Step 7: Verifying settings persisted after restart..."
GET_RESULT=$(curl -s -X GET "http://localhost:8000/api/v1/plugins/audio_transcription/settings" \
    -H "Authorization: Bearer $TOKEN")

if echo "$GET_RESULT" | grep -q 'e2e-test-'; then
    echo -e "${GREEN}OK: Settings persisted after restart!${NC}"
    echo "  Response: $GET_RESULT"
else
    echo -e "${RED}FAIL: Settings not persisted after restart${NC}"
    echo "  Response: $GET_RESULT"
    exit 1
fi

echo ""
echo "==================================="
echo -e "${GREEN}ALL TESTS PASSED${NC}"
echo "==================================="
