# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A production-ready mortgage calculator application with intelligent LLM-powered web scraping capabilities for all 50 US states and their counties. The system captures regulation-grade mortgage data including property taxes, transfer taxes, recordation taxes, recording fees, and insurance estimates.

**Quick Start:** Run `./setup.sh` then `./build_and_start.sh` to get everything running in Docker.

**Service Ports:**
- Backend API: http://localhost:8000
- Scraper Service: http://localhost:8001
- VLM OCR Service: http://localhost:8002
- Admin Panel: http://localhost:8000/admin
- PostgreSQL: localhost:5432
- Redis: localhost:6379

## Architecture

### Backend Stack
- **Django 4.2+** with Django REST Framework for API
- **PostgreSQL 15** for structured data storage
- **Redis 7** for caching and Celery message broker
- **Celery** for async task processing (scraping, OCR)
- **JWT** authentication with token refresh

### Scraper Service
- **FastAPI** standalone service at `scraper/`
- **LLM Integration**: OpenAI GPT-4 or Anthropic Claude 3.5 (configurable)
- **Web Search**: SerpAPI or Brave Search API
- **Agentic Reasoning**: Multi-loop extraction with self-correction

### VLM OCR Service
- **FastAPI** standalone service at `vlm-service/`
- **Claude Vision** integration for document OCR
- Extracts structured data from pay stubs, W-2s, bank statements

### Frontend (Future)
- React 18+ with Material-UI
- Currently using Django templates for quick development

## Project Structure

```
real_estate_app/
├── backend/              # Django application
│   ├── api/             # Core models (State, County, TaxData, LoanEstimate)
│   ├── calculator/      # Mortgage calculation engine
│   ├── documents/       # Document upload and OCR processing
│   ├── scraper_integration/  # Integration with scraper service
│   ├── config/          # Django settings
│   └── manage.py
├── scraper/             # FastAPI scraper service
│   ├── main.py          # FastAPI app
│   ├── scraper_agent.py # Main scraping logic
│   ├── llm_client.py    # LLM abstraction
│   ├── web_search.py    # Web search client
│   └── database.py      # Database operations
├── vlm-service/         # FastAPI OCR service
│   └── main.py          # Claude Vision OCR
├── scripts/             # Utility scripts
│   └── scrape_all_jurisdictions.py
├── docker-compose.yml   # All services configuration
├── .env                 # Backend environment variables
├── .env.scraper         # Scraper environment variables
├── setup.sh             # Initial setup script
├── build_and_start.sh   # Complete build & init script
└── run_tests.sh         # Test runner script
```

## Development Commands

### Quick Start (Recommended)

The project includes automated scripts for setup and development:

```bash
# Initial setup - creates .env files and configures API keys
./setup.sh

# Complete build and initialization (one command setup)
./build_and_start.sh

# Run all tests
./run_tests.sh
```

### Docker Development (Primary Method)

```bash
# Build and start all services
docker-compose up --build

# View logs (all services)
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f scraper-agent
docker-compose logs -f vlm-service

# After first startup, initialize database
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py load_jurisdictions
docker-compose exec backend python manage.py createsuperuser

# Restart a specific service
docker-compose restart backend

# Stop all services
docker-compose down

# Stop and remove volumes (CAUTION: deletes database)
docker-compose down -v

# Access Django shell
docker-compose exec backend python manage.py shell

# Access PostgreSQL
docker-compose exec postgres psql -U admin -d mortgage_calc
```

### Local Development (Without Docker)

```bash
# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py load_jurisdictions
python manage.py runserver

# Scraper service (separate terminal)
cd scraper
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8001

# VLM OCR service (separate terminal)
cd vlm-service
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8002

# Celery worker (separate terminal)
cd backend
celery -A config worker -l info

# Celery beat (separate terminal, for scheduled tasks)
celery -A config beat -l info
```

### Testing

```bash
# Run all tests (automated script)
./run_tests.sh

# Or manually with Docker
docker-compose exec backend python manage.py test

# Test specific app
docker-compose exec backend python manage.py test api
docker-compose exec backend python manage.py test calculator
docker-compose exec backend python manage.py test documents

# Run with verbose output
docker-compose exec backend python manage.py test --verbosity=2

# Test specific test case
docker-compose exec backend python manage.py test calculator.tests.MortgageCalculatorTests.test_monthly_payment_calculation
```

## Key Components

### 1. Django Backend (`backend/`)

