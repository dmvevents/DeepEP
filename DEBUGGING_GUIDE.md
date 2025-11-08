# Debugging Guide - Real Estate Tax Scraper

## Quick Health Check

### 1. Check All Docker Services
```bash
docker-compose ps
```
**What to look for**: All services should show "Up" and "(healthy)" status

### 2. Check if API is responding
```bash
curl http://localhost:8000/api/health/
```
**Expected output**: `{"status":"healthy","services":{"database":"healthy","cache":"healthy"}}`

### 3. Check if Scraper is responding
```bash
curl http://localhost:8001/health
```
**Expected output**: JSON with status information

---

## Viewing Logs (Most Important for Debugging)

### View ALL logs in real-time
```bash
docker-compose logs -f
```
Press `Ctrl+C` to stop

### View specific service logs

**Backend (Django API)**
```bash
docker-compose logs -f backend
```

**Scraper Service**
```bash
docker-compose logs -f scraper-agent
```

**VLM OCR Service**
```bash
docker-compose logs -f vlm-service
```

**Database**
```bash
docker-compose logs -f postgres
```

**Celery Worker**
```bash
docker-compose logs -f celery
```

### View last 50 lines of a service
```bash
docker-compose logs --tail 50 backend
```

### View logs without timestamp
```bash
docker-compose logs --no-log-prefix backend
```

---

## Testing the API

### 1. List all states
```bash
curl http://localhost:8000/api/states/ | python3 -m json.tool
```

### 2. Get counties for Maryland (state_id = 20)
```bash
curl http://localhost:8000/api/states/20/counties/ | python3 -m json.tool
```

### 3. Get tax data for a specific county
```bash
# Montgomery County, MD
curl http://localhost:8000/api/tax-data/by-location/MD/Montgomery/ | python3 -m json.tool

# Fairfax, VA
curl http://localhost:8000/api/tax-data/by-location/VA/Fairfax/ | python3 -m json.tool

# Philadelphia, PA
curl http://localhost:8000/api/tax-data/by-location/PA/Philadelphia/ | python3 -m json.tool
```

### 4. Test scraper directly
```bash
curl -X POST http://localhost:8001/scrape \
  -H "Content-Type: application/json" \
  -d '{"state": "MD", "county": "Montgomery", "force_refresh": false}' | python3 -m json.tool
```

---

## Database Checks

### Connect to PostgreSQL
```bash
docker-compose exec postgres psql -U admin -d mortgage_calc
```

**Useful queries once connected:**
```sql
-- Count states
SELECT COUNT(*) FROM api_state;

-- Count counties
SELECT COUNT(*) FROM api_county;

-- Count tax data records
SELECT COUNT(*) FROM api_taxdata;

-- See recent tax data
SELECT state_id, county_id, data_completeness, scraper_confidence, last_verified
FROM api_taxdata
WHERE is_current = true
ORDER BY last_verified DESC
LIMIT 10;

-- Exit
\q
```

### Check database from Django shell
```bash
docker-compose exec backend python manage.py shell
```

Then in the shell:
```python
from api.models import State, County, TaxData

# Count records
print(f"States: {State.objects.count()}")
print(f"Counties: {County.objects.count()}")
print(f"Tax Data: {TaxData.objects.count()}")

# Get a specific county
county = County.objects.get(state__code='MD', name='Montgomery')
print(county)

# Get its tax data
tax_data = county.tax_data.filter(is_current=True).first()
print(f"Completeness: {tax_data.data_completeness}%")
print(f"Property Tax Rate: {tax_data.data['property_tax']['total_rate']}")

# Exit
exit()
```

---

## Viewing JSON Results

### View Maryland results (pretty printed)
```bash
cat tests/maryland_counties_complete.json | python3 -m json.tool | less
```

### View VA/DC/PA results
```bash
cat tests/va_dc_pa_results.json | python3 -m json.tool | less
```

### Query specific data from JSON

**Show all Maryland property tax rates:**
```bash
python3 -c "
import json
with open('tests/maryland_counties_complete.json') as f:
    data = json.load(f)
    for c in sorted(data.get('counties', []), key=lambda x: x['county_name']):
        if c.get('success'):
            rate = c['property_tax']['total_rate']
            print(f'{c[\"county_name\"]:<25} {rate:.4f} ({rate*100:.2f}%)')
"
```

