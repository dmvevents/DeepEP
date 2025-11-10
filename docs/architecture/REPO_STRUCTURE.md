# Repository Structure

This document describes the organization of the mortgage calculator repository.

## Directory Structure

```
real_estate_app/
├── backend/                    # Django REST API application
│   ├── api/                   # Core models and API endpoints
│   ├── calculator/            # Mortgage calculation engine
│   ├── documents/             # Document upload and OCR
│   ├── scraper_integration/   # Integration with scraper service
│   ├── config/                # Django settings
│   ├── manage.py
│   └── requirements.txt
│
├── scraper/                   # FastAPI scraper service
│   ├── main.py               # FastAPI application
│   ├── scraper_agent.py      # Scraper orchestration
│   ├── llm_client.py         # LLM provider abstraction
│   ├── web_search.py         # Web search client
│   ├── database.py           # Database operations
│   ├── config.py             # Configuration
│   └── requirements.txt
│
├── vlm-service/               # FastAPI OCR service
│   ├── main.py               # Claude Vision OCR
│   └── requirements.txt
│
├── frontend/                  # React frontend (future)
│
├── tests/                     # Test suite
│   ├── test_system.py        # Comprehensive system tests
│   ├── test_results.json     # Test execution logs
│   └── README.md             # Test documentation
│
├── logs/                      # Application logs
│   └── test_results_*.json   # Timestamped test results
│
├── scripts/                   # Utility scripts
│   ├── utilities/            # Helper scripts
│   └── scrape_all_jurisdictions.py
│
├── docs/                      # Documentation
│   ├── api/                  # API documentation
│   └── ...
│
├── nginx/                     # Nginx configuration
│
├── .env                       # Backend environment variables
├── .env.scraper               # Scraper environment variables
├── docker-compose.yml         # Docker services configuration
├── setup.sh                   # Initial setup script
├── build_and_start.sh         # Build and start script
├── run_tests.sh               # Test runner script
├── CLAUDE.md                  # Development guide for Claude Code
├── REPO_STRUCTURE.md          # This file
├── README.md                  # Project README
└── QUICKSTART.md              # Quick start guide
```

## Key Directories

### `/backend` - Django REST API
Main application backend with API endpoints, models, and business logic.

**Setup:**
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### `/scraper` - FastAPI Scraper Service
Autonomous scraper service using LLM for intelligent data extraction.

**Setup:**
```bash
cd scraper
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8001
```

### `/vlm-service` - VLM OCR Service
Claude Vision-powered document OCR service.

**Setup:**
```bash
cd vlm-service
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8002
```

### `/tests` - Test Suite
Comprehensive testing infrastructure with JSON logging.

**Run tests:**
```bash
python3 tests/test_system.py
```

### `/logs` - Logs Directory
Store test results, application logs, and debug information.

### `/scripts` - Utility Scripts
Helper scripts for development and maintenance tasks.

## Virtual Environments

Each service should use its own virtual environment:

```bash
# Backend
backend/venv/

# Scraper
scraper/venv/

# VLM Service
vlm-service/venv/
```

### Creating Virtual Environments

```bash
# For each service
cd <service_directory>
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Activating Virtual Environments

```bash
# Backend
cd backend && source venv/bin/activate

# Scraper
cd scraper && source venv/bin/activate

# VLM
cd vlm-service && source venv/bin/activate
```

## Configuration Files

### Environment Variables
- `.env` - Backend configuration (Django, PostgreSQL, Redis)
- `.env.scraper` - Scraper configuration (LLM, web search)
- `.env.example` - Backend template
- `.env.scraper.example` - Scraper template

### Docker
- `docker-compose.yml` - All services configuration
- `backend/Dockerfile` - Backend container
- `scraper/Dockerfile` - Scraper container
- `vlm-service/Dockerfile` - VLM container

## Git Ignore Patterns

Important files/directories that should be ignored:
```
venv/
__pycache__/
*.pyc
.env
.env.scraper
*.log
test_results*.json
scrape_results*.csv
media/
staticfiles/
.DS_Store
```

## Development Workflow

1. **Initial Setup**
   ```bash
   ./setup.sh
   ```

2. **Start Services**
   ```bash
   docker-compose up --build
   ```

3. **Run Migrations**
   ```bash
   docker-compose exec backend python manage.py migrate
   docker-compose exec backend python manage.py load_jurisdictions
   ```

4. **Run Tests**
   ```bash
   ./run_tests.sh
   # or
   python3 tests/test_system.py logs/test_results_$(date +%Y%m%d_%H%M%S).json
   ```

5. **Monitor Logs**
   ```bash
   docker-compose logs -f backend
   docker-compose logs -f scraper-agent
   ```

## Best Practices

1. **Always use virtual environments** for local development
2. **Log all operations** to JSON for debugging
3. **Use docker-compose** for consistent development environment
4. **Run tests** before committing changes
5. **Document** new endpoints and features
6. **Follow** PEP 8 style guidelines
7. **Keep** .env files secure and never commit them
8. **Update** requirements.txt when adding dependencies

## Maintenance

### Updating Dependencies
```bash
# For each service
cd <service>
source venv/bin/activate
pip install --upgrade -r requirements.txt
pip freeze > requirements.txt
```

### Database Migrations
```bash
docker-compose exec backend python manage.py makemigrations
docker-compose exec backend python manage.py migrate
```

### Cleaning Up
```bash
# Stop and remove containers
docker-compose down

# Remove volumes (CAUTION: deletes database)
docker-compose down -v

# Clean Python cache
find . -type d -name __pycache__ -exec rm -r {} +
find . -type f -name "*.pyc" -delete
```
