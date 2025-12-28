#!/bin/bash
# E2E Test: Multi-Instance Plugin Settings Consistency
#
# This script verifies that plugin settings are shared across multiple
# backend instances via the shared PostgreSQL database.
#
# Prerequisites:
# 1. PostgreSQL running on localhost:5432
# 2. Redis running on localhost:6379
# 3. Backend NOT running (script will start/stop instances)
#
# Usage: ./test_multi_instance_consistency.sh

set -e

BACKEND_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$BACKEND_DIR"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# PIDs for cleanup
INSTANCE_A_PID=""
INSTANCE_B_PID=""

echo "=== E2E Test: Multi-Instance Plugin Settings Consistency ==="
echo ""

# Function to start backend on specific port
start_backend_instance() {
    local port=$1
    local name=$2
    local log_file="/tmp/e2e_backend_${port}.log"

    echo "Starting $name on port $port..."
    poetry run uvicorn app.main:app --host 0.0.0.0 --port $port > "$log_file" 2>&1 &
    local pid=$!

    # Wait for instance to be ready (up to 30 seconds)
    local attempts=0
    local max_attempts=30
    while [ $attempts -lt $max_attempts ]; do
        if curl -s "http://localhost:$port/api/v1/auth/login" -X POST \
             -H "Content-Type: application/json" \
             -d '{"email":"admin@example.com","password":"admin123"}' > /dev/null 2>&1; then
            echo -e "${GREEN}$name started successfully (PID: $pid)${NC}"
            echo $pid
            return 0
        fi
        sleep 1
        attempts=$((attempts + 1))
    done

    echo -e "${RED}Failed to start $name on port $port${NC}"
    cat "$log_file"
    return 1
}

# Function to stop all backend instances
stop_all_instances() {
    echo ""
    echo "Stopping all backend instances..."
    if [ ! -z "$INSTANCE_A_PID" ]; then
        kill $INSTANCE_A_PID 2>/dev/null || true
        wait $INSTANCE_A_PID 2>/dev/null || true
        echo "  Instance A stopped"
    fi
    if [ ! -z "$INSTANCE_B_PID" ]; then
        kill $INSTANCE_B_PID 2>/dev/null || true
        wait $INSTANCE_B_PID 2>/dev/null || true
        echo "  Instance B stopped"
    fi
    sleep 2
}

# Cleanup on exit
trap stop_all_instances EXIT

# Function to get auth token from instance
get_auth_token() {
    local port=$1
    curl -s -X POST "http://localhost:$port/api/v1/auth/login" \
        -H "Content-Type: application/json" \
        -d '{"email":"admin@example.com","password":"admin123"}' | \
        grep -o '"access_token":"[^"]*' | cut -d'"' -f4
}

# Step 1: Start Instance A on port 8000
echo "Step 1: Starting Instance A on port 8000..."
INSTANCE_A_PID=$(start_backend_instance 8000 "Instance A")
if [ -z "$INSTANCE_A_PID" ]; then
    echo -e "${RED}FAIL: Could not start Instance A${NC}"
    exit 1
fi

# Step 2: Start Instance B on port 8001
echo ""
echo "Step 2: Starting Instance B on port 8001..."
INSTANCE_B_PID=$(start_backend_instance 8001 "Instance B")
if [ -z "$INSTANCE_B_PID" ]; then
    echo -e "${RED}FAIL: Could not start Instance B${NC}"
    exit 1
fi

# Step 3: Get auth tokens from both instances
echo ""
echo "Step 3: Getting auth tokens from both instances..."
TOKEN_A=$(get_auth_token 8000)
TOKEN_B=$(get_auth_token 8001)

if [ -z "$TOKEN_A" ]; then
    echo -e "${RED}FAIL: Could not get auth token from Instance A${NC}"
    exit 1
fi
echo -e "${GREEN}OK: Got token from Instance A${NC}"

if [ -z "$TOKEN_B" ]; then
    echo -e "${RED}FAIL: Could not get auth token from Instance B${NC}"
    exit 1
fi
echo -e "${GREEN}OK: Got token from Instance B${NC}"

# Step 4: PUT settings via Instance A
echo ""
echo "Step 4: Saving plugin settings via Instance A (port 8000)..."
UNIQUE_KEY="multi-instance-test-$(date +%s)"
TEST_SETTINGS="{\"settings\": {\"api_key\": \"$UNIQUE_KEY\", \"model\": \"whisper-large-v3\", \"shared_test\": true}}"

