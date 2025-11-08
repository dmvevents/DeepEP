#!/bin/bash

# Setup script for Mortgage Calculator Application
# This script configures environment variables and sets up the project

set -e

echo "========================================"
echo "Mortgage Calculator Setup"
echo "========================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running on Mac M4
ARCH=$(uname -m)
if [[ "$ARCH" == "arm64" ]]; then
    echo -e "${GREEN}✓ Detected Apple Silicon (ARM64)${NC}"
    echo ""
fi

# Create .env file for backend
if [ ! -f .env ]; then
    echo "Creating .env file for backend..."
    cat > .env << 'EOF'
# Django Backend Configuration
DEBUG=True
SECRET_KEY=django-insecure-change-this-in-production-$(openssl rand -hex 32)

# Database Configuration
DB_NAME=mortgage_calc
DB_USER=admin
DB_PASSWORD=securemortgagepassword123
DB_HOST=postgres
DB_PORT=5432
DATABASE_URL=postgresql://admin:securemortgagepassword123@postgres:5432/mortgage_calc

# Redis Configuration
REDIS_URL=redis://redis:6379/0

# CORS Configuration
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:80

# LLM Configuration (for OCR extraction in backend)
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=YOUR_CLAUDE_API_KEY_HERE
OPENAI_API_KEY=

# OCR Configuration
OCR_PROVIDER=vlm
VLM_SERVICE_URL=http://vlm-service:8002

# Web Search Configuration (optional for backend)
WEB_SEARCH_PROVIDER=serpapi
SERP_API_KEY=

# Scraper Configuration
SCRAPER_SERVICE_URL=http://scraper-agent:8001
SCRAPER_CACHE_EXPIRY_DAYS=30
SCRAPER_MAX_RETRIES=3
SCRAPER_TIMEOUT=300

# JWT Configuration
JWT_ACCESS_TOKEN_LIFETIME=60
JWT_REFRESH_TOKEN_LIFETIME=1440

# File Upload
MAX_UPLOAD_SIZE=10485760

# Logging
LOG_LEVEL=INFO

# Feature Flags
ENABLE_AUTO_RESCRAPE=True
ENABLE_OCR_PROCESSING=True
ENABLE_DOCUMENT_UPLOAD=True

# Security
ALLOWED_HOSTS=localhost,127.0.0.1,backend
EOF
    echo -e "${GREEN}✓ Created .env file${NC}"
else
    echo -e "${YELLOW}! .env file already exists${NC}"
fi

# Create .env.scraper file for scraper service
if [ ! -f .env.scraper ]; then
    echo "Creating .env.scraper file..."
    cat > .env.scraper << 'EOF'
# Scraper Agent Configuration

# LLM Provider
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=YOUR_CLAUDE_API_KEY_HERE
OPENAI_API_KEY=
LLM_MODEL=claude-3-5-sonnet-20241022
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=4000

# Web Search Configuration
WEB_SEARCH_PROVIDER=serpapi
SERP_API_KEY=YOUR_SERPAPI_KEY_HERE
BRAVE_SEARCH_API_KEY=
MAX_SEARCH_RESULTS=10

# Database Configuration (shared with backend)
DATABASE_URL=postgresql://admin:securemortgagepassword123@postgres:5432/mortgage_calc

# Scraper Behavior
SCRAPER_TIMEOUT=300
MAX_RETRIES=3
RETRY_DELAY=5
MAX_REASONING_LOOPS=5
MIN_CONFIDENCE_SCORE=70
MIN_COMPLETENESS_SCORE=80

# Caching
CACHE_EXPIRY_DAYS=30
USE_CACHED_RESULTS=True

# Rate Limiting
MAX_REQUESTS_PER_MINUTE=20
MAX_CONCURRENT_SCRAPES=5

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Browser/HTTP Configuration
USER_AGENT=Mozilla/5.0 (Mortgage Calculator Scraper Bot)
REQUEST_TIMEOUT=30
FOLLOW_REDIRECTS=True
MAX_REDIRECTS=5

# Validation
REQUIRE_OFFICIAL_SOURCES=True

# Performance
ENABLE_ASYNC=True
WORKER_THREADS=4

# Testing
TEST_MODE=False
MOCK_LLM_RESPONSES=False
EOF
    echo -e "${GREEN}✓ Created .env.scraper file${NC}"
else
    echo -e "${YELLOW}! .env.scraper file already exists${NC}"
fi

echo ""
echo "========================================"
echo "Configure API Keys"
echo "========================================"
echo ""

# Prompt for Claude API key
read -p "Enter your Claude API key: " CLAUDE_KEY
if [ ! -z "$CLAUDE_KEY" ]; then
    # Update both .env files
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/ANTHROPIC_API_KEY=.*/ANTHROPIC_API_KEY=$CLAUDE_KEY/" .env
        sed -i '' "s/ANTHROPIC_API_KEY=.*/ANTHROPIC_API_KEY=$CLAUDE_KEY/" .env.scraper
    else
        # Linux
        sed -i "s/ANTHROPIC_API_KEY=.*/ANTHROPIC_API_KEY=$CLAUDE_KEY/" .env
        sed -i "s/ANTHROPIC_API_KEY=.*/ANTHROPIC_API_KEY=$CLAUDE_KEY/" .env.scraper
    fi
    echo -e "${GREEN}✓ Claude API key configured${NC}"
fi

# Prompt for SerpAPI key (optional)
echo ""
read -p "Enter your SerpAPI key (optional, press Enter to skip): " SERP_KEY
if [ ! -z "$SERP_KEY" ]; then
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s/SERP_API_KEY=.*/SERP_API_KEY=$SERP_KEY/" .env
        sed -i '' "s/SERP_API_KEY=.*/SERP_API_KEY=$SERP_KEY/" .env.scraper
    else
        sed -i "s/SERP_API_KEY=.*/SERP_API_KEY=$SERP_KEY/" .env
        sed -i "s/SERP_API_KEY=.*/SERP_API_KEY=$SERP_KEY/" .env.scraper
    fi
    echo -e "${GREEN}✓ SerpAPI key configured${NC}"
else
    echo -e "${YELLOW}! SerpAPI key skipped - scraper will use mock data${NC}"
fi

echo ""
echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "  1. Review and edit .env and .env.scraper if needed"
echo "  2. Run: docker-compose up --build"
echo "  3. In another terminal:"
echo "     docker-compose exec backend python manage.py migrate"
echo "     docker-compose exec backend python manage.py load_jurisdictions"
echo "     docker-compose exec backend python manage.py createsuperuser"
echo ""
echo "Then access:"
echo "  - API: http://localhost:8000/api"
echo "  - Admin: http://localhost:8000/admin"
echo "  - Scraper: http://localhost:8001"
echo ""
