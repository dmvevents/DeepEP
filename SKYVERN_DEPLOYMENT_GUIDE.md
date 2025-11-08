# Skyvern AI Agent Deployment Guide
## Automated Testing & Demo for Mortgage Qualification System

**Created by:** Neumann Rashid AI Development
**Date:** November 8, 2025
**Purpose:** Deploy Skyvern AI agent to automate testing and create impressive demos of the mortgage qualification workflow

---

## 📋 Table of Contents

1. [What is Skyvern?](#what-is-skyvern)
2. [Why Use Skyvern for This Project?](#why-use-skyvern)
3. [System Requirements](#system-requirements)
4. [Installation](#installation)
5. [Configuration](#configuration)
6. [Demo Use Cases](#demo-use-cases)
7. [Example Workflows](#example-workflows)
8. [Integration with Mortgage System](#integration)
9. [Production Deployment](#production-deployment)
10. [Troubleshooting](#troubleshooting)

---

## 🤖 What is Skyvern?

Skyvern is an **AI-powered browser automation platform** that uses:
- **Large Language Models (LLMs)** to understand web pages
- **Computer Vision** to identify UI elements
- **Natural language instructions** instead of brittle XPath selectors

**Key Advantage:** Works across websites without custom code for each site. The AI figures out how to interact with web elements automatically.

---

## 💡 Why Use Skyvern for This Project?

### For Testing
- **Automated E2E Testing**: Test complete qualification workflow without manual intervention
- **Multi-Browser Testing**: Verify functionality across Chrome, Firefox, Safari
- **Regression Testing**: Ensure new changes don't break existing features
- **Load Testing**: Simulate multiple concurrent users

### For Demos
- **Impressive Presentations**: Show AI agent automatically filling forms, uploading documents
- **Investor Demos**: Demonstrate complete workflow in real-time without human intervention
- **Video Marketing**: Record agent completing qualification in 60 seconds
- **Client Onboarding**: Show potential clients how simple the process is

### For Integration
- **Data Population**: Automatically populate test data from external sources
- **Third-Party Integration**: Scrape competitor websites for comparison
- **Report Generation**: Automatically generate and download qualification reports
- **Monitoring**: Verify system uptime and functionality 24/7

---

## 🖥️ System Requirements

### Hardware
- **CPU:** 4+ cores recommended
- **RAM:** 8GB minimum, 16GB recommended
- **Storage:** 5GB for Skyvern + Chrome/browsers
- **OS:** macOS, Linux, or Windows 10+

### Software
- **Python:** 3.11.x (compatible with 3.12, not 3.13)
- **Node.js:** 18+ and npm
- **Docker Desktop:** For containerized deployment
- **Chrome/Chromium:** Included with Skyvern

### For Mac M4 (Your System)
✅ Fully supported with ARM64 architecture
✅ Metal GPU acceleration available
✅ Works with existing OLLAMA setup

---

## 📦 Installation

### Option 1: Quick Start (Recommended for Testing)

```bash
# Navigate to project directory
cd /Users/antonalexander/Github/real_estate_app

# Create Skyvern directory
mkdir skyvern-demo
cd skyvern-demo

# Install Skyvern
pip3 install skyvern

# Initialize Skyvern (creates config files)
skyvern quickstart
```

**Output:**
```
✓ Created .env file
✓ Downloaded browser binaries
✓ Created example workflows
✓ Ready to run!

Next steps:
1. Configure your LLM provider in .env
2. Run: skyvern run all
3. Open: http://localhost:8000
```

### Option 2: Docker Compose (Production)

```bash
cd /Users/antonalexander/Github/real_estate_app/skyvern-demo

# Clone Skyvern repository
git clone https://github.com/Skyvern-AI/skyvern.git
cd skyvern

# Generate .env file
make env

# Configure LLM provider (see Configuration section)
nano .env

# Start Skyvern services
docker compose up -d

# Check status
docker compose ps
```

**Services Started:**
- **skyvern-api** (Port 8000) - Backend API
- **skyvern-ui** (Port 3000) - Web interface
- **postgres** (Port 5432) - Database
- **redis** (Port 6379) - Cache

---

## ⚙️ Configuration

### 1. Configure LLM Provider

Skyvern supports multiple LLM providers. Choose one:

#### Option A: OpenAI (Recommended for Production)
```bash
# Edit .env file
nano .env

# Add your OpenAI API key
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-api-key-here
LLM_MODEL=gpt-4-turbo-preview
```

#### Option B: Anthropic Claude (Best Quality)
```bash
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-your-key-here
LLM_MODEL=claude-3-5-sonnet-20241022
```

#### Option C: OLLAMA (Free, Local - Already Running!)
```bash
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
LLM_MODEL=granite3.2-vision  # Or llama3.2-vision:11b

# Note: Ollama is already running on your system for OCR!
# Reuse the same OLLAMA instance
```

### 2. Configure Browser Settings

```bash
# .env configuration
BROWSER_TYPE=chromium
BROWSER_HEADLESS=false  # Set true for production, false for debugging
BROWSER_VIEWPORT_WIDTH=1920
BROWSER_VIEWPORT_HEIGHT=1080
```

### 3. Configure Network

```bash
# Allow Skyvern to access your local services
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000,file://
```

---

## 🎯 Demo Use Cases

### Use Case 1: Complete Qualification Workflow Demo
**Scenario:** Show investor how AI agent completes entire mortgage qualification

**Steps:**
1. Agent opens qualification workflow page
2. Fills in loan details (property value, loan amount, etc.)
3. Uploads sample documents (paystubs, W-2s)
4. Enters property costs and debts
5. Submits for qualification
6. Displays results with qualification decision

**Demo Impact:**
- Shows end-to-end automation
- Demonstrates OCR integration
- Highlights multi-step workflow
- Proves system works without human intervention

### Use Case 2: Document Upload Testing
**Scenario:** Automated testing of OCR extraction across multiple document types

**Steps:**
1. Agent navigates to document upload page
2. Selects document type (paystub, W-2, etc.)
3. Uploads test document
4. Clicks "Extract Data"
5. Verifies extraction results
6. Validates confidence scores

**Demo Impact:**
- Ensures OCR accuracy
- Tests all 5 document types
- Validates confidence scoring
- Confirms error handling

### Use Case 3: Multi-Guideline Comparison
**Scenario:** Show how system compares qualification across loan types

**Steps:**
1. Agent inputs borrower information
2. Submits same data for Fannie Mae, FHA, and VA
3. Extracts qualification results for each
4. Generates comparison report
5. Screenshots results dashboard

**Demo Impact:**
- Shows system intelligence
- Highlights multi-guideline support
- Demonstrates value proposition
- Creates marketing materials

### Use Case 4: Property Tax Scraper Demo
**Scenario:** Demonstrate automated property tax data retrieval

**Steps:**
1. Agent opens tax scraper interface
2. Inputs property address
3. Triggers tax data scraping
4. Waits for VLM extraction
5. Displays tax data with confidence
6. Shows data completeness metrics

**Demo Impact:**
- Shows proprietary tax scraping
- Highlights 65 jurisdiction coverage
- Demonstrates AI extraction
- Proves data accuracy (98.5%)

---

## 📝 Example Workflows

### Workflow 1: Test Document Upload Page

Create file: `workflows/test_document_upload.py`

```python
from skyvern import Skyvern
import asyncio

async def test_document_upload():
    """Test document upload and OCR extraction"""

    skyvern = Skyvern()

    # Define workflow
    workflow = {
        "url": "file:///Users/antonalexander/Github/real_estate_app/frontend/document_upload.html",
        "steps": [
            {
                "action": "click",
                "description": "Select Pay Stub document type",
                "target": "button containing 'Pay Stub'"
            },
            {
                "action": "upload",
                "description": "Upload paystub document",
                "file_path": "/path/to/sample-paystub.pdf"
            },
            {
                "action": "click",
                "description": "Click Extract Data button",
                "target": "button containing 'Extract Data'"
            },
            {
                "action": "wait",
                "duration": 5000,
                "description": "Wait for extraction to complete"
            },
            {
                "action": "extract",
                "description": "Extract confidence score",
                "schema": {
                    "confidence_score": "number",
                    "extracted_data": "object"
                }
            },
            {
                "action": "screenshot",
                "description": "Capture results",
                "output": "results/document_upload_test.png"
            }
        ]
    }

    # Execute workflow
    result = await skyvern.run_workflow(workflow)

    # Validate results
    assert result['success'], "Workflow failed"
    assert result['data']['confidence_score'] > 70, "Confidence too low"

    print(f"✅ Document Upload Test Passed")
    print(f"Confidence Score: {result['data']['confidence_score']}%")
    print(f"Screenshot saved: results/document_upload_test.png")

    return result

if __name__ == '__main__':
    asyncio.run(test_document_upload())
```

### Workflow 2: Complete Qualification Workflow

Create file: `workflows/complete_qualification_demo.py`

```python
from skyvern import Skyvern
import asyncio

async def complete_qualification_demo():
    """Demonstrate complete mortgage qualification workflow"""

    skyvern = Skyvern()

    workflow = {
        "url": "file:///Users/antonalexander/Github/real_estate_app/frontend/qualification_workflow.html",
        "steps": [
            # Step 1: Loan Details
            {
                "action": "fill",
                "description": "Fill loan details",
                "fields": {
                    "property_value": "500000",
                    "loan_amount": "400000",
                    "interest_rate": "6.5",
                    "loan_term": "30",
                    "loan_type": "fannie_mae",
                    "credit_score": "740"
                }
            },
            {
                "action": "click",
                "description": "Next: Upload Documents",
                "target": "button containing 'Next: Upload Documents'"
            },

            # Step 2: Document Upload
            {
                "action": "upload_multiple",
                "description": "Upload paystubs",
                "file_paths": [
                    "/path/to/paystub1.pdf",
                    "/path/to/paystub2.pdf"
                ]
            },
            {
                "action": "upload_multiple",
                "description": "Upload W-2s",
                "file_paths": [
                    "/path/to/w2_2024.pdf",
                    "/path/to/w2_2023.pdf"
                ]
            },
            {
                "action": "click",
                "description": "Next: Property Costs",
                "target": "button containing 'Next: Property Costs'"
            },

            # Step 3: Property Costs
            {
                "action": "fill",
                "description": "Fill property costs",
                "fields": {
                    "property_tax": "500",
                    "insurance": "150",
                    "hoa_fees": "200"
                }
            },
            {
                "action": "click",
                "description": "Next: Other Debts",
                "target": "button containing 'Next: Other Debts'"
            },

            # Step 4: Other Debts
            {
                "action": "fill",
                "description": "Fill debt information",
                "fields": {
                    "car_payments": "450",
                    "student_loans": "250",
                    "credit_cards": "100"
                }
            },
            {
                "action": "click",
                "description": "Calculate Qualification",
                "target": "button containing 'Calculate Qualification'"
            },

            # Step 5: Wait and Extract Results
            {
                "action": "wait",
                "duration": 3000,
                "description": "Wait for calculation"
            },
            {
                "action": "extract",
                "description": "Extract qualification results",
                "schema": {
                    "qualified": "boolean",
                    "qualified_loan_types": "array",
                    "monthly_income": "number",
                    "housing_payment": "number",
                    "dti_ratio": "number"
                }
            },
            {
                "action": "screenshot",
                "description": "Capture results page",
                "output": "results/qualification_results.png"
            }
        ]
    }

    # Execute workflow with livestream for demo
    result = await skyvern.run_workflow(
        workflow,
        livestream=True,  # Shows browser in real-time
        record_video=True,  # Creates demo video
        video_output="demo_videos/qualification_demo.mp4"
    )

    # Display results
    print("\n" + "="*80)
    print("QUALIFICATION DEMO RESULTS")
    print("="*80)
    print(f"Qualified: {result['data']['qualified']}")
    print(f"Qualified For: {', '.join(result['data']['qualified_loan_types'])}")
    print(f"Monthly Income: ${result['data']['monthly_income']:,.2f}")
    print(f"Housing Payment: ${result['data']['housing_payment']:,.2f}")
    print(f"DTI Ratio: {result['data']['dti_ratio']:.2f}%")
    print(f"\n📸 Screenshot: results/qualification_results.png")
    print(f"🎥 Video: demo_videos/qualification_demo.mp4")
    print("="*80)

    return result

if __name__ == '__main__':
    asyncio.run(complete_qualification_demo())
```

### Workflow 3: Automated Regression Testing

Create file: `workflows/regression_test_suite.py`

```python
from skyvern import Skyvern
import asyncio

async def regression_test_suite():
    """Run complete regression test suite"""

    skyvern = Skyvern()

    test_cases = [
        {
            "name": "High Income, Low DTI - Should Qualify",
            "data": {
                "property_value": 500000,
                "loan_amount": 400000,
                "interest_rate": 6.5,
                "credit_score": 800,
                "monthly_income": 15000,
                "other_debts": 500
            },
            "expected": {"qualified": True}
        },
        {
            "name": "Low Income, High DTI - Should Not Qualify",
            "data": {
                "property_value": 500000,
                "loan_amount": 450000,
                "interest_rate": 7.5,
                "credit_score": 650,
                "monthly_income": 5000,
                "other_debts": 2000
            },
            "expected": {"qualified": False}
        },
        {
            "name": "Borderline Case - FHA Should Qualify",
            "data": {
                "property_value": 300000,
                "loan_amount": 285000,
                "interest_rate": 6.0,
                "credit_score": 680,
                "monthly_income": 7000,
                "other_debts": 800,
                "loan_type": "fha"
            },
            "expected": {"qualified": True}
        }
    ]

    results = []

    for test_case in test_cases:
        print(f"\n🧪 Running: {test_case['name']}")

        result = await skyvern.run_task(
            url="file:///Users/antonalexander/Github/real_estate_app/frontend/qualification_workflow.html",
            prompt=f"Complete the mortgage qualification workflow with these values: {test_case['data']}. Extract the qualification result."
        )

        passed = result['data']['qualified'] == test_case['expected']['qualified']

        results.append({
            "test": test_case['name'],
            "passed": passed,
            "result": result['data']
        })

        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_case['name']}")

    # Generate test report
    print("\n" + "="*80)
    print("REGRESSION TEST REPORT")
    print("="*80)
    total = len(results)
    passed = sum(1 for r in results if r['passed'])
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    print("="*80)

    return results

if __name__ == '__main__':
    asyncio.run(regression_test_suite())
```

---

## 🔗 Integration with Mortgage System

### Integration Points

1. **OCR Service** (Port 8003)
   - Skyvern uploads documents
   - Waits for extraction
   - Validates confidence scores

2. **Backend API** (Port 8000)
   - Triggers qualification calculations
   - Retrieves stored estimates
   - Manages user data

3. **Tax Scraper** (Port 8001)
   - Automates property tax lookup
   - Validates scraped data
   - Tests VLM extraction

4. **Frontend Pages**
   - Document Upload: `frontend/document_upload.html`
   - Qualification Workflow: `frontend/qualification_workflow.html`
   - Tax Data Viewer: `frontend/index.html`
   - Guidelines Reference: `frontend/mortgage_guidelines.html`

### Example: End-to-End System Test

```python
async def test_complete_system():
    """Test all system components together"""

    skyvern = Skyvern()

    # 1. Test Tax Scraper
    print("Testing tax scraper...")
    tax_result = await skyvern.run_task(
        url="http://localhost:8001/scrape/MD/Montgomery",
        prompt="Extract property tax data and validate completeness > 90%"
    )

    # 2. Test OCR Service
    print("Testing OCR service...")
    ocr_result = await skyvern.run_task(
        url="file:///Users/antonalexander/Github/real_estate_app/frontend/document_upload.html",
        prompt="Upload sample paystub and verify extraction with confidence > 70%"
    )

    # 3. Test Complete Qualification
    print("Testing complete qualification workflow...")
    qual_result = await skyvern.run_task(
        url="file:///Users/antonalexander/Github/real_estate_app/frontend/qualification_workflow.html",
        prompt="Complete qualification workflow with property value $500k, loan $400k, credit score 740"
    )

    # 4. Validate Results
    all_passed = (
        tax_result['success'] and
        ocr_result['success'] and
        qual_result['success']
    )

    if all_passed:
        print("\n✅ All System Tests Passed!")
    else:
        print("\n❌ Some Tests Failed - Check Logs")

    return all_passed
```

---

## 🚀 Running Skyvern

### Start Skyvern Service

```bash
# Option 1: CLI (Quick Start)
cd /Users/antonalexander/Github/real_estate_app/skyvern-demo
skyvern run all

# Opens:
# - API: http://localhost:8000
# - UI: http://localhost:3000

# Option 2: Docker Compose
cd /Users/antonalexander/Github/real_estate_app/skyvern-demo/skyvern
docker compose up -d

# Check logs
docker compose logs -f skyvern-api
```

### Access Skyvern UI

1. Open browser: `http://localhost:3000`
2. Create new workflow
3. Configure target URL
4. Define automation steps
5. Run and monitor

### Run Workflow from CLI

```bash
# Using Python script
python3 workflows/complete_qualification_demo.py

# Using Skyvern CLI
skyvern run workflow --file workflows/complete_qualification_demo.json

# With livestream (show browser)
skyvern run workflow --file workflows/complete_qualification_demo.json --livestream

# With video recording
skyvern run workflow --file workflows/complete_qualification_demo.json --record
```

---

## 🎬 Production Deployment

### Deploy Skyvern for Production

1. **Infrastructure Setup**
   ```bash
   # Use Docker Compose in production mode
   docker compose -f docker-compose.prod.yml up -d
   ```

2. **Configure Reverse Proxy (Nginx)**
   ```nginx
   server {
       listen 443 ssl;
       server_name skyvern.yourdomain.com;

       location / {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

3. **Schedule Automated Tests**
   ```bash
   # Add to crontab for nightly testing
   0 2 * * * cd /path/to/skyvern-demo && python3 workflows/regression_test_suite.py
   ```

4. **Monitor & Alerting**
   ```bash
   # Configure health checks
   curl http://localhost:8000/health

   # Set up alerts for failures
   # Use monitoring service (Datadog, New Relic, etc.)
   ```

---

## 🐛 Troubleshooting

### Common Issues

#### Issue 1: Skyvern Can't Find Elements
**Symptom:** "Could not locate element" errors

**Solutions:**
1. Increase wait times between actions
2. Use more descriptive element descriptions
3. Enable visual debugging: `BROWSER_HEADLESS=false`
4. Check element actually exists: Use browser DevTools

#### Issue 2: OLLAMA Connection Failed
**Symptom:** "Failed to connect to OLLAMA at localhost:11434"

**Solutions:**
```bash
# Verify OLLAMA is running
curl http://localhost:11434/api/tags

# Start OLLAMA if not running
ollama serve

# Check firewall settings
# Ensure OLLAMA allows connections from Skyvern
```

#### Issue 3: File Upload Fails
**Symptom:** Documents not uploading to OCR service

**Solutions:**
1. Verify file paths are absolute
2. Check file permissions: `chmod 644 file.pdf`
3. Ensure file size < 10MB
4. Verify OCR service is running: `curl http://localhost:8003/health`

#### Issue 4: Slow Performance
**Symptom:** Workflows take too long

**Solutions:**
1. Use headless mode: `BROWSER_HEADLESS=true`
2. Reduce screenshot resolution
3. Disable unnecessary features
4. Use faster LLM model (GPT-4-turbo vs GPT-4)
5. Optimize workflows (parallel actions where possible)

---

## 📊 Demo Checklist

Before presenting demo to investors/clients:

- [ ] **Services Running**
  - [ ] OLLAMA server (port 11434)
  - [ ] OCR service (port 8003)
  - [ ] Backend API (port 8000)
  - [ ] Tax scraper (port 8001)
  - [ ] Skyvern service (port 8000)
  - [ ] Skyvern UI (port 3000)

- [ ] **Test Data Prepared**
  - [ ] Sample paystubs (2)
  - [ ] Sample W-2s (2)
  - [ ] Sample tax returns (optional)
  - [ ] Property addresses for tax scraping
  - [ ] Borrower scenarios (3-5 examples)

- [ ] **Workflows Tested**
  - [ ] Document upload workflow
  - [ ] Complete qualification workflow
  - [ ] Multi-guideline comparison
  - [ ] Tax scraper demo

- [ ] **Recording Equipment**
  - [ ] Screen recording software ready
  - [ ] Browser window positioned
  - [ ] Demo script prepared
  - [ ] Backup screenshots captured

- [ ] **Presentation Materials**
  - [ ] Demo video rendered (60 seconds)
  - [ ] Screenshots of results
  - [ ] Metrics dashboard (DTI, confidence, etc.)
  - [ ] Comparison chart (Fannie Mae vs FHA vs VA)

---

## 📚 Additional Resources

### Documentation
- **Skyvern Docs:** https://docs.skyvern.com
- **GitHub Repo:** https://github.com/Skyvern-AI/skyvern
- **API Reference:** https://docs.skyvern.com/api

### Community
- **Discord:** Skyvern AI Community
- **GitHub Issues:** Bug reports and feature requests
- **Twitter:** @SkyvernAI

### Project-Specific
- **OCR Service README:** `ocr-service/README.md`
- **Backend Calculator:** `backend/calculator/`
- **Phase 3 Summary:** `PHASE_3_OCR_SUMMARY.md`
- **Project Architecture:** `docs/PROJECT_ARCHITECTURE.md`

---

## 🎯 Quick Start Commands

```bash
# 1. Install Skyvern
pip3 install skyvern
skyvern quickstart

# 2. Configure OLLAMA (already running)
nano .env
# Add: LLM_PROVIDER=ollama
# Add: OLLAMA_BASE_URL=http://localhost:11434

# 3. Start Skyvern
skyvern run all

# 4. Run demo workflow
python3 workflows/complete_qualification_demo.py

# 5. Access UI
open http://localhost:3000
```

---

## 📈 Next Steps

1. **Week 1:** Install and configure Skyvern
2. **Week 2:** Create demo workflows for all pages
3. **Week 3:** Record demo videos
4. **Week 4:** Integrate with CI/CD for automated testing
5. **Week 5:** Deploy to production for monitoring

---

**Status:** Ready for Implementation
**Timeline:** 1-2 weeks for full deployment
**Priority:** High (Demo preparation for investors)

---

**Created by:** Neumann Rashid AI Development
**Contact:** Anton Alexander
**Last Updated:** November 8, 2025
