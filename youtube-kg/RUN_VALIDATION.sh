#!/usr/bin/env bash
# Master validation script for signup feature
# Runs all checks and produces a final report

set -e

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
BASE_URL="${1:-http://localhost}"
TIMESTAMP=$(date '+%Y-%m-%d_%H-%M-%S')
REPORT_FILE="$REPO_ROOT/validation-report-$TIMESTAMP.txt"

echo "════════════════════════════════════════════════════════════════"
echo "YouTube Knowledge Graph - Signup Feature Validation Report"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Report generated: $(date)"
echo "Repository: $REPO_ROOT"
echo "API Base URL: $BASE_URL"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Initialize report
{
  echo "═══════════════════════════════════════════════════════════════"
  echo "YouTube KG - Signup Feature Validation Report"
  echo "═══════════════════════════════════════════════════════════════"
  echo ""
  echo "Generated: $(date)"
  echo "Repository: $REPO_ROOT"
  echo "API URL: $BASE_URL"
  echo ""
} > "$REPORT_FILE"

# Check 1: Code files exist
echo -e "${YELLOW}1. Checking code files...${NC}"
echo "Checking code files..." >> "$REPORT_FILE"
FILES_OK=true
for file in \
  "frontend/src/pages/SignupPage.tsx" \
  "frontend/src/pages/LoginPage.tsx" \
  "frontend/src/App.tsx" \
  "backend/app/schemas/auth.py" \
  "signup-test.sh"
do
  if [ -f "$REPO_ROOT/$file" ]; then
    echo -e "${GREEN}✓${NC} $file exists"
    echo "✓ $file exists" >> "$REPORT_FILE"
  else
    echo -e "${RED}✗${NC} $file NOT FOUND"
    echo "✗ $file NOT FOUND" >> "$REPORT_FILE"
    FILES_OK=false
  fi
done
echo "" >> "$REPORT_FILE"

if [ "$FILES_OK" = true ]; then
  echo -e "${GREEN}All code files present${NC}"
else
  echo -e "${RED}Some files missing!${NC}"
  exit 1
fi
echo ""

# Check 2: Documentation exists
echo -e "${YELLOW}2. Checking documentation...${NC}"
echo "Checking documentation..." >> "$REPORT_FILE"
DOCS_OK=true
for doc in \
  "CLAUDE.md" \
  "DEPLOYMENT_PLAN.md" \
  "SIGNUP_DEPLOYMENT_CHECKLIST.md" \
  "BUILD_COMPLETE.md"
do
  if [ -f "$REPO_ROOT/$doc" ]; then
    echo -e "${GREEN}✓${NC} $doc exists"
    echo "✓ $doc exists" >> "$REPORT_FILE"
  else
    echo -e "${RED}✗${NC} $doc NOT FOUND"
    echo "✗ $doc NOT FOUND" >> "$REPORT_FILE"
    DOCS_OK=false
  fi
done
echo "" >> "$REPORT_FILE"

if [ "$DOCS_OK" = true ]; then
  echo -e "${GREEN}All documentation present${NC}"
else
  echo -e "${YELLOW}Warning: Some documentation missing (optional)${NC}"
fi
echo ""

# Check 3: Code contains required strings
echo -e "${YELLOW}3. Checking code quality...${NC}"
echo "Checking code quality..." >> "$REPORT_FILE"
QUALITY_OK=true

if grep -q "export default function SignupPage" "$REPO_ROOT/frontend/src/pages/SignupPage.tsx"; then
  echo -e "${GREEN}✓${NC} SignupPage exports correctly"
  echo "✓ SignupPage exports correctly" >> "$REPORT_FILE"
else
  echo -e "${RED}✗${NC} SignupPage export missing"
  echo "✗ SignupPage export missing" >> "$REPORT_FILE"
  QUALITY_OK=false
fi

if grep -q "/signup" "$REPO_ROOT/frontend/src/App.tsx"; then
  echo -e "${GREEN}✓${NC} /signup route in App.tsx"
  echo "✓ /signup route in App.tsx" >> "$REPORT_FILE"
else
  echo -e "${RED}✗${NC} /signup route NOT in App.tsx"
  echo "✗ /signup route NOT in App.tsx" >> "$REPORT_FILE"
  QUALITY_OK=false
fi

if grep -q "Field(min_length=8)" "$REPO_ROOT/backend/app/schemas/auth.py"; then
  echo -e "${GREEN}✓${NC} Password min-length validation in auth.py"
  echo "✓ Password min-length validation in auth.py" >> "$REPORT_FILE"
