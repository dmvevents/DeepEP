# OCR Service - Mortgage Document Extraction

FastAPI service for extracting structured data from mortgage documents using OLLAMA vision models.

## Supported Documents

1. **Pay Stubs** - Extract gross income, YTD, deductions, net pay
2. **W-2 Forms** - Extract all box values (1-14)
3. **Bank Statements** - Extract balances, deposits, withdrawals
4. **Tax Returns (1040)** - Extract AGI, taxable income, etc.
5. **Schedule C** - Extract self-employment income and expenses

## Technology Stack

- **FastAPI** - Modern Python web framework
- **OLLAMA** - Local vision models
  - Primary: `granite3.2-vision` (specialized for tables/financial docs)
  - Fallback: `llama3.2-vision:11b` (general vision understanding)
- **PIL/Pillow** - Image processing
- **Pydantic** - Data validation

## Installation

### Prerequisites

1. **OLLAMA** must be installed and running locally
   ```bash
   # Install OLLAMA (macOS)
   brew install ollama

   # Pull required models
   ollama pull granite3.2-vision
   ollama pull llama3.2-vision:11b
   ```

2. **Python 3.11+**

### Setup

```bash
# Navigate to OCR service directory
cd ocr-service

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Edit .env with your configuration
nano .env
```

## Running the Service

### Standalone (Development)

```bash
# Activate virtual environment
source venv/bin/activate

# Run with uvicorn
uvicorn main:app --host 0.0.0.0 --port 8003 --reload
```

### Docker Compose (Production)

```bash
# From project root
docker-compose up -d ocr-service

# View logs
docker-compose logs -f ocr-service
```

## API Endpoints

### Health Check
```bash
GET /health

# Response
{
  "status": "healthy",
  "models_available": ["granite3.2-vision", "llama3.2-vision:11b"],
  "timestamp": "2025-11-08T12:00:00"
}
```

### Extract Pay Stub
```bash
POST /extract/paystub
Content-Type: multipart/form-data

file: [image/pdf file]

# Response
{
  "success": true,
  "document_type": "paystub",
  "extracted_data": {
    "employee_name": "John Doe",
    "gross_income_current": 5000.00,
    "gross_income_ytd": 60000.00,
    ...
  },
  "confidence_score": 95,
  "model_used": "granite3.2-vision",
  "processing_time_ms": 1500.5
}
```

### Extract W-2
```bash
POST /extract/w2
Content-Type: multipart/form-data

file: [image/pdf file]
```

### Extract Bank Statement
```bash
POST /extract/bank-statement
Content-Type: multipart/form-data

file: [image/pdf file]
```

### Extract Tax Return (1040)
```bash
POST /extract/tax-return
Content-Type: multipart/form-data

file: [image/pdf file]
```

### Extract Schedule C
```bash
POST /extract/schedule-c
Content-Type: multipart/form-data

file: [image/pdf file]
```

## Testing

### cURL Examples

```bash
# Test health
curl http://localhost:8003/health

# Extract pay stub
curl -X POST http://localhost:8003/extract/paystub \
  -F "file=@/path/to/paystub.pdf"

# Extract W-2
curl -X POST http://localhost:8003/extract/w2 \
  -F "file=@/path/to/w2.pdf"
```

### Python Example

```python
import requests

# Upload document
with open('paystub.pdf', 'rb') as f:
    files = {'file': f}
    response = requests.post(
        'http://localhost:8003/extract/paystub',
        files=files
    )

    result = response.json()
    print(f"Extracted income: ${result['extracted_data']['gross_income_ytd']}")
    print(f"Confidence: {result['confidence_score']}%")
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_HOST` | `http://localhost:11434` | OLLAMA API host |
| `OCR_PRIMARY_MODEL` | `granite3.2-vision` | Primary extraction model |
| `OCR_FALLBACK_MODEL` | `llama3.2-vision:11b` | Fallback if primary fails |
| `CONFIDENCE_THRESHOLD` | `70` | Minimum confidence score (0-100) |
| `DATABASE_URL` | PostgreSQL connection | Shared database |

## Model Selection

