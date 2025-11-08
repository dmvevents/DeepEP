# Skyvern Demo for Mortgage Qualification System

This directory contains Skyvern AI workflows for automated testing and demo creation.

## Quick Start

1. **Install Skyvern:**
   ```bash
   pip3 install skyvern
   skyvern quickstart
   ```

2. **Configure OLLAMA (already running):**
   ```bash
   # Edit .env and add:
   LLM_PROVIDER=ollama
   OLLAMA_BASE_URL=http://localhost:11434
   LLM_MODEL=granite3.2-vision
   ```

3. **Start Skyvern:**
   ```bash
   skyvern run all
   ```

4. **Access UI:**
   - Open: http://localhost:3000

## Directory Structure

```
skyvern-demo/
├── workflows/           # Automation workflow scripts
│   ├── test_document_upload.py
│   ├── complete_qualification_demo.py
│   └── regression_test_suite.py
├── results/            # Test results and screenshots
├── demo_videos/        # Recorded demo videos
├── .env                # Configuration (created by quickstart)
└── README.md           # This file
```

## Workflows

### 1. Document Upload Test
Tests OCR extraction functionality
```bash
python3 workflows/test_document_upload.py
```

### 2. Complete Qualification Demo
Full end-to-end qualification workflow
```bash
python3 workflows/complete_qualification_demo.py
```

### 3. Regression Test Suite
Automated testing across multiple scenarios
```bash
python3 workflows/regression_test_suite.py
```

## Demo Use Cases

1. **Investor Demos**: Show AI automating entire qualification
2. **Testing**: Automated regression testing
3. **Video Marketing**: Record demos for marketing materials
4. **Integration Testing**: Verify all services work together

## Documentation

See `SKYVERN_DEPLOYMENT_GUIDE.md` in parent directory for full documentation.

## Support

- Skyvern Docs: https://docs.skyvern.com
- GitHub: https://github.com/Skyvern-AI/skyvern
- Project Lead: Anton Alexander