**Main Apps:**
- `api/` - Core models (State, County, TaxData, LoanEstimate, UserProfile)
- `calculator/` - Mortgage calculation engine with CFPB Loan Estimate logic
- `documents/` - Document upload and OCR processing
- `scraper_integration/` - Integration with FastAPI scraper service

**Core Models:**
- `State` - 50 US states
- `County` - All US counties (~3,143 total, sample data included)
- `TaxData` - Versioned tax data with completeness/confidence scores
- `ScraperLog` - Audit trail for all scraping operations
- `LoanEstimate` - Saved mortgage calculations
- `DocumentUpload` - User-uploaded documents for OCR

**Key Files:**
- `calculator/engine.py` - Complete mortgage calculation logic
- `api/models.py` - All data models
- `api/serializers.py` - API serializers
- `api/views.py` - API viewsets

### 2. Scraper Service (`scraper/`)

**LLM-Powered Intelligent Scraper:**
- Uses web search to find official government sources
- LLM extracts structured tax data from search results
- Self-validates and re-scrapes if completeness < threshold
- Saves to shared PostgreSQL database

**Key Files:**
- `main.py` - FastAPI application
- `scraper_agent.py` - Main scraper orchestration logic
- `llm_client.py` - LLM provider abstraction (OpenAI/Claude)
- `web_search.py` - Web search client (SerpAPI/Brave)
- `database.py` - Database operations
- `config.py` - Settings with Pydantic
- `test_scraper.py` - Scraper unit tests

**Configuration:**
- `.env.scraper` - Environment variables (API keys, etc.)
- See `.env.scraper.example` for all available options

### 3. VLM OCR Service (`vlm-service/`)

**Claude Vision-Powered OCR:**
- Processes uploaded documents (PDF, JPG, PNG)
- Extracts structured data from financial documents
- Returns JSON with extracted fields

**Key Files:**
- `main.py` - FastAPI application with OCR endpoints

**Supported Document Types:**
- Pay stubs
- W-2 forms
- Bank statements
- Tax returns
- Purchase agreements

### 4. Calculation Engine (`backend/calculator/engine.py`)

Implements full CFPB Loan Estimate calculations:

**Section A: Loan Terms**
- Monthly P&I calculation using amortization formula
- Interest rate, loan term

**Section B: Projected Payments**
- PMI/MIP calculation based on LTV
- Escrow estimates (property tax + insurance)

**Section C: Costs at Closing**
- Total closing costs
- Cash to close calculation

**Section E: Taxes and Government Fees**
- Recording fees (deed, mortgage, surcharges)
- Transfer taxes with buyer/seller split
- Recordation taxes with tiered structure
- First-time homebuyer exemptions

**Section G: Initial Escrow Payment at Closing**
- Property tax proration based on closing date
- Homeowners insurance escrow
- Initial escrow deposit (2-3 months)

**Section H: Other Costs**
- Title services
- Title insurance (lender's and owner's)

**Key Methods:**
- `calculate()` - Main entry point
- `_calculate_monthly_payment()` - Amortization formula
- `_calculate_mortgage_insurance()` - PMI/MIP logic
- `_get_annual_property_tax()` - Uses scraped tax data
- `_calculate_property_tax_proration()` - Closing date proration
- `_calculate_transfer_taxes()` - With FTB exemptions
- `_calculate_recordation_taxes()` - Tiered rate structure

### 5. API Endpoints

