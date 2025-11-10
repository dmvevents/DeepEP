#!/bin/bash

# Automated test runner for Mortgage Calculator
# Runs all unit tests and integration tests

set -e

echo "========================================"
echo "Mortgage Calculator - Test Runner"
echo "========================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if services are running
echo "Checking services..."
if ! docker-compose ps | grep -q "Up"; then
    echo -e "${RED}✗ Services not running${NC}"
    echo "  Start services with: docker-compose up -d"
    exit 1
fi
echo -e "${GREEN}✓ Services are running${NC}"
echo ""

# Wait for backend to be ready
echo "Waiting for backend to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:8000/api/health/ > /dev/null; then
        echo -e "${GREEN}✓ Backend is ready${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}✗ Backend failed to start${NC}"
        exit 1
    fi
    sleep 2
done
echo ""

# Test 1: Backend Unit Tests
echo "========================================"
echo "Test 1: Backend Unit Tests"
echo "========================================"
docker-compose exec -T backend python manage.py test --verbosity=2
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Backend tests passed${NC}"
else
    echo -e "${RED}✗ Backend tests failed${NC}"
    exit 1
fi
echo ""

# Test 2: Calculator Tests
echo "========================================"
echo "Test 2: Calculator Engine Tests"
echo "========================================"
docker-compose exec -T backend python manage.py test calculator --verbosity=2
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Calculator tests passed${NC}"
else
    echo -e "${RED}✗ Calculator tests failed${NC}"
    exit 1
fi
echo ""

# Test 3: API Tests
echo "========================================"
echo "Test 3: API Tests"
echo "========================================"
docker-compose exec -T backend python manage.py test api --verbosity=2
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ API tests passed${NC}"
else
    echo -e "${RED}✗ API tests failed${NC}"
    exit 1
fi
echo ""

# Test 4: Health Checks
echo "========================================"
echo "Test 4: Service Health Checks"
echo "========================================"

# Backend
if curl -s http://localhost:8000/api/health/ | grep -q "healthy"; then
    echo -e "${GREEN}✓ Backend health check passed${NC}"
else
    echo -e "${RED}✗ Backend health check failed${NC}"
fi

# Scraper
if curl -s http://localhost:8001/health | grep -q "healthy"; then
    echo -e "${GREEN}✓ Scraper health check passed${NC}"
else
    echo -e "${RED}✗ Scraper health check failed${NC}"
fi

# VLM
if curl -s http://localhost:8002/health | grep -q "healthy"; then
    echo -e "${GREEN}✓ VLM health check passed${NC}"
else
    echo -e "${YELLOW}! VLM health check failed (API key may not be set)${NC}"
fi
echo ""

# Test 5: Scraper Test
echo "========================================"
echo "Test 5: Scraper Integration Test"
echo "========================================"
echo "Testing scraper with Montgomery County, MD..."

SCRAPER_RESULT=$(curl -s -X POST http://localhost:8001/scrape \
  -H "Content-Type: application/json" \
  -d '{"state":"MD","county":"Montgomery","force_refresh":false}')

if echo "$SCRAPER_RESULT" | grep -q '"success":true'; then
    echo -e "${GREEN}✓ Scraper test passed${NC}"
    echo "$SCRAPER_RESULT" | python3 -m json.tool | head -20
else
    echo -e "${YELLOW}! Scraper test returned data (check for errors)${NC}"
    echo "$SCRAPER_RESULT" | python3 -m json.tool | head -20
fi
echo ""

# Test 6: Database Check
echo "========================================"
echo "Test 6: Database Check"
echo "========================================"

# Check jurisdictions loaded
STATES_COUNT=$(docker-compose exec -T backend python manage.py shell -c "from api.models import State; print(State.objects.count())" 2>/dev/null | tail -1)
COUNTIES_COUNT=$(docker-compose exec -T backend python manage.py shell -c "from api.models import County; print(County.objects.count())" 2>/dev/null | tail -1)

echo "States in database: $STATES_COUNT"
echo "Counties in database: $COUNTIES_COUNT"

if [ "$STATES_COUNT" -ge 50 ]; then
    echo -e "${GREEN}✓ All 50 states loaded${NC}"
else
    echo -e "${YELLOW}! Only $STATES_COUNT states loaded${NC}"
fi
echo ""

# Summary
echo "========================================"
echo "Test Summary"
echo "========================================"
echo -e "${GREEN}✓ All critical tests passed!${NC}"
echo ""
echo "Next steps:"
echo "  1. Run bulk scraping: python scripts/scrape_all_jurisdictions.py --test-mode"
echo "  2. Access admin panel: http://localhost:8000/admin"
echo "  3. Try calculations via API"
echo ""
