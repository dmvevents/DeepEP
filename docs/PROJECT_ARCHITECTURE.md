# Mortgage Lending Qualification System - Architecture

## Date: November 8, 2025

## System Overview

Complete mortgage lending qualification system that automates:
1. **Income Qualification** (guideline-dependent)
2. **Property Cost Calculations** (universal)
3. **Document Processing** (OCR/VLM)
4. **DTI Calculations** (debt-to-income ratios)
5. **Loan Estimate Generation** (comparable to title company outputs)

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      FRONTEND (React)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Property    │  │   Document   │  │  Guidelines  │      │
│  │    Input     │  │    Upload    │  │   Reference  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                 DJANGO BACKEND (Port 8000)                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              API Gateway & Orchestration              │   │
│  └──────────────────────────────────────────────────────┘   │
│                            │                                 │
│     ┌──────────────────────┼──────────────────────┐        │
│     ↓                      ↓                      ↓         │
│  ┌───────┐           ┌───────────┐         ┌────────┐     │
│  │Income │           │ Property  │         │  DTI   │     │
│  │Calc   │           │   Costs   │         │ Calc   │     │
│  │Engine │           │Calculator │         │ Engine │     │
│  └───────┘           └───────────┘         └────────┘     │
└─────────────────────────────────────────────────────────────┘
         │                     │                      │
         ↓                     ↓                      ↓
┌────────────────┐  ┌────────────────┐  ┌────────────────┐
│  OCR Service   │  │ Tax Scraper    │  │  PostgreSQL    │
│  (Port 8003)   │  │  (Port 8001)   │  │  (Port 5432)   │
│  MonkeyOCR     │  │  FastAPI       │  │  Database      │
└────────────────┘  └────────────────┘  └────────────────┘
         │                     │
         ↓                     ↓
┌────────────────┐  ┌────────────────┐
│   Guideline    │  │     Redis      │
│    Database    │  │  (Port 6379)   │
│  (Fannie/FHA)  │  │   Caching      │
└────────────────┘  └────────────────┘
```

---

## Component Details

### 1. Frontend Layer

#### Tax Data Viewer (`frontend/index.html`)
- **Status**: ✅ Complete
- **Features**:
  - State/County selector
  - Real-time tax data display
  - All scraped data fields visible
- **Integration**: Calls Backend API at `/api/tax-data/by-location/{state}/{county}/`

#### Mortgage Guidelines Reference (`frontend/mortgage_guidelines.html`)
- **Status**: ✅ Complete
- **Features**:
  - Comprehensive loan type comparison
  - Income calculation methodologies
  - DTI calculator
  - All 6 loan types documented
- **Purpose**: Knowledge base for system development

#### Mortgage Qualification App (TO BUILD)
- **Status**: 🔄 Pending
- **Features**:
  - Property address input
  - Sales price input
  - Document upload (pay stubs, W-2s, bank statements)
  - Loan type selection
  - Qualification results display
  - Comparison with title company estimates

---

### 2. Backend Layer (Django)

#### Current Structure
```
backend/
├── api/                    # Core models & endpoints
│   ├── models.py          # State, County, TaxData
│   ├── views.py           # API viewsets
│   ├── serializers.py     # Data serialization
│   └── urls/              # URL routing
├── calculator/            # Mortgage calculations
│   ├── engine.py          # CFPB Loan Estimate logic
│   └── urls.py
├── documents/             # Document upload & OCR
│   ├── models.py          # DocumentUpload
│   └── views.py
├── scraper_integration/   # Tax scraper integration
│   ├── tasks.py           # Celery tasks
│   └── urls.py
└── config/                # Django settings
    ├── settings.py
    └── urls.py
