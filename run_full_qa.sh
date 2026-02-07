#!/bin/bash
# FCRA Platform - Full QA Suite Runner
# Run this before deploying to production

set -e

echo "============================================"
echo "FCRA Platform - Full QA Suite"
echo "============================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track results
UNIT_PASSED=0
CYPRESS_PASSED=0
REGRESSION_PASSED=0

# Activate virtual environment
source venv/bin/activate

echo -e "${YELLOW}[1/4] Running Unit Tests...${NC}"
echo "----------------------------------------"
if python -m pytest tests/ -v --tb=short -q 2>&1 | tee /tmp/unit_tests.log | tail -5; then
    UNIT_PASSED=1
    echo -e "${GREEN}✓ Unit tests passed${NC}"
else
    echo -e "${RED}✗ Unit tests failed${NC}"
fi
echo ""

echo -e "${YELLOW}[2/4] Running Credit Import Regression Tests...${NC}"
echo "----------------------------------------"
if python -m pytest tests/test_credit_import_regression.py tests/test_credit_extraction_regression.py -v --tb=short 2>&1 | tee /tmp/regression_tests.log | tail -10; then
    REGRESSION_PASSED=1
    echo -e "${GREEN}✓ Regression tests passed${NC}"
else
    echo -e "${RED}✗ Regression tests failed${NC}"
fi
echo ""

echo -e "${YELLOW}[3/4] Starting Flask Server for E2E Tests...${NC}"
echo "----------------------------------------"
# Kill any existing server
lsof -ti:5001 | xargs kill -9 2>/dev/null || true
sleep 1

# Start server in background
export DATABASE_URL="postgresql://localhost/fcra?sslmode=disable"
export FCRA_ENCRYPTION_KEY="KML5PemZHFpNI_klNCZ4sliZPqJH5iLW4ynQSwHs-xg="
export PORT=5001
export CI=true
nohup python app.py > /tmp/flask_qa.log 2>&1 &
SERVER_PID=$!
echo "Server started (PID: $SERVER_PID)"

# Wait for server to be ready
echo "Waiting for server..."
for i in {1..30}; do
    if curl -s http://localhost:5001/health > /dev/null 2>&1; then
        echo "Server ready!"
        break
    fi
    sleep 1
done
echo ""

echo -e "${YELLOW}[4/4] Running Cypress E2E Tests...${NC}"
echo "----------------------------------------"
if CI=true npx cypress run --spec "cypress/e2e/login.cy.js,cypress/e2e/clients.cy.js,cypress/e2e/dashboard.cy.js" 2>&1 | tee /tmp/cypress_tests.log | tail -20; then
    CYPRESS_PASSED=1
    echo -e "${GREEN}✓ Cypress tests passed${NC}"
else
    echo -e "${RED}✗ Cypress tests failed${NC}"
fi

# Cleanup
echo ""
echo "Stopping server..."
kill $SERVER_PID 2>/dev/null || true

# Summary
echo ""
echo "============================================"
echo "QA SUMMARY"
echo "============================================"

if [ $UNIT_PASSED -eq 1 ]; then
    echo -e "${GREEN}✓ Unit Tests: PASSED${NC}"
else
    echo -e "${RED}✗ Unit Tests: FAILED${NC}"
fi

if [ $REGRESSION_PASSED -eq 1 ]; then
    echo -e "${GREEN}✓ Regression Tests: PASSED${NC}"
else
    echo -e "${RED}✗ Regression Tests: FAILED${NC}"
fi

if [ $CYPRESS_PASSED -eq 1 ]; then
    echo -e "${GREEN}✓ Cypress E2E: PASSED${NC}"
else
    echo -e "${RED}✗ Cypress E2E: FAILED${NC}"
fi

echo ""
if [ $UNIT_PASSED -eq 1 ] && [ $REGRESSION_PASSED -eq 1 ] && [ $CYPRESS_PASSED -eq 1 ]; then
    echo -e "${GREEN}============================================${NC}"
    echo -e "${GREEN}ALL TESTS PASSED - READY FOR DEPLOY${NC}"
    echo -e "${GREEN}============================================${NC}"
    exit 0
else
    echo -e "${RED}============================================${NC}"
    echo -e "${RED}SOME TESTS FAILED - DO NOT DEPLOY${NC}"
    echo -e "${RED}============================================${NC}"
    echo ""
    echo "Check logs:"
    echo "  - Unit tests: /tmp/unit_tests.log"
    echo "  - Regression: /tmp/regression_tests.log"
    echo "  - Cypress: /tmp/cypress_tests.log"
    echo "  - Flask: /tmp/flask_qa.log"
    exit 1
fi
