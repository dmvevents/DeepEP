# Mortgage Calculator Application

A production-ready mortgage calculator with intelligent web scraping capabilities for all 50 US states and their counties. Captures regulation-grade mortgage data including property taxes, transfer taxes, recordation taxes, recording fees, and insurance estimates.

## Features

- **Intelligent Web Scraping**: LLM-powered agent that scrapes official government sources for accurate tax data
- **All 50 States Coverage**: Comprehensive data for all US counties
- **Mortgage Calculations**: CFPB Loan Estimate-compliant calculations
- **OCR Document Processing**: Extract data from pay stubs, W-2s, bank statements, and more
- **RESTful API**: Django REST Framework backend
- **Modern Frontend**: React-based responsive interface
- **Production Ready**: Docker containerization with PostgreSQL, Redis, and nginx

## Architecture

- **Backend**: Django 4.2+ with Django REST Framework
- **Frontend**: React 18+ with Material-UI
- **Scraper Agent**: FastAPI service with LLM integration (OpenAI/Claude)
- **Database**: PostgreSQL 15
- **Cache**: Redis 7
- **Task Queue**: Celery
- **Web Server**: nginx

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+
- Node.js 18+
- API Keys (OpenAI/Anthropic, SerpAPI)

### Environment Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd real_estate_app
```

2. Create environment files:
```bash
cp .env.example .env
cp .env.scraper.example .env.scraper
```

3. Edit `.env` and `.env.scraper` with your API keys and configuration

### Docker Deployment (Recommended)

```bash
# Build and start all services
docker-compose up --build

# Run migrations
docker-compose exec backend python manage.py migrate

# Create superuser
docker-compose exec backend python manage.py createsuperuser

# Load initial state/county data
docker-compose exec backend python manage.py load_jurisdictions
```

Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/api
- Scraper API: http://localhost:8001
- Admin Panel: http://localhost:8000/admin

### Local Development

#### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Load initial data
python manage.py load_jurisdictions

# Start development server
python manage.py runserver
```

#### Scraper Agent Setup

```bash
cd scraper
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start scraper service
uvicorn main:app --reload --port 8001
```

#### Frontend Setup

```bash
cd frontend
npm install
npm start
```

#### Celery Worker (for async tasks)

```bash
cd backend
celery -A config worker -l info
```

## API Documentation

### Core Endpoints

**Authentication:**
- `POST /api/auth/register/` - User registration
- `POST /api/auth/login/` - Login (returns JWT tokens)
- `POST /api/auth/token/refresh/` - Refresh access token

**Tax Data:**
- `GET /api/states/` - List all states
- `GET /api/states/{state_id}/counties/` - List counties for state
- `GET /api/tax-data/{state}/{county}/` - Get current tax data (triggers scraper if needed)
- `GET /api/tax-data/{state}/{county}/history/` - Get historical tax data versions

**Calculations:**
- `POST /api/calculate/` - Calculate loan estimate
- `GET /api/calculate/{id}/` - Retrieve saved calculation
- `GET /api/calculate/{id}/pdf/` - Export calculation as PDF

**Documents:**
- `POST /api/documents/upload/` - Upload document for OCR
- `GET /api/documents/{id}/` - Get document details
- `POST /api/documents/{id}/extract/` - Trigger extraction (if not auto-processed)

**Scraper:**
- `POST /scraper/fetch/{state}/{county}/` - Trigger manual scrape
- `GET /scraper/status/{task_id}/` - Check scraping task status
- `GET /scraper/stats/` - Get scraper performance statistics

## Testing

### Run Backend Tests

```bash
cd backend
python manage.py test
```

### Test Scraper on All Jurisdictions

```bash
cd scraper
python test_all_jurisdictions.py
```

This will generate a CSV report with success rates and data completeness scores.

### Frontend Tests

```bash
cd frontend
npm test
```

### Integration Tests

```bash
# With Docker running
docker-compose exec backend python manage.py test --tag=integration
```

## Data Model

### Key Models

- **User**: Authentication and user profiles
- **State**: US states (50 records)
- **County**: US counties (~3,143 records)
- **TaxData**: Versioned tax information with timestamps and sources
- **ScraperLog**: Audit trail for scraping operations
- **DocumentUpload**: User-submitted documents with OCR results
- **LoanEstimate**: Calculated mortgage estimates
- **CalculationHistory**: User's saved calculations

## Scraper Agent

The LLM-powered scraper agent uses a reasoning loop to:

1. Search for official government sources
2. Extract structured tax data
3. Validate across multiple sources
4. Self-correct if data seems inconsistent
5. Store with confidence scores and source URLs

Supports multiple LLM backends:
- OpenAI GPT-4
- Anthropic Claude 3.5
- Other providers via LiteLLM

## Calculation Engine

Implements CFPB Loan Estimate calculations:

- **Section A**: Loan terms and monthly payments
- **Section B**: Projected payments with escrow
- **Section C**: Closing costs
- **Section E**: Taxes and government fees (from scraped data)
- **Section G**: Initial escrow payments with proration
- **Section H**: Other costs including title and recording

### Key Features

- Property tax proration based on closing date
- Transfer tax split (buyer/seller)
- First-time homebuyer exemptions
- State-specific assessment ratios
- Tiered recordation tax structures

## OCR Pipeline

Processes financial documents with high accuracy:

1. Upload PDF/JPG/PNG
2. OCR with DeepSeek or Tesseract
3. LLM extraction of structured data
4. User review and correction
5. Integration into calculations

**Supported Documents:**
- Pay stubs
- W-2 forms
- Bank statements
- Tax returns
- Purchase agreements
- Insurance declarations

## Monitoring and Maintenance

### Data Freshness

Tax data is automatically flagged as stale after 30 days. The system can:
- Auto-rescrape stale data (configurable)
- Alert administrators to review
- Show "last verified" dates to users

### Scraper Health Dashboard

Access at `/admin/scraper/health/` to view:
- Success rates by state
- Average completeness scores
- Failed scrapes requiring review
- Data staleness alerts

### Logging

All services use structured JSON logging. View logs:

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f scraper
```

## Production Deployment

### Security Checklist

- [ ] Set `DEBUG=False` in production
- [ ] Use strong `SECRET_KEY`
- [ ] Configure HTTPS with SSL certificates
- [ ] Set up CORS properly
- [ ] Enable rate limiting
- [ ] Configure firewall rules
- [ ] Use environment variables for secrets
- [ ] Set up database backups
- [ ] Enable monitoring (Sentry, etc.)

### Scaling

- Horizontal scaling: Add more scraper agent containers
- Database: Use managed PostgreSQL (AWS RDS, etc.)
- Cache: Use managed Redis
- Static files: Serve via CDN
- Load balancing: nginx or cloud load balancer

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -am 'Add feature'`
4. Push to branch: `git push origin feature-name`
5. Submit pull request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
- GitHub Issues: [repository]/issues
- Documentation: [link to docs]
- Email: support@example.com