```

#### New Components Needed

##### Income Qualification Engine (`calculator/income_engine.py`)
```python
class IncomeQualificationEngine:
    """
    Routes income calculation based on loan type
    Applies appropriate guideline (Fannie Mae, FHA, etc.)
    """

    def __init__(self, loan_type: str):
        self.loan_type = loan_type
        self.guideline = self._load_guideline(loan_type)

    def calculate_qualifying_income(
        self,
        documents: List[DocumentUpload],
        income_data: Dict
    ) -> Dict:
        """
        Calculate qualifying income using guideline-specific rules

        Returns:
        {
            "base_income": float,
            "bonus_income": float,
            "overtime_income": float,
            "commission_income": float,
            "self_employment_income": float,
            "other_income": float,
            "total_qualifying_income": float,
            "calculation_method": str,
            "confidence_score": float
        }
        """
        pass
```

##### Guideline Manager (`calculator/guidelines/`)
```python
# Fannie Mae guideline
class FannieMaeGuideline:
    MAX_DTI_AUTO = 50
    MAX_DTI_MANUAL = 45
    BONUS_CALCULATION = "2_year_average"
    SELF_EMPLOYED_HISTORY = 24  # months

# FHA guideline
class FHAGuideline:
    MAX_DTI_STANDARD = 43
    MAX_DTI_MAXIMUM = 56.99
    MIN_CREDIT_SCORE_3_5_DOWN = 580
    MIN_CREDIT_SCORE_10_DOWN = 500
```

##### DTI Calculator (`calculator/dti_calculator.py`)
```python
class DTICalculator:
    """
    Calculate front-end and back-end DTI ratios
    """

    def calculate(
        self,
        monthly_income: float,
        housing_payment: float,
        monthly_debts: float
    ) -> Dict:
        """
        Returns:
        {
            "front_end_dti": float,  # Housing / Income
            "back_end_dti": float,   # Total Debts / Income
            "qualifies_fannie_mae": bool,
            "qualifies_fha": bool,
            "qualifies_usda": bool,
            "qualifies_va": bool
        }
        """
        pass
```

---

### 3. OCR Service (NEW - Port 8003)

#### Purpose
Extract financial data from uploaded documents using MonkeyOCR-Apple-Silicon

#### API Endpoints
```
POST /ocr/extract
- Input: Document file (PDF, PNG, JPG)
- Output: Structured JSON with extracted fields

POST /ocr/extract/paystub
- Specialized extraction for pay stubs
- Returns: gross_income, ytd, deductions, etc.

POST /ocr/extract/w2
- Specialized extraction for W-2 forms
- Returns: box_1_wages, federal_tax, etc.

POST /ocr/extract/bank_statement
- Specialized extraction for bank statements
- Returns: deposits, withdrawals, balances

POST /ocr/extract/tax_return
- Specialized extraction for tax returns
- Returns: AGI, taxable_income, schedules

GET /ocr/health
- Health check endpoint
```

#### Technology Stack
- **Framework**: FastAPI
- **OCR Model**: MonkeyOCR-Apple-Silicon (MLX optimized)
- **Fallback**: Granite3.2-vision via OLLAMA
- **Container**: Docker (similar to existing scraper/VLM services)

#### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install MonkeyOCR
RUN git clone https://huggingface.co/Jimmi42/MonkeyOCR-Apple-Silicon /app/monkeyocr

# Copy application
COPY . .

# Expose port
EXPOSE 8003

# Run service
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003"]
```

---

### 4. Tax Scraper Service (Port 8001)

#### Status
✅ **Complete and Operational**

#### Current Capabilities
- Scrapes property tax data by state/county
- Extracts transfer taxes, recording fees, recordation taxes
- Stores in PostgreSQL with versioning
- 98.5% success rate (65 jurisdictions tested)

#### Integration Points
- Called by backend via `/scrape` endpoint
- Results stored in `TaxData` model
- Used by property cost calculator

---

### 5. Database Schema

#### Existing Tables
- `api_state` - 51 states (50 + DC)
- `api_county` - 65 counties (MD, VA, DC, PA)
- `api_taxdata` - Tax data with versioning
- `api_scrapelog` - Scraping audit trail
- `api_loanestimate` - Saved calculations
- `api_documentupload` - Uploaded documents

#### New Tables Needed

