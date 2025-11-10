# Quick Start Guide - Mortgage Calculator

This guide will help you build, test, and run the complete mortgage calculator application with Docker Compose.

## Prerequisites

- **Docker Desktop** installed and running
- **Mac M4** (Apple Silicon) - or any modern computer
- **Claude API Key** (you have: sk-ant-api03-...)
- **SerpAPI Key** (optional, for web search) - Get free at https://serpapi.com/

## Step 1: Initial Setup

Run the automated setup script:

```bash
cd /Users/antonalexander/Github/real_estate_app

# Make script executable
chmod +x setup.sh

# Run setup (will create .env files and configure API keys)
./setup.sh
```

When prompted:
- **Enter Claude API Key**: Paste your key (sk-ant-api03-...)
- **Enter SerpAPI Key**: Optional - press Enter to skip for now

The script will create `.env` and `.env.scraper` files with your keys.

## Step 2: Build All Docker Containers

Build all services (this may take 5-10 minutes):

```bash
docker-compose build
```

This builds:
- PostgreSQL database
- Redis cache
- Django backend API
- FastAPI scraper agent
- VLM OCR service (Claude Vision)
- Celery workers
- Nginx reverse proxy

## Step 3: Start All Services

Start all containers:

```bash
docker-compose up -d
```

Check that all services are running:

```bash
docker-compose ps
```

You should see all services as "Up" and healthy.

## Step 4: Initialize Database

Run database migrations and load initial data:

```bash
# Run migrations
docker-compose exec backend python manage.py migrate

# Load US states and sample counties
docker-compose exec backend python manage.py load_jurisdictions

# Create admin user
docker-compose exec backend python manage.py createsuperuser
```

Follow prompts to create your admin account.

## Step 5: Verify Services

Test that all services are working:

```bash
# Check backend API
curl http://localhost:8000/api/health/

# Check scraper service
curl http://localhost:8001/health

# Check VLM OCR service
curl http://localhost:8002/health
```

All should return `{"status": "healthy"}`.

## Step 6: Access the Application

Open in your browser:

- **API Docs**: http://localhost:8000/api/docs
- **Admin Panel**: http://localhost:8000/admin (login with superuser credentials)
- **Backend API**: http://localhost:8000/api
- **Scraper API**: http://localhost:8001
- **VLM OCR API**: http://localhost:8002

## Step 7: Run Unit Tests

Test all components:

```bash
# Backend tests
docker-compose exec backend python manage.py test

# Specifically test calculator
docker-compose exec backend python manage.py test calculator

# Specifically test API
docker-compose exec backend python manage.py test api
```

All tests should pass!

## Step 8: Test the Scraper

Test scraping a single jurisdiction:

```bash
# Test Montgomery County, Maryland
curl -X POST http://localhost:8001/scrape \
  -H "Content-Type: application/json" \
  -d '{"state":"MD","county":"Montgomery","force_refresh":true}'
```

This will:
1. Search for official tax data sources
2. Extract structured data using Claude
3. Save to PostgreSQL database
4. Return complete tax data with confidence scores

Expected response: JSON with property tax, transfer tax, recording fees, etc.

## Step 9: Test Calculation Engine

Create a test calculation via API:

```bash
# First, get a JWT token
TOKEN=$(curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"your_admin_username","password":"your_password"}' \
  | jq -r '.access')

# Calculate a loan estimate
curl -X POST http://localhost:8000/api/calculate/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "county_id": 1,
    "property_value": 500000,
    "loan_amount": 400000,
    "down_payment": 100000,
    "interest_rate": 6.5,
    "loan_term_years": 30,
    "loan_type": "conventional",
    "property_type": "single_family",
    "first_time_homebuyer": false,
    "closing_date": "2025-06-15"
  }'
```

Expected response: Complete CFPB Loan Estimate with all sections.

## Step 10: Bulk Scraping Test

Test scraping multiple jurisdictions:

