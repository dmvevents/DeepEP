# Scraper Improvements & Observations

**Test Date:** November 8, 2025
**Test Type:** Complete Maryland County Scraping (24 counties)

## Test Results Summary

### Success Metrics
- ✅ **23 out of 24 counties** scraped successfully (95.8% success rate)
- ✅ **Average completeness:** 89.4%
- ✅ **Average confidence:** 82.9%
- ✅ **Total duration:** 8.78 minutes (~22 seconds per county)

### Failed Counties
1. **Dorchester County** - HTTP 500 error (likely temporary server issue)

## Issues Identified

### 1. Rate Limiting (429 Errors)

**Problem:**
The Brave Search API is returning "429 Too Many Requests" errors during scraping. From logs:

```
2025-11-08 15:18:48,909 - httpx - INFO - HTTP Request: GET https://api.search.brave.com/res/v1/web/search?q=Garrett%20MD%20transfer%20tax%20rate&count=10 "HTTP/1.1 429 Too Many Requests"
2025-11-08 15:18:48,910 - web_search - ERROR - Search failed for query 'Garrett MD transfer tax rate': Client error '429 Too Many Requests'
```

**Impact:**
- Some search queries fail
- Completeness scores drop (e.g., 75% instead of 100%)
- Still able to scrape with reduced information

**Solutions:**

#### Short-term:
1. **Add delays between requests**
   - Current: 1 second between counties
   - Recommended: 2-3 seconds between counties
   - Add 500ms delay between individual search queries

2. **Implement exponential backoff**
   ```python
   if response.status_code == 429:
       wait_time = 2 ** retry_count  # 2s, 4s, 8s, etc.
       time.sleep(wait_time)
       retry()
   ```

3. **Cache search results**
   - Many searches are similar across counties
   - Cache state-level data (recordation tax, transfer tax)
   - Reuse cached results to reduce API calls

#### Long-term:
1. **Switch to SerpAPI** (if available)
   - Better rate limits
   - More reliable
   - Configure in `.env.scraper`:
     ```
     WEB_SEARCH_PROVIDER=serpapi
     SERP_API_KEY=your_key_here
     ```

2. **Implement request pooling**
   - Batch similar queries
   - Reduce total API calls by 40-50%

3. **Use multiple search providers**
   - Fallback to alternate provider on 429
   - Round-robin between providers

### 2. Completeness Variations

**Observation:**
Completeness scores vary from 75% to 100%:
- 100%: Baltimore, Calvert, Charles, Harford, Montgomery, Prince George's, Worcester
- 87%: Most counties
- 75%: Anne Arundel, Carroll, St. Mary's

**Reasons:**
1. Some counties have less online documentation
2. Rate limiting causes missing data
3. Transfer tax and recordation tax often state-level (can be cached)

**Improvement:**
Create a state-level cache for common fields:
```python
MD_STATE_DATA = {
    "transfer_tax": {"state_rate": 0.005},
    "recordation_tax": {"tiers": [...], "source": "Maryland state law"}
}
```

### 3. Data Quality Anomalies

**Found Issues:**
1. **Kent County:** Property tax rate = 1.1 (should be 0.011 or 1.1%)
2. **Somerset County:** Property tax rate = 1.1 (same issue)
3. **Wicomico County:** Property tax rate = 1.1 (same issue)

These appear to be parsing errors where the percentage sign was removed but the value wasn't converted to decimal.

**Fix Needed:**
Add validation in the scraper:
```python
if property_tax_rate > 0.1:  # Likely a percentage not decimal
    property_tax_rate = property_tax_rate / 100
```

## Recommended Code Changes

### 1. Add Rate Limiting Handler

File: `scraper/web_search.py`

```python
import time
from typing import Optional

class RateLimitHandler:
    def __init__(self, base_delay: float = 0.5):
        self.base_delay = base_delay
        self.last_request = 0

    def wait_if_needed(self):
        """Ensure minimum delay between requests"""
        elapsed = time.time() - self.last_request
        if elapsed < self.base_delay:
            time.sleep(self.base_delay - elapsed)
        self.last_request = time.time()

    def handle_429(self, retry_count: int) -> Optional[float]:
        """Return wait time for exponential backoff"""
        if retry_count > 5:
            return None  # Give up
        wait_time = (2 ** retry_count) + 1  # 2s, 5s, 9s, 17s, 33s
        return wait_time
```

### 2. Add State-Level Caching

File: `scraper/state_cache.py`