##### `income_qualification`
```sql
CREATE TABLE income_qualification (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES auth_user(id),
    loan_type VARCHAR(50),  -- 'fannie_mae', 'fha', 'usda', 'va', 'freddie_mac'
    guideline_version VARCHAR(20),

    -- Income components
    base_income DECIMAL(12, 2),
    bonus_income DECIMAL(12, 2),
    overtime_income DECIMAL(12, 2),
    commission_income DECIMAL(12, 2),
    self_employment_income DECIMAL(12, 2),
    other_income DECIMAL(12, 2),
    total_qualifying_income DECIMAL(12, 2),

    -- Calculation metadata
    calculation_method TEXT,
    confidence_score INTEGER,
    calculation_date TIMESTAMP DEFAULT NOW(),

    -- Supporting documents
    documents JSONB,  -- List of document IDs
    extracted_data JSONB  -- Raw OCR output
);
```

##### `lending_guidelines`
```sql
CREATE TABLE lending_guidelines (
    id SERIAL PRIMARY KEY,
    loan_type VARCHAR(50),
    version VARCHAR(20),
    effective_date DATE,
    guidelines JSONB,  -- Complete guideline rules
    source_url TEXT,
    last_updated TIMESTAMP DEFAULT NOW()
);
```

##### `dti_calculations`
```sql
CREATE TABLE dti_calculations (
    id SERIAL PRIMARY KEY,
    income_qualification_id INTEGER REFERENCES income_qualification(id),
    loan_estimate_id INTEGER REFERENCES api_loanestimate(id),

    -- Income
    monthly_gross_income DECIMAL(12, 2),

    -- Housing costs
    principal_interest DECIMAL(10, 2),
    property_tax DECIMAL(10, 2),
    insurance DECIMAL(10, 2),
    hoa_fees DECIMAL(10, 2),
    total_housing_payment DECIMAL(10, 2),

    -- Other debts
    car_payments DECIMAL(10, 2),
    credit_card_payments DECIMAL(10, 2),
    student_loans DECIMAL(10, 2),
    other_debts DECIMAL(10, 2),
    total_monthly_debts DECIMAL(10, 2),

    -- Ratios
    front_end_dti DECIMAL(5, 2),
    back_end_dti DECIMAL(5, 2),

    -- Qualification results
    qualifies_fannie_mae BOOLEAN,
    qualifies_freddie_mac BOOLEAN,
    qualifies_fha BOOLEAN,
    qualifies_usda BOOLEAN,
    qualifies_va BOOLEAN,

    calculation_date TIMESTAMP DEFAULT NOW()
);
```

---

## Data Flow

### Complete Loan Application Flow

```
1. User Input
   ├── Property Address → Tax Scraper → Property Costs
   ├── Sales Price
   ├── Loan Type Selection
   └── Document Upload → OCR Service → Income Data

2. Data Processing
   ├── Income Extraction (OCR)
   │   ├── Pay Stubs → Gross Income, YTD
   │   ├── W-2s → Annual Wages
   │   ├── Bank Statements → Deposits/Assets
   │   └── Tax Returns → Self-Employment Income
   │
   ├── Income Qualification (By Guideline)
   │   ├── Load guideline rules for loan type
   │   ├── Calculate base income
   │   ├── Calculate variable income (2-year average)
   │   ├── Calculate self-employment income
   │   ├── Apply continuity tests
   │   └── Output: Total Qualifying Income
   │
   ├── Property Costs (From Scraped Data)
   │   ├── Property Tax (annual & monthly)
   │   ├── Transfer Tax (state + county)
   │   ├── Recordation Tax (tiered)
   │   ├── Recording Fees (deed + mortgage)
   │   ├── Insurance Estimate
   │   └── Output: Total Property Costs
   │
   └── DTI Calculation
       ├── Monthly Income (from qualification)
       ├── Housing Payment (PITI + HOA)
       ├── Other Monthly Debts
       ├── Calculate Front-End DTI
       ├── Calculate Back-End DTI
       └── Check against loan type limits

3. Qualification Decision
   ├── Compare DTI to guideline max
   ├── Check compensating factors
   ├── Generate qualification status
   └── Provide detailed breakdown

4. Loan Estimate Generation
   ├── Property Information
   ├── Loan Terms
   ├── Projected Payments
   ├── Costs at Closing
   ├── Taxes & Government Fees
   ├── Escrow
   ├── Cash to Close
   └── Comparison to Title Company Estimate
```

