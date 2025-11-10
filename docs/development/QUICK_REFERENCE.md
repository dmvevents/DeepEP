# Quick Reference - Most Common Commands

## 🚨 When Something Breaks

### 1. Check what's running
```bash
docker-compose ps
```

### 2. View live logs (see errors in real-time)
```bash
# All services
docker-compose logs -f

# Just backend
docker-compose logs -f backend

# Just scraper
docker-compose logs -f scraper-agent
```

Press `Ctrl+C` to stop viewing logs

### 3. Restart everything
```bash
docker-compose restart
```

---

## ✅ Check if Everything Works

### Quick health check (run this first!)
```bash
curl http://localhost:8000/api/health/
```
Should return: `{"status":"healthy",...}`

### Check database
```bash
docker-compose exec postgres psql -U admin -d mortgage_calc -c "SELECT COUNT(*) FROM api_taxdata WHERE is_current = true;"
```

---

## 🔍 View Your Data

### Open the frontend
```bash
open frontend/index.html
```

### Test API for specific county
```bash
# Montgomery, MD
curl http://localhost:8000/api/tax-data/by-location/MD/Montgomery/ | python3 -m json.tool | less

# Fairfax, VA
curl http://localhost:8000/api/tax-data/by-location/VA/Fairfax/ | python3 -m json.tool | less

# Philadelphia, PA
curl http://localhost:8000/api/tax-data/by-location/PA/Philadelphia/ | python3 -m json.tool | less
```

### View JSON results
```bash
# Maryland results
cat tests/multi_state_results.json | python3 -m json.tool | less

# Virginia/DC/PA results
cat tests/va_dc_pa_results.json | python3 -m json.tool | less
```

### Show all property tax rates
```bash
# Maryland
python3 -c "
import json
with open('tests/multi_state_results.json') as f:
    data = json.load(f)
    for c in data['counties']:
        if c.get('success'):
            rate = c['property_tax']['total_rate']
            print(f\"{c['county_name']:<25} {rate:.4f} ({rate*100:.2f}%)\")
"
```

---

## 📊 Current Status Summary

Run this to see everything at once:
```bash
echo "=== SERVICES ===" && docker-compose ps && \
echo -e "\n=== API STATUS ===" && curl -s http://localhost:8000/api/health/ && \
echo -e "\n\n=== DATA COUNT ===" && docker-compose exec -T postgres psql -U admin -d mortgage_calc -c "SELECT COUNT(*) as tax_records FROM api_taxdata WHERE is_current = true;"
```

---

## 🔄 Re-run Scraping

### Scrape single county
```bash
curl -X POST http://localhost:8001/scrape \
  -H "Content-Type: application/json" \
  -d '{"state": "MD", "county": "Montgomery", "force_refresh": true}'
```

### Scrape all Maryland counties again
```bash
python3 tests/test_maryland_full.py tests/maryland_new.json
```

### Scrape VA/DC/PA again
```bash
python3 tests/test_multi_state.py tests/va_dc_pa_new.json
```

---

## 📍 Where Are Things?

- **Frontend**: `frontend/index.html` (open in browser)
- **Test Results**: `tests/*.json` files
- **Documentation**:
  - `COMPLETE_SUMMARY.md` - Full project overview
  - `DEBUGGING_GUIDE.md` - Detailed debugging help
  - `VIEW_RESULTS.md` - How to query JSON data
  - `IMPROVEMENTS.md` - Known issues
- **Logs**: `docker-compose logs [service-name]`

---

## 🎯 What You Have

✅ **65 counties** with complete tax data:
- Maryland: 24 counties (100% success)
- Virginia: 20 counties (100% success)
- DC: 1 jurisdiction (100% success)
- Pennsylvania: 20 counties (100% success)

✅ **Working frontend** at `frontend/index.html`

✅ **Working API** at `http://localhost:8000`

---

## 🆘 Emergency Commands

### Services won't start
```bash
docker-compose down
docker-compose up -d
```

### Need to see what's wrong
```bash
docker-compose logs --tail 100 backend
docker-compose logs --tail 100 scraper-agent
```

### Nuclear option (starts fresh, DELETES ALL DATA!)
```bash
docker-compose down -v
docker-compose up --build -d
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py load_jurisdictions
```

---

## 📱 Contact Info

- Full debugging guide: `DEBUGGING_GUIDE.md`
- Project summary: `COMPLETE_SUMMARY.md`
- View this file in MacDown: `open -a MacDown QUICK_REFERENCE.md`