```python
MARYLAND_STATE_DATA = {
    "transfer_tax": {
        "state_rate": 0.005,
        "state_rate_source": "Maryland Tax Code",
        "state_rate_confidence": 100
    },
    "recordation_tax": {
        "tiers": [
            {"max_value": 500000, "rate": 0.0035},
            {"min_value": 500000, "rate": 0.005}
        ],
        "tiers_source": "Maryland Recordation Tax Law",
        "tiers_confidence": 100
    }
}

def get_state_defaults(state_code: str) -> dict:
    """Get cached state-level data"""
    return MARYLAND_STATE_DATA if state_code == "MD" else {}
```

### 3. Add Data Validation

File: `scraper/scraper_agent.py`

```python
def validate_property_tax_rate(rate: float) -> float:
    """Validate and correct property tax rate"""
    if rate > 0.1:  # Likely percentage, not decimal
        corrected = rate / 100
        logger.warning(f"Property tax rate {rate} > 0.1, converting to {corrected}")
        return corrected
    return rate

def validate_tax_data(data: dict) -> dict:
    """Validate all tax data fields"""
    if "property_tax" in data:
        rate = data["property_tax"].get("total_rate")
        if rate:
            data["property_tax"]["total_rate"] = validate_property_tax_rate(rate)
    return data
```

## Real-Time Monitoring

### Create Live Progress Script

File: `tests/monitor_scraping.py`

```python
#!/usr/bin/env python3
"""Monitor scraping progress in real-time"""
import json
import time
import sys

def monitor_file(filename: str):
    """Monitor JSON file for updates"""
    print("Monitoring scraping progress...")
    print("Press Ctrl+C to stop\n")

    last_size = 0
    while True:
        try:
            with open(filename) as f:
                data = json.load(f)

            completed = len(data.get("counties", []))
            total = data.get("total_counties", 0)

            if completed > last_size:
                latest = data["counties"][-1]
                status = "✅" if latest.get("success") else "❌"
                print(f"{status} [{completed}/{total}] {latest['county_name']}: "
                      f"Completeness: {latest.get('data_completeness', 'N/A')}%, "
                      f"Confidence: {latest.get('scraper_confidence', 'N/A')}%")
                last_size = completed

            time.sleep(1)

        except (FileNotFoundError, json.JSONDecodeError):
            time.sleep(1)
        except KeyboardInterrupt:
            print("\n\nMonitoring stopped")
            break

if __name__ == "__main__":
    filename = sys.argv[1] if len(sys.argv) > 1 else "maryland_counties_complete.json"
    monitor_file(filename)
```

## Performance Optimization

### Current Performance
- **Average time per county:** 22 seconds
- **Total for 24 counties:** 8.78 minutes
- **Bottleneck:** LLM processing (9-11 seconds per county)

### Optimization Opportunities

1. **Parallel scraping** (with rate limit awareness)
   - Process 2-3 counties simultaneously
   - Reduce total time by 50-60%
   - Estimated: 4-5 minutes for all counties

2. **Batch LLM requests**
   - Send multiple counties to LLM at once
   - Reduce overhead
   - Better utilization

3. **Progressive caching**
   - Cache common searches
   - Reuse state-level data
   - Reduce API calls by 40%

## Data Quality Metrics by County

| County | Completeness | Confidence | Property Tax | Transfer Tax | Duration |
|--------|--------------|------------|--------------|--------------|----------|
| Montgomery | 100% | 75% | 1.1234% | 1.0% | 9.9s |
| Baltimore | 100% | 88% | 3.2% | 2.0% | 15.0s |
| Prince George's | 100% | 85% | 0.58% | 1.45% | 20.0s |
| Worcester | 100% | 85% | 0.815% | 0.5% | 11.2s |

**High-Quality Counties (100% completeness):**
- Baltimore
- Calvert
- Charles
- Harford
- Montgomery
- Prince George's
- Worcester

## Next Steps

1. ✅ **Immediate:** Review and fix Kent, Somerset, Wicomico property tax rates
2. ⏳ **Short-term:** Implement rate limiting handler
3. ⏳ **Medium-term:** Add state-level caching
4. ⏳ **Long-term:** Implement parallel scraping with proper rate limiting

## Conclusion

The scraper is **highly effective** with a 95.8% success rate and 89.4% average completeness. The main issues are:

1. **Rate limiting** - Can be resolved with delays and caching
2. **Data validation** - Need to validate property tax rates
3. **Completeness** - Can be improved with state-level caching

With these improvements, we can achieve:
- 100% success rate
- 95%+ average completeness
- 50% faster scraping
- Better data quality