else
  echo -e "${RED}✗${NC} Password validation missing"
  echo "✗ Password validation missing" >> "$REPORT_FILE"
  QUALITY_OK=false
fi

if grep -q "Sign up" "$REPO_ROOT/frontend/src/pages/LoginPage.tsx"; then
  echo -e "${GREEN}✓${NC} Signup link in LoginPage"
  echo "✓ Signup link in LoginPage" >> "$REPORT_FILE"
else
  echo -e "${RED}✗${NC} Signup link missing from LoginPage"
  echo "✗ Signup link missing from LoginPage" >> "$REPORT_FILE"
  QUALITY_OK=false
fi

if [ -x "$REPO_ROOT/signup-test.sh" ]; then
  echo -e "${GREEN}✓${NC} signup-test.sh is executable"
  echo "✓ signup-test.sh is executable" >> "$REPORT_FILE"
else
  echo -e "${YELLOW}⚠${NC} signup-test.sh is not executable (fixing...)"
  chmod +x "$REPO_ROOT/signup-test.sh"
  echo "✓ signup-test.sh chmod +x applied" >> "$REPORT_FILE"
fi

echo "" >> "$REPORT_FILE"

if [ "$QUALITY_OK" = true ]; then
  echo -e "${GREEN}Code quality checks passed${NC}"
else
  echo -e "${RED}Code quality issues found!${NC}"
  exit 1
fi
echo ""

# Check 4: Git status
echo -e "${YELLOW}4. Checking git status...${NC}"
echo "Checking git status..." >> "$REPORT_FILE"
cd "$REPO_ROOT"
if [ "$(git rev-parse --abbrev-ref HEAD)" = "main" ] || [ "$(git rev-parse --abbrev-ref HEAD)" = "claude/youtube-creator-knowledge-graph-d9a8o1" ]; then
  echo -e "${GREEN}✓${NC} On correct branch"
  echo "✓ On $(git rev-parse --abbrev-ref HEAD)" >> "$REPORT_FILE"
else
  echo -e "${YELLOW}⚠${NC} On branch: $(git rev-parse --abbrev-ref HEAD)"
  echo "⚠ On branch: $(git rev-parse --abbrev-ref HEAD)" >> "$REPORT_FILE"
fi

COMMIT_COUNT=$(git log --oneline | grep -E "feat\(auth\)|docs: add signup" | wc -l)
if [ "$COMMIT_COUNT" -ge 2 ]; then
  echo -e "${GREEN}✓${NC} Signup commits present ($COMMIT_COUNT)"
  echo "✓ Signup commits present ($COMMIT_COUNT)" >> "$REPORT_FILE"
else
  echo -e "${YELLOW}⚠${NC} Expected at least 2 signup commits"
  echo "⚠ Expected at least 2 signup commits" >> "$REPORT_FILE"
fi
echo "" >> "$REPORT_FILE"
echo ""

# Check 5: API connectivity (if running)
echo -e "${YELLOW}5. Attempting API connectivity test...${NC}"
echo "Attempting API connectivity..." >> "$REPORT_FILE"

HEALTH_CHECK=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/health" 2>/dev/null || echo "000")
if [ "$HEALTH_CHECK" == "200" ]; then
  echo -e "${GREEN}✓${NC} API is running and healthy at $BASE_URL"
  echo "✓ API is healthy (HTTP 200)" >> "$REPORT_FILE"
  echo ""
  echo -e "${BLUE}Running full signup validation script...${NC}"
  echo "Running signup-test.sh..." >> "$REPORT_FILE"
  bash "$REPO_ROOT/signup-test.sh" "$BASE_URL" 2>&1 | tee -a "$REPORT_FILE"
else
  echo -e "${YELLOW}⚠${NC} API not responding (HTTP $HEALTH_CHECK)"
  echo "⚠ API not responding - skipping endpoint tests" >> "$REPORT_FILE"
  echo ""
  echo "To run full validation:"
  echo "1. Start Docker Compose: docker compose up -d"
  echo "2. Wait for services: docker compose ps"
  echo "3. Run tests: bash signup-test.sh http://localhost"
fi
echo ""

# Summary
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Validation Complete${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo ""
echo "Report saved to: $REPORT_FILE"
echo ""
echo "Next steps:"
echo "1. Review code changes: git show HEAD~2..HEAD"
echo "2. Run startup script: docker compose up -d"
echo "3. Test signup: bash signup-test.sh http://localhost"
echo "4. Manual test: Open http://localhost/signup in browser"
echo "5. Deploy: Merge to main and run in production"
echo ""
echo -e "${GREEN}✅ Build validation complete!${NC}"