---

## Technology Stack Summary

| Component | Technology | Port | Status |
|-----------|-----------|------|--------|
| Frontend | HTML/JS + React (future) | 80/3000 | 🔄 Partial |
| Backend | Django 4.2 + DRF | 8000 | ✅ Running |
| OCR Service | FastAPI + MonkeyOCR | 8003 | 🔄 To Build |
| Tax Scraper | FastAPI + GPT-4 | 8001 | ✅ Running |
| VLM Service | FastAPI + Claude | 8002 | ✅ Running |
| Database | PostgreSQL 15 | 5432 | ✅ Running |
| Cache | Redis 7 | 6379 | ✅ Running |
| Task Queue | Celery | - | ✅ Running |

---

## Implementation Roadmap

### Phase 1: Foundation (Weeks 1-2) ✅ COMPLETE
- [x] Property tax scraping system
- [x] Tax data frontend viewer
- [x] Mortgage guidelines research
- [x] Guidelines reference page
- [x] OCR model research
- [x] Project architecture

### Phase 2: Income Engine (Weeks 3-4)
- [ ] Build income qualification engine
- [ ] Implement guideline routing
- [ ] Create income calculation methods (salary, bonus, self-employed)
- [ ] Build DTI calculator
- [ ] Unit tests for all income calculations

### Phase 3: OCR Integration (Weeks 5-6)
- [ ] Set up MonkeyOCR-Apple-Silicon
- [ ] Build OCR service (FastAPI)
- [ ] Create extraction endpoints (paystub, W-2, bank statement)
- [ ] Test with sample documents
- [ ] Implement fallback to Granite3.2-vision
- [ ] Build document upload UI

### Phase 4: Integration & Testing (Weeks 7-8)
- [ ] Connect income engine to OCR service
- [ ] Integrate property costs with tax scraper
- [ ] Build complete qualification workflow
- [ ] Create qualification results UI
- [ ] Test with 10 real loan scenarios
- [ ] Validate against title company estimates
- [ ] Measure variance (target: <5%)

### Phase 5: Production Readiness (Weeks 9-10)
- [ ] Error handling and edge cases
- [ ] Logging and monitoring
- [ ] Performance optimization
- [ ] Security hardening
- [ ] Documentation completion
- [ ] Deployment automation

---

## Key Metrics & Validation

### Success Criteria
1. **Accuracy**: 80%+ calculations within 5% of title company estimates
2. **Coverage**: 100% of calculations within 10% of title company estimates
3. **OCR Accuracy**: >95% field extraction accuracy
4. **Performance**: <30 seconds total processing time per application
5. **Reliability**: 99%+ uptime for all services

### Test Dataset Requirements
- 10 real property scenarios with title company loan estimates
- Mix of loan types (Fannie Mae, FHA, VA, etc.)
- Various income types (W-2, self-employed, variable)
- Different property locations (tax rate variations)
- Range of credit scores and DTI ratios

---

## Next Immediate Steps

1. **Create OCR Service Structure**
   ```bash
   mkdir -p ocr-service/{app,tests,models}
   touch ocr-service/{main.py,requirements.txt,Dockerfile}
   ```

2. **Build Income Qualification Engine**
   ```bash
   mkdir -p backend/calculator/guidelines
   touch backend/calculator/{income_engine.py,dti_calculator.py}
   touch backend/calculator/guidelines/{fannie_mae.py,fha.py,usda.py,va.py}
   ```

3. **Create Database Migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

4. **Set Up Test Framework**
   ```bash
   mkdir -p tests/{unit,integration,e2e}
   mkdir -p tests/sample_documents
   ```

---

**Last Updated:** November 8, 2025
**Status:** Architecture Complete - Ready for Phase 2 Implementation
