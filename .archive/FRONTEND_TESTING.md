# Frontend Testing Guide

## ✅ CORS Issue Fixed!

**Problem**: The frontend couldn't load data because browsers block requests from `file://` protocol to `http://localhost:8000` unless the server explicitly allows it.

**Solution**: Added `null` to CORS_ALLOWED_ORIGINS in `.env` file and recreated the backend container.

---

## 🧪 Test the Frontend Now

### Step 1: Open the Frontend
```bash
open frontend/index.html
```

Or visit directly: `file:///Users/antonalexander/Github/real_estate_app/frontend/index.html`

### Step 2: Test Loading Data

1. **Select a State**: Choose "Maryland" from the dropdown
2. **Select a County**: Choose "Montgomery" from the dropdown
3. **Click "Load Tax Data"** button
4. **Result**: You should see all the tax data display!

### Step 3: Try Other States

**Virginia:**
- Select "Virginia"
- Choose "Fairfax"
- Load data

**Pennsylvania:**
- Select "Pennsylvania"
- Choose "Philadelphia"
- Load data

**District of Columbia:**
- Select "District of Columbia"
- Choose "District of Columbia"
- Load data

---

## 🔍 If It Still Doesn't Work

### Check Browser Console
1. Open the frontend
2. Press `F12` (or `Cmd+Option+I` on Mac)
3. Click the "Console" tab
4. Try loading data
5. **Look for error messages** (copy them if you see any)

### Check Network Tab
1. In Developer Tools, click "Network" tab
2. Try loading data
3. **Look for red/failed requests**
4. Click on any failed request to see details

### Verify Backend is Running
```bash
# Should return healthy status
curl http://localhost:8000/api/health/

# Should return states list
curl http://localhost:8000/api/states/ | python3 -m json.tool | head -20
```

### Check Backend Logs
```bash
# Watch logs while you test frontend
docker-compose logs -f backend
```

---

## 📊 Expected Data Display

When you successfully load Montgomery County, MD, you should see:

**Property Tax:**
- Total Rate: 1.12%
- County Rate: 0.64%
- State Rate: 0.00%
- School Rate: 0.37%

**Transfer Tax:**
- State Rate: 0.5%
- County Rate: 1.0%

**Recording Fees:**
- Deed: $50 (flat) + $5/page
- Mortgage: $80 (flat) + $5/page

**Insurance Estimate:**
- ~$650 per $100k coverage

**Metadata:**
- Completeness: 100%
- Confidence: 92%
- Last Verified: 2025-11-08

---

## 🎯 What Was Fixed

### Before (Broken):
```
.env:
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:80
```
- Frontend at `file://` → ❌ Blocked by CORS

### After (Fixed):
```
.env:
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:80,null
```
- Frontend at `file://` → ✅ Allowed!

### Command Used:
```bash
docker-compose up -d --force-recreate backend
```
This recreated the container with the new environment variable.

---

## 💡 Alternative: Run Frontend Through HTTP Server

If you still have issues, you can serve the frontend through an HTTP server instead of `file://`:

```bash
# Option 1: Python HTTP server
cd /Users/antonalexander/Github/real_estate_app
python3 -m http.server 3000

# Then visit: http://localhost:3000/frontend/index.html
```

```bash
# Option 2: Node.js http-server (if installed)
cd /Users/antonalexander/Github/real_estate_app/frontend
npx http-server -p 3000

# Then visit: http://localhost:3000
```

With HTTP server, you can use `http://localhost:3000` which is already in CORS_ALLOWED_ORIGINS.

---

## ✅ Success Checklist

- [ ] Backend is running and healthy
- [ ] CORS includes "null" origin
- [ ] Frontend opens in browser
- [ ] State dropdown loads and shows states
- [ ] County dropdown loads when state selected
- [ ] "Load Tax Data" button works
- [ ] Tax data displays correctly
- [ ] No errors in browser console

---

## 🆘 Still Having Issues?

Run this diagnostic:
```bash
echo "=== Backend Health ===" && \
curl -s http://localhost:8000/api/health/ && \
echo -e "\n\n=== CORS Config ===" && \
docker-compose exec -T backend python -c "from config.settings import CORS_ALLOWED_ORIGINS; print(CORS_ALLOWED_ORIGINS)" && \
echo -e "\n=== Test API ===" && \
curl -s http://localhost:8000/api/states/ | python3 -c "import sys, json; data=json.load(sys.stdin); print(f\"Found {len(data.get('results', []))} states\")"
```

If everything above works but frontend still fails, check browser console for specific error messages.
