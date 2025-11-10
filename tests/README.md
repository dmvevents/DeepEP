# Tests Directory

This directory contains all test scripts and test results.

## Test Scripts

### `test_system.py`
Comprehensive system test suite that tests:
- API health checks
- Database reads/writes
- Scraper functionality
- End-to-end workflows

Logs all operations to JSON for debugging and monitoring.

**Usage:**
```bash
python3 tests/test_system.py [output_file]
```

**Default output:** `test_results.json`

## Test Results

Test results are saved as JSON files with the following structure:
- `test_run_timestamp`: When the tests were run
- `total_tests`: Number of tests executed
- `passed`: Number of successful tests
- `failed`: Number of failed tests
- `results`: Array of test operations with:
  - `timestamp`: When the operation was executed
  - `operation`: Description of the operation
  - `endpoint`: API endpoint tested
  - `method`: HTTP method (GET, POST, etc.)
  - `request_data`: Request payload
  - `response_data`: Response data
  - `status_code`: HTTP status code
  - `success`: Boolean indicating success/failure
  - `error`: Error message if failed
  - `duration_ms`: Operation duration in milliseconds

## Running Tests

### All Tests
```bash
python3 tests/test_system.py
```

### With Custom Output Location
```bash
python3 tests/test_system.py logs/test_results_$(date +%Y%m%d_%H%M%S).json
```

### With Docker
```bash
docker-compose exec backend python manage.py test
docker-compose exec backend python manage.py test calculator
docker-compose exec backend python manage.py test api
```