```bash
# Install Python dependencies for test script
pip install pandas tqdm requests

# Test scrape 2-3 states (test mode)
python scripts/scrape_all_jurisdictions.py --states MD,VA,DC --test-mode

# View results
cat scrape_results.csv
```

## Step 11: Test OCR Service

Test document OCR with Claude Vision:

```bash
# Upload a document (replace with your test image)
curl -X POST http://localhost:8002/ocr \
  -F "file=@/path/to/test_paystub.jpg" \
  -F "document_type=pay_stub"
```

Expected response: Extracted structured data from the document.

## Step 12: Full Production Scraping (Optional)

To scrape ALL states and counties:

```bash
# This will take several hours!
python scripts/scrape_all_jurisdictions.py

# Or scrape specific states
python scripts/scrape_all_jurisdictions.py --states CA,TX,FL,NY
```

Results are saved to `scrape_results.csv` with:
- Success rate
- Average completeness
- Average confidence
- Processing time per jurisdiction

## Common Commands

```bash
# View logs
docker-compose logs -f backend
docker-compose logs -f scraper-agent
docker-compose logs -f vlm-service

# Restart a service
docker-compose restart backend

# Stop all services
docker-compose down

# Stop and remove volumes (CAUTION: deletes database!)
docker-compose down -v

# Access Django shell
docker-compose exec backend python manage.py shell

# Access PostgreSQL
docker-compose exec postgres psql -U admin -d mortgage_calc

# Run specific tests
docker-compose exec backend python manage.py test calculator.tests.MortgageCalculatorTests.test_monthly_payment_calculation
```

## Monitoring

### Database Coverage

Check how many counties have tax data:

```python
docker-compose exec backend python manage.py shell

from api.models import County, TaxData
total = County.objects.filter(active=True).count()
with_data = County.objects.filter(active=True, tax_data__is_current=True).distinct().count()
print(f"Coverage: {with_data}/{total} ({with_data/total*100:.1f}%)")
```

### Scraper Performance

View scraper statistics:

```bash
curl http://localhost:8001/stats
```

### Admin Dashboard

Login to http://localhost:8000/admin to:
- View all scraped tax data
- Check scraper logs
- Monitor data completeness scores
- View saved loan estimates

## Troubleshooting

### Services won't start
```bash
# Check logs
docker-compose logs

# Rebuild
docker-compose down
docker-compose build --no-cache
docker-compose up
```

### Database connection errors
```bash
# Ensure PostgreSQL is healthy
docker-compose ps postgres

# Restart PostgreSQL
docker-compose restart postgres
```

### Scraper returns errors
```bash
# Check API keys are set
docker-compose exec scraper-agent env | grep API_KEY

# Check scraper logs
docker-compose logs scraper-agent

# Test Claude API directly
curl http://localhost:8001/test \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"state":"MD","county":"Test"}'
```

### Tests fail
```bash
# Ensure migrations are run
docker-compose exec backend python manage.py migrate

# Load test data
docker-compose exec backend python manage.py load_jurisdictions

# Run tests with verbose output
docker-compose exec backend python manage.py test --verbosity=2
```

## Performance Optimization

For Mac M4:
- Docker Desktop should use at least 4 GB RAM
- Enable VirtioFS for better volume performance
- Use Docker Desktop's resource settings to allocate 4+ CPU cores

## Next Steps

1. **Add More Counties**: Edit `backend/api/management/commands/load_jurisdictions.py` to add more counties
2. **Build React Frontend**: The API is ready for a React app
3. **Deploy to Production**: Use AWS, Google Cloud, or similar with managed PostgreSQL
4. **Add Monitoring**: Set up Sentry, Datadog, or similar
5. **Scale Scraping**: Add more scraper containers in docker-compose

## Success Metrics

After running the scraper:
- ✓ Success rate > 90%
- ✓ Average completeness > 85%
- ✓ Average confidence > 80%
- ✓ All calculations produce valid CFPB-compliant results
- ✓ OCR extraction accuracy > 90% for typed documents

Congratulations! Your mortgage calculator is now fully operational!