**Show counties with issues:**
```bash
python3 -c "
import json
with open('tests/maryland_counties_complete.json') as f:
    data = json.load(f)
    print('Counties with completeness < 90%:')
    for c in data.get('counties', []):
        if c.get('success') and c.get('data_completeness', 0) < 90:
            print(f'  {c[\"county_name\"]}: {c[\"data_completeness\"]}%')
"
```

---

## Frontend Testing

### Open the frontend
```bash
open frontend/index.html
```

Or visit directly:
```
file:///Users/antonalexander/Github/real_estate_app/frontend/index.html
```

### Check browser console for errors
1. Open the frontend in browser
2. Press `F12` or `Cmd+Option+I` (Mac) to open Developer Tools
3. Click "Console" tab
4. Try loading data - any errors will appear here

---

## Common Issues & Solutions

### Issue: Services showing "(unhealthy)"
**Solution**: Check logs to see the error
```bash
docker-compose logs --tail 100 [service-name]
```

### Issue: API returns 404
**Solution**: Check if the endpoint exists
```bash
# List all registered URLs
docker-compose exec backend python manage.py show_urls
```

### Issue: No tax data for a county
**Solution**: Trigger a scrape
```bash
curl -X POST http://localhost:8001/scrape \
  -H "Content-Type: application/json" \
  -d '{"state": "MD", "county": "CountyName", "force_refresh": true}'
```

### Issue: Rate limiting (429 errors)
**Solution**: Check scraper logs and wait 60 seconds
```bash
docker-compose logs scraper-agent | grep "429"
```

### Issue: Database connection errors
**Solution**: Check if PostgreSQL is running
```bash
docker-compose ps postgres
docker-compose logs postgres
```

---

## Restart Services

### Restart specific service
```bash
docker-compose restart backend
docker-compose restart scraper-agent
```

### Restart all services
```bash
docker-compose restart
```

### Rebuild and restart (if code changed)
```bash
docker-compose down
docker-compose up --build -d
```

### Nuclear option (fresh start)
```bash
docker-compose down -v  # WARNING: Deletes database!
docker-compose up --build -d
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py load_jurisdictions
```

---

## Monitoring in Real-Time

### Watch service status continuously
```bash
watch -n 2 'docker-compose ps'
```

### Tail multiple logs simultaneously (use separate terminals)
```bash
# Terminal 1
docker-compose logs -f backend

# Terminal 2
docker-compose logs -f scraper-agent

# Terminal 3
docker-compose logs -f vlm-service
```

---

## Test Scripts Status

### Check if test files exist
```bash
ls -lh tests/*.json
```

### Run system test again
```bash
python3 tests/test_system.py
```

### Re-scrape Maryland
```bash
python3 tests/test_maryland_full.py tests/maryland_new.json
```

### Re-scrape VA/DC/PA
```bash
python3 tests/test_multi_state.py tests/multi_state_new.json
```

---

## Quick Diagnostic Commands

```bash
# Everything in one view
echo "=== DOCKER SERVICES ===" && \
docker-compose ps && \
echo -e "\n=== API HEALTH ===" && \
curl -s http://localhost:8000/api/health/ && \
echo -e "\n\n=== SCRAPER HEALTH ===" && \
curl -s http://localhost:8001/health && \
echo -e "\n\n=== RECENT BACKEND LOGS ===" && \
docker-compose logs --tail 10 backend && \
echo -e "\n=== DATABASE STATUS ===" && \
docker-compose exec postgres psql -U admin -d mortgage_calc -c "SELECT COUNT(*) as tax_records FROM api_taxdata WHERE is_current = true;"
```

---

## Getting Help

If you see errors:
1. **Copy the error message** from the logs
2. **Note which service** is failing
3. **Check when it started** (before/after what action?)
4. **Look for patterns** (does it happen for all counties or just some?)

Common error patterns:
- `429` = Rate limiting (wait and retry)
- `500` = Server error (check backend logs)
- `404` = Not found (check URL/endpoint)
- `Connection refused` = Service not running
- `Timeout` = Service too slow (check resource usage)