### Granite3.2-vision (Primary)
- **Specialization**: Tables, charts, financial documents
- **Speed**: Fast
- **Accuracy**: Excellent for structured forms
- **Best For**: W-2s, paystubs with tables

### Llama 3.2 Vision:11b (Fallback)
- **Specialization**: General document understanding
- **Speed**: Moderate
- **Accuracy**: Very high for text-heavy documents
- **Best For**: Tax returns, bank statements with prose

## Confidence Scoring

The service calculates confidence based on completeness:

- **90-100%**: All required fields extracted
- **70-89%**: Most fields extracted, minor gaps
- **50-69%**: Partial extraction, manual review needed
- **<50%**: Low confidence, reprocessing recommended

### Required Fields by Document Type

**Pay Stub:**
- employee_name
- gross_income
- pay_period

**W-2:**
- employee_name
- tax_year
- box_1_wages

**Bank Statement:**
- account_holder
- statement_period
- ending_balance

**Tax Return:**
- taxpayer_name
- tax_year
- adjusted_gross_income

**Schedule C:**
- business_name
- tax_year
- net_profit_loss

## Integration with Income Engine

The OCR service integrates with the income qualification engine:

```python
# 1. Extract documents via OCR
paystub_data = ocr_service.extract_paystub(file)
w2_data = ocr_service.extract_w2(file)

# 2. Feed to income engine
from calculator.income_engine import IncomeQualificationEngine

engine = IncomeQualificationEngine(
    loan_type='fannie_mae',
    loan_amount=400000,
    property_value=500000
)

result = engine.calculate_qualifying_income(
    w2_documents=[w2_data['extracted_data']],
    paystub_documents=[paystub_data['extracted_data']]
)

print(f"Qualifying income: ${result['total_qualifying_income']:,.2f}")
```

## Error Handling

### Common Errors

1. **OLLAMA not running**
   ```
   Error: Connection refused to http://localhost:11434
   Solution: Start OLLAMA with `ollama serve`
   ```

2. **Model not found**
   ```
   Error: Model 'granite3.2-vision' not found
   Solution: Pull model with `ollama pull granite3.2-vision`
   ```

3. **Low confidence**
   ```
   Warning: Confidence score 45% below threshold 70%
   Solution: Try better quality scan or alternative model
   ```

## Performance

- **Pay Stub**: ~1.5-2 seconds per document
- **W-2**: ~2-3 seconds per document
- **Bank Statement**: ~3-5 seconds per document
- **Tax Return**: ~3-6 seconds per document

## Logging

Logs are stored in `logs/ocr_service.log`:
- Rotation: Every 100 MB
- Retention: 30 days
- Format: JSON structured logs

```bash
# View logs
tail -f logs/ocr_service.log

# In Docker
docker-compose logs -f ocr-service
```

## Security

- No API key required for local OLLAMA
- Documents processed in memory
- Temporary files deleted immediately
- No data stored permanently
- PII extracted but not logged

## Future Enhancements

- [ ] MonkeyOCR-Apple-Silicon integration (3x faster on M-series)
- [ ] Batch processing endpoint
- [ ] Confidence improvement via ensemble models
- [ ] Custom fine-tuning for specific document formats
- [ ] Support for handwritten annotations
- [ ] Multi-page PDF processing

## Troubleshooting

### Service won't start

```bash
# Check OLLAMA is running
curl http://localhost:11434/api/version

# Check models are installed
ollama list

# Check port 8003 is available
lsof -i :8003
```

### Low extraction accuracy

1. Ensure document is high resolution (300+ DPI)
2. Try alternative model (fallback automatically used)
3. Check document isn't heavily redacted
4. Verify document type matches endpoint

### Slow processing

1. Check OLLAMA is using GPU acceleration
2. Consider smaller models for simpler documents
3. Batch multiple documents together
4. Scale horizontally with more containers

## Support

- **Documentation**: See `docs/PROJECT_ARCHITECTURE.md`
- **Issues**: Report via project management
- **Developer**: Neumann Rashid AI Development

---

**Created by:** Neumann Rashid AI Development
**Date:** November 8, 2025
**Version:** 1.0.0