**Core Backend API** (http://localhost:8000/api):
- Authentication: `/api/auth/register/`, `/api/auth/login/`, `/api/auth/token/refresh/`
- Tax Data: `/api/states/`, `/api/counties/`, `/api/tax-data/`
- Calculations: `/api/calculate/` (POST to create, GET to retrieve)
- Documents: `/api/documents/upload/`, `/api/documents/{id}/`
- Scraper Control: `/api/scraper/trigger/{state}/{county}/` (admin only)
- Health: `/api/health/`

**Scraper Service** (http://localhost:8001):
- `POST /scrape` - Trigger scrape with JSON: `{"state":"MD","county":"Montgomery"}`
- `GET /scrape/{state}/{county}` - Trigger scrape via URL params
- `GET /stats` - Scraper performance statistics
- `GET /health` - Health check

**VLM OCR Service** (http://localhost:8002):
- `POST /ocr` - Upload document for OCR extraction
- `GET /health` - Health check

## Database Schema

### Key Relationships
- `State` ← (1:M) → `County`
- `County` ← (1:M) → `TaxData` (versioned, one is_current=True)
- `County` ← (1:M) → `Municipality` (for overlay taxes)
- `User` ← (1:1) → `UserProfile`
- `User` ← (1:M) → `LoanEstimate`
- `LoanEstimate` → (M:1) → `TaxData` (FK to specific version used)
- `State`/`County` ← (1:M) → `ScraperLog` (audit trail)

### Important Fields
- `TaxData.is_current` - Only one current version per jurisdiction
- `TaxData.data` - JSONField with complete tax structure
- `TaxData.data_completeness` - 0-100 score
- `TaxData.scraper_confidence` - 0-100 score
- `TaxData.is_stale` - Property that checks last_verified vs expiry days
- `LoanEstimate.calculation_results` - JSONField with all calculated sections

## Environment Variables

The project uses two environment files:
- `.env` - Backend (Django) configuration
- `.env.scraper` - Scraper service configuration

Run `./setup.sh` to automatically create these files with defaults. See `.env.example` and `.env.scraper.example` for all available options.

**Key variables to configure:**
- `ANTHROPIC_API_KEY` - Required for Claude LLM (both files)
- `SERP_API_KEY` - Required for web search in scraper (optional for testing)
- `DATABASE_URL` - PostgreSQL connection (auto-configured in Docker)
- `SCRAPER_SERVICE_URL` - URL to scraper service (http://localhost:8001 or http://scraper-agent:8001 in Docker)
- `VLM_SERVICE_URL` - URL to VLM OCR service (http://vlm-service:8002 in Docker)

## Tax Data Structure

The `TaxData.data` JSONField contains:

```json
{
  "state": "MD",
  "county": "Montgomery",
  "effective_date": "2025-01-01",
  "data_completeness": 95,
  "scraper_confidence": 85,
  "property_tax": {
    "total_rate": 0.011234,
    "assessment_ratio": 100,
    "components": {
      "county": 0.007123,
      "state": 0.001120,
      "municipality": 0.000856,
      "school": 0.002135
    },
    "homestead_cap": "Annual increase limited to 10%",
    "reassessment_cycle": "3 years",
    "billing_schedule": {
      "first_half_due": "September 30",
      "second_half_due": "December 31"
    },
    "municipalities": [
      {
        "name": "Rockville",
        "zip_codes": ["20850", "20851"],
        "millage": 0.000856
      }
    ]
  },
  "transfer_tax": {
    "state_rate": 0.005,
    "county_rate": 0.01,
    "first_time_buyer_threshold": 500000,
    "first_time_buyer_exemption": "state portion waived",
    "buyer_seller_split": "typically seller pays, negotiable"
  },
  "recordation_tax": {
    "tiers": [
      {"max_value": 500000, "rate": 0.0035},
      {"min_value": 500000, "rate": 0.005}
    ],
    "school_tax_included": true
  },
  "recording_fees": {
    "deed": {"flat": 50, "per_page": 5},
    "mortgage": {"flat": 80, "per_page": 5},
    "surcharge": 20
  },
  "insurance_estimate": {
    "base_premium_per_100k": 650,
    "source": "NAIC state average 2024"
  },
  "sources": [
    "https://www.dat.state.md.us/",
    "https://www.montgomerycountymd.gov/finance/"
  ],
  "notes": "Based on 100% of fair market value assessment"
}
```

## Common Development Tasks

### Bulk Scraping Jurisdictions

```bash
# Test mode - scrape a few counties
python scripts/scrape_all_jurisdictions.py --states MD,VA,DC --test-mode

# Scrape specific states
python scripts/scrape_all_jurisdictions.py --states CA,TX,FL,NY

# Scrape all states (takes several hours)
python scripts/scrape_all_jurisdictions.py

# Results saved to scrape_results.csv
```

### Testing the Scraper

```bash
# Via curl
curl -X POST http://localhost:8001/scrape \
  -H "Content-Type: application/json" \
  -d '{"state":"MD","county":"Montgomery","force_refresh":true}'

# Check scraper stats
curl http://localhost:8001/stats
```

### Checking Data Coverage

```bash
# Via Django shell
docker-compose exec backend python manage.py shell

>>> from api.models import County, TaxData
>>> total = County.objects.filter(active=True).count()
>>> with_data = County.objects.filter(active=True, tax_data__is_current=True).distinct().count()
>>> print(f"Coverage: {with_data}/{total} ({with_data/total*100:.1f}%)")
```

### Testing Calculation Engine

```bash
# Via Django shell
docker-compose exec backend python manage.py shell

>>> from calculator.engine import MortgageCalculator
>>> from api.models import County
>>> from decimal import Decimal
>>> from datetime import datetime
>>>
>>> county = County.objects.get(state__code='MD', name='Montgomery')
>>> tax_data = county.tax_data.filter(is_current=True).first()
>>> calc = MortgageCalculator(tax_data.data)
>>> result = calc.calculate(
...     property_value=Decimal('500000'),
...     loan_amount=Decimal('400000'),
...     down_payment=Decimal('100000'),
...     interest_rate=Decimal('6.5'),
...     loan_term_years=30,
...     closing_date=datetime(2025, 6, 15),
...     loan_type='conventional',
...     first_time_homebuyer=False
... )
>>> print(result['summary'])
```

### Adding Counties to Database

```bash
# Via Django shell
docker-compose exec backend python manage.py shell

>>> from api.models import State, County
>>> state = State.objects.get(code='CA')
>>> County.objects.create(state=state, name='Los Angeles', active=True)
```

### Manual Management Commands

```bash
# Load jurisdictions (states and sample counties)
docker-compose exec backend python manage.py load_jurisdictions

# Create superuser
docker-compose exec backend python manage.py createsuperuser

# Run migrations
docker-compose exec backend python manage.py migrate

# Collect static files
docker-compose exec backend python manage.py collectstatic --noinput
```

## Important Implementation Notes

### Tax Data Freshness
- Tax data is considered stale after `SCRAPER_CACHE_EXPIRY_DAYS` (default: 30)
- Celery beat task runs daily to check and queue re-scraping of stale data
- API automatically triggers re-scraping when stale data is accessed (if `ENABLE_AUTO_RESCRAPE=True`)

### Versioning
- Each scrape creates a new version of `TaxData`
- Only one version per jurisdiction has `is_current=True`
- Historical versions are preserved for audit/comparison
- `LoanEstimate` stores FK to specific `TaxData` version used

### LLM Prompting
- Scraper uses structured JSON mode for reliable extraction
- Includes self-correction loop if completeness < threshold
- Validates against official source patterns (.gov, .us, etc.)
- Blacklists real estate listing sites

### Calculation Accuracy
- All monetary calculations use Python `Decimal` for precision
- Results rounded to 2 decimal places (cents)
- Property tax proration accounts for actual billing schedules
- Municipality overlays applied by ZIP code matching

### Error Handling
- All scraping failures logged to `ScraperLog`
- Celery tasks have retry logic with exponential backoff
- API returns specific error codes (404 for no data, 503 for scraper failures)
- LLM failures fall back to cached data when available

## Production Deployment Considerations

1. **Security**
   - Set `DEBUG=False`
   - Use strong `SECRET_KEY`
   - Configure HTTPS/SSL certificates in nginx
   - Restrict CORS origins
   - Use environment variables for all secrets

2. **Database**
   - Use managed PostgreSQL (AWS RDS, etc.)
   - Set up regular backups
   - Create indexes for performance (already defined in models)

3. **Caching**
   - Use managed Redis
   - Consider CDN for static files

4. **Scalability**
   - Horizontal scaling: Run multiple backend/scraper containers
   - Use load balancer (nginx or cloud LB)
   - Separate Celery workers by queue (scraping vs OCR)

5. **Monitoring**
   - Configure Sentry DSN for error tracking
   - Set up CloudWatch/Datadog for metrics
   - Monitor scraper success rates in admin dashboard

6. **Rate Limiting**
   - nginx already configured with rate limits
   - Adjust based on traffic patterns
   - Monitor LLM API usage and costs

## Troubleshooting

### Scraper Returns Empty Results
1. Check API keys in `.env.scraper`
2. Verify web search provider is working: `curl` test
3. Check `ScraperLog` for error messages
4. Test LLM directly with sample search results

### Calculations Seem Wrong
1. Verify tax data completeness score
2. Check `TaxData.sources` to validate official sources
3. Test with known values from official calculators
4. Review `calculation_results` JSON for intermediate values

### Database Connection Errors
1. Ensure PostgreSQL is running
2. Check `DATABASE_URL` in environment
3. Verify database user permissions
4. Check connection limits

### Celery Tasks Not Running
1. Ensure Redis is running
2. Check Celery worker is started
3. For scheduled tasks, ensure Celery beat is running
4. Check task status: `celery -A config inspect active`

## Code Style and Conventions

- Follow PEP 8 for Python code
- Use type hints where appropriate
- Document all public methods with docstrings
- Use descriptive variable names
- Keep functions focused and single-purpose
- Write tests for new functionality
- Use Django's ORM (avoid raw SQL)
- Prefer serializers for data validation over manual validation