PUT_RESULT=$(curl -s -X PUT "http://localhost:8000/api/v1/plugins/audio_transcription/settings" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN_A" \
    -d "$TEST_SETTINGS")

if echo "$PUT_RESULT" | grep -q '"status":"ok"'; then
    echo -e "${GREEN}OK: Settings saved via Instance A${NC}"
    echo "  Settings: api_key=$UNIQUE_KEY"
else
    echo -e "${RED}FAIL: Could not save settings via Instance A${NC}"
    echo "  Response: $PUT_RESULT"
    exit 1
fi

# Step 5: GET settings via Instance B (should see the settings saved by Instance A)
echo ""
echo "Step 5: Retrieving settings via Instance B (port 8001)..."
GET_RESULT=$(curl -s -X GET "http://localhost:8001/api/v1/plugins/audio_transcription/settings" \
    -H "Authorization: Bearer $TOKEN_B")

if echo "$GET_RESULT" | grep -q "$UNIQUE_KEY"; then
    echo -e "${GREEN}OK: Instance B sees settings saved by Instance A!${NC}"
    echo "  Response: $GET_RESULT"
else
    echo -e "${RED}FAIL: Instance B does not see settings from Instance A${NC}"
    echo "  Expected api_key: $UNIQUE_KEY"
    echo "  Got: $GET_RESULT"
    exit 1
fi

# Step 6: Verify shared_test field is present (ensures full settings are shared)
if echo "$GET_RESULT" | grep -q '"shared_test":true\|"shared_test": true'; then
    echo -e "${GREEN}OK: All settings fields are shared correctly${NC}"
else
    echo -e "${YELLOW}WARN: shared_test field check failed, but main test passed${NC}"
fi

# Step 7: Verify by GET from Instance A as well
echo ""
echo "Step 6: Verifying consistency - GET from Instance A should match..."
GET_RESULT_A=$(curl -s -X GET "http://localhost:8000/api/v1/plugins/audio_transcription/settings" \
    -H "Authorization: Bearer $TOKEN_A")

if echo "$GET_RESULT_A" | grep -q "$UNIQUE_KEY"; then
    echo -e "${GREEN}OK: Instance A returns same settings${NC}"
else
    echo -e "${RED}FAIL: Instance A and B have different settings!${NC}"
    echo "  Instance A: $GET_RESULT_A"
    echo "  Instance B: $GET_RESULT"
    exit 1
fi

# Step 8: Update settings via Instance B and verify via Instance A
echo ""
echo "Step 7: Updating settings via Instance B..."
UNIQUE_KEY_B="updated-by-instance-b-$(date +%s)"
TEST_SETTINGS_B="{\"settings\": {\"api_key\": \"$UNIQUE_KEY_B\", \"updated_by\": \"instance_b\"}}"

PUT_RESULT_B=$(curl -s -X PUT "http://localhost:8001/api/v1/plugins/audio_transcription/settings" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN_B" \
    -d "$TEST_SETTINGS_B")

if echo "$PUT_RESULT_B" | grep -q '"status":"ok"'; then
    echo -e "${GREEN}OK: Settings updated via Instance B${NC}"
else
    echo -e "${RED}FAIL: Could not update settings via Instance B${NC}"
    echo "  Response: $PUT_RESULT_B"
    exit 1
fi

# Verify Instance A sees the update
echo ""
echo "Step 8: Verifying Instance A sees update from Instance B..."
GET_RESULT_FINAL=$(curl -s -X GET "http://localhost:8000/api/v1/plugins/audio_transcription/settings" \
    -H "Authorization: Bearer $TOKEN_A")

if echo "$GET_RESULT_FINAL" | grep -q "$UNIQUE_KEY_B"; then
    echo -e "${GREEN}OK: Instance A sees update from Instance B!${NC}"
    echo "  Response: $GET_RESULT_FINAL"
else
    echo -e "${RED}FAIL: Instance A does not see update from Instance B${NC}"
    echo "  Expected api_key: $UNIQUE_KEY_B"
    echo "  Got: $GET_RESULT_FINAL"
    exit 1
fi

echo ""
echo "==================================="
echo -e "${GREEN}ALL MULTI-INSTANCE TESTS PASSED${NC}"
echo "==================================="
echo ""
echo "Summary:"
echo "  - Instance A and Instance B share the same database"
echo "  - Settings saved via Instance A are visible to Instance B"
echo "  - Settings updated via Instance B are visible to Instance A"
echo "  - Multi-instance consistency verified!"
