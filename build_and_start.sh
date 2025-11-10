#!/bin/bash

# Complete build and initialization script
# This script will build, start, and initialize the entire application

set -e

echo "========================================"
echo "Mortgage Calculator"
echo "Complete Build & Initialization"
echo "========================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Step 1: Check prerequisites
echo -e "${BLUE}Step 1: Checking Prerequisites${NC}"
echo "========================================"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker not found${NC}"
    echo "  Install Docker Desktop: https://www.docker.com/products/docker-desktop"
    exit 1
fi
echo -e "${GREEN}✓ Docker installed${NC}"

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}✗ Docker Compose not found${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker Compose installed${NC}"

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo -e "${RED}✗ Docker is not running${NC}"
    echo "  Start Docker Desktop and try again"
    exit 1
fi
echo -e "${GREEN}✓ Docker is running${NC}"
echo ""

# Step 2: Environment setup
echo -e "${BLUE}Step 2: Environment Configuration${NC}"
echo "========================================"

if [ ! -f .env ]; then
    echo -e "${YELLOW}! .env file not found${NC}"
    echo "  Running setup script..."
    ./setup.sh
else
    echo -e "${GREEN}✓ .env file exists${NC}"
fi

if [ ! -f .env.scraper ]; then
    echo -e "${YELLOW}! .env.scraper file not found${NC}"
    echo "  Please run: ./setup.sh"
    exit 1
else
    echo -e "${GREEN}✓ .env.scraper file exists${NC}"
fi
echo ""

# Step 3: Stop existing containers
echo -e "${BLUE}Step 3: Cleaning Up${NC}"
echo "========================================"
echo "Stopping any existing containers..."
docker-compose down 2>/dev/null || true
echo -e "${GREEN}✓ Cleaned up${NC}"
echo ""

# Step 4: Build containers
echo -e "${BLUE}Step 4: Building Docker Containers${NC}"
echo "========================================"
echo "This may take 5-10 minutes..."
echo ""

docker-compose build --progress=plain

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ All containers built successfully${NC}"
else
    echo -e "${RED}✗ Build failed${NC}"
    exit 1
fi
echo ""

# Step 5: Start services
echo -e "${BLUE}Step 5: Starting Services${NC}"
echo "========================================"
docker-compose up -d

echo "Waiting for services to be healthy..."
sleep 10

# Wait for database
echo "Waiting for PostgreSQL..."
for i in {1..30}; do
    if docker-compose exec -T postgres pg_isready -U admin &>/dev/null; then
        echo -e "${GREEN}✓ PostgreSQL ready${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}✗ PostgreSQL failed to start${NC}"
        exit 1
    fi
    sleep 2
done

# Wait for backend
echo "Waiting for backend..."
for i in {1..60}; do
    if curl -s http://localhost:8000/api/health/ &>/dev/null; then
        echo -e "${GREEN}✓ Backend ready${NC}"
        break
    fi
    if [ $i -eq 60 ]; then
        echo -e "${RED}✗ Backend failed to start${NC}"
        echo "  Check logs: docker-compose logs backend"
        exit 1
    fi
    sleep 2
done
echo ""

# Step 6: Initialize database
echo -e "${BLUE}Step 6: Initializing Database${NC}"
echo "========================================"

echo "Running migrations..."
docker-compose exec -T backend python manage.py migrate
echo -e "${GREEN}✓ Migrations complete${NC}"

echo "Loading jurisdictions..."
docker-compose exec -T backend python manage.py load_jurisdictions
echo -e "${GREEN}✓ Jurisdictions loaded${NC}"
echo ""

# Step 7: Create superuser
echo -e "${BLUE}Step 7: Create Admin User${NC}"
echo "========================================"

if [ -t 0 ]; then
    # Interactive mode
    echo "Create a superuser account:"
    docker-compose exec backend python manage.py createsuperuser
else
    # Non-interactive mode
    echo -e "${YELLOW}! Running in non-interactive mode${NC}"
    echo "  To create admin user later, run:"
    echo "  docker-compose exec backend python manage.py createsuperuser"
fi
echo ""

# Step 8: Health checks
echo -e "${BLUE}Step 8: Health Checks${NC}"
echo "========================================"

# Check all services
SERVICES=("backend:8000" "scraper-agent:8001" "vlm-service:8002")

for service in "${SERVICES[@]}"; do
    SERVICE_NAME=$(echo $service | cut -d: -f1)
    SERVICE_PORT=$(echo $service | cut -d: -f2)

    if curl -s http://localhost:$SERVICE_PORT/health &>/dev/null; then
        echo -e "${GREEN}✓ $SERVICE_NAME is healthy${NC}"
    else
        echo -e "${YELLOW}! $SERVICE_NAME may not be fully configured${NC}"
    fi
done
echo ""

# Step 9: Display information
echo -e "${BLUE}Step 9: Application Ready!${NC}"
echo "========================================"
echo ""
echo -e "${GREEN}✓ All services are running!${NC}"
echo ""
echo "Access the application:"
echo "  • Backend API:    http://localhost:8000/api"
echo "  • API Docs:       http://localhost:8000/api/docs"
echo "  • Admin Panel:    http://localhost:8000/admin"
echo "  • Scraper API:    http://localhost:8001"
echo "  • VLM OCR API:    http://localhost:8002"
echo ""
echo "View logs:"
echo "  docker-compose logs -f backend"
echo "  docker-compose logs -f scraper-agent"
echo "  docker-compose logs -f vlm-service"
echo ""
echo "Run tests:"
echo "  ./run_tests.sh"
echo ""
echo "Test scraping:"
echo "  python scripts/scrape_all_jurisdictions.py --test-mode"
echo ""
echo -e "${YELLOW}Note: Make sure your Claude API key is set in .env and .env.scraper${NC}"
echo ""

# Optional: Run basic tests
read -p "Run basic tests now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    ./run_tests.sh
fi

echo ""
echo "========================================"
echo -e "${GREEN}Setup Complete!${NC}"
echo "========================================"
