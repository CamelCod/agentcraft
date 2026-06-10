#!/usr/bin/env bash
# Comprehensive signup flow validation script
# Usage: bash signup-test.sh [BASE_URL]
# Example: bash signup-test.sh http://localhost

set -e

BASE_URL="${1:-http://localhost}"
PASS=0
FAIL=0
TEST_EMAIL="test-$(date +%s)@example.com"
TEST_PASSWORD="ValidPass123"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test helper function
check() {
  local test_name="$1"
  local response="$2"
  local expected_code="$3"
  local actual_code=$(echo "$response" | tail -1)

  if [ "$actual_code" == "$expected_code" ]; then
    echo -e "${GREEN}✓ PASS${NC}: $test_name"
    ((PASS++))
  else
    echo -e "${RED}✗ FAIL${NC}: $test_name (expected $expected_code, got $actual_code)"
    ((FAIL++))
  fi
}

check_field() {
  local test_name="$1"
  local json="$2"
  local field="$3"

  if echo "$json" | grep -q "\"$field\""; then
    echo -e "${GREEN}✓ PASS${NC}: $test_name"
    ((PASS++))
  else
    echo -e "${RED}✗ FAIL${NC}: $test_name (field $field not found)"
    ((FAIL++))
  fi
}

echo -e "${YELLOW}Starting signup flow validation...${NC}"
echo "Base URL: $BASE_URL"
echo "Test email: $TEST_EMAIL"
echo ""

# Test 1: Health check
echo -e "${YELLOW}1. Testing API health check${NC}"
RESPONSE=$(curl -s -w "\n%{http_code}" "$BASE_URL/health" 2>/dev/null | tail -1)
check "API is healthy" "$RESPONSE" "200"
echo ""

# Test 2: Register new user
echo -e "${YELLOW}2. Testing user registration${NC}"
REGISTER_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$TEST_EMAIL\",
    \"password\": \"$TEST_PASSWORD\",
    \"full_name\": \"Test User\"
  }")

REGISTER_CODE=$(echo "$REGISTER_RESPONSE" | tail -1)
REGISTER_BODY=$(echo "$REGISTER_RESPONSE" | head -n -1)

check "Registration returns 201" "$REGISTER_RESPONSE" "201"
check_field "Response has id field" "$REGISTER_BODY" "id"
check_field "Response has email field" "$REGISTER_BODY" "email"
check_field "Response has role field" "$REGISTER_BODY" "role"
check_field "Response has is_active field" "$REGISTER_BODY" "is_active"

if [ "$REGISTER_CODE" == "201" ]; then
  if echo "$REGISTER_BODY" | grep -q "\"role\":\"analyst\""; then
    echo -e "${GREEN}✓ PASS${NC}: New user assigned analyst role"
    ((PASS++))
  else
    echo -e "${RED}✗ FAIL${NC}: New user role is not analyst"
    ((FAIL++))
  fi
fi
echo ""

# Test 3: Attempt duplicate registration
echo -e "${YELLOW}3. Testing duplicate registration prevention${NC}"
DUPLICATE_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$TEST_EMAIL\",
    \"password\": \"$TEST_PASSWORD\",
    \"full_name\": \"Another User\"
  }")

DUPLICATE_CODE=$(echo "$DUPLICATE_RESPONSE" | tail -1)
check "Duplicate email returns 400" "$DUPLICATE_RESPONSE" "400"
echo ""

# Test 4: Test weak password validation
echo -e "${YELLOW}4. Testing password minimum length validation${NC}"
WEAK_PASS_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"weak-pass-$(date +%s)@example.com\",
    \"password\": \"weak\",
    \"full_name\": \"Test User\"
  }")

WEAK_PASS_CODE=$(echo "$WEAK_PASS_RESPONSE" | tail -1)
check "Weak password returns 422" "$WEAK_PASS_RESPONSE" "422"
echo ""

# Test 5: Login with new credentials
echo -e "${YELLOW}5. Testing login with new credentials${NC}"
LOGIN_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$TEST_EMAIL\",
    \"password\": \"$TEST_PASSWORD\"
  }")

LOGIN_CODE=$(echo "$LOGIN_RESPONSE" | tail -1)
LOGIN_BODY=$(echo "$LOGIN_RESPONSE" | head -n -1)

check "Login returns 200" "$LOGIN_RESPONSE" "200"
check_field "Response has access_token" "$LOGIN_BODY" "access_token"
check_field "Response has refresh_token" "$LOGIN_BODY" "refresh_token"

# Extract access token
ACCESS_TOKEN=$(echo "$LOGIN_BODY" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
echo "Token obtained: ${ACCESS_TOKEN:0:20}..."
echo ""

# Test 6: Get user info with token
echo -e "${YELLOW}6. Testing authenticated request (GET /me)${NC}"
if [ -n "$ACCESS_TOKEN" ]; then
  ME_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/api/v1/auth/me" \
    -H "Authorization: Bearer $ACCESS_TOKEN")

  ME_CODE=$(echo "$ME_RESPONSE" | tail -1)
  ME_BODY=$(echo "$ME_RESPONSE" | head -n -1)

  check "/auth/me returns 200" "$ME_RESPONSE" "200"
  check_field "User email matches registered email" "$ME_BODY" "$TEST_EMAIL"
else
  echo -e "${RED}✗ FAIL${NC}: No access token available for authenticated test"
  ((FAIL++))
fi
echo ""

# Test 7: Invalid credentials
echo -e "${YELLOW}7. Testing login with invalid credentials${NC}"
INVALID_LOGIN=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$TEST_EMAIL\",
    \"password\": \"WrongPassword123\"
  }")

check "Invalid password returns 401" "$INVALID_LOGIN" "401"
echo ""

# Summary
echo -e "${YELLOW}═══════════════════════════════════════${NC}"
echo -e "Test Results:"
echo -e "${GREEN}Passed: $PASS${NC}"
echo -e "${RED}Failed: $FAIL${NC}"
echo -e "${YELLOW}═══════════════════════════════════════${NC}"

if [ $FAIL -eq 0 ]; then
  echo -e "${GREEN}All tests passed!${NC}"
  exit 0
else
  echo -e "${RED}Some tests failed.${NC}"
  exit 1
fi
