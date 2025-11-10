# How to View Maryland Scraping Results

**Results File:** `tests/maryland_counties_complete.json`
**File Size:** 71 KB
**Lines:** 1,980

## Quick View Commands

### View summary statistics
```bash
python3 -c "
import json
with open('tests/maryland_counties_complete.json') as f:
    data = json.load(f)
    print(f'Total Counties: {data[\"total_counties\"]}')
    print(f'Success Rate: {data[\"scraped_successfully\"]}/{data[\"total_counties\"]}')
    print(f'Duration: {data[\"total_duration_minutes\"]:.2f} minutes')
"
```

### View specific county
```bash
python3 -c "
import json
import sys
county_name = sys.argv[1] if len(sys.argv) > 1 else 'Montgomery'
with open('tests/maryland_counties_complete.json') as f:
    data = json.load(f)
    county = [c for c in data['counties'] if c['county_name'] == county_name][0]
    print(json.dumps(county, indent=2))
" Montgomery
```

### View all property tax rates
```bash
python3 -c "
import json
with open('tests/maryland_counties_complete.json') as f:
    data = json.load(f)
    print('COUNTY                 | PROPERTY TAX | TRANSFER TAX')
    print('-' * 55)
    for c in sorted(data['counties'], key=lambda x: x['county_name']):
        if c.get('success'):
            pt = c['property_tax']['total_rate']
            tt = c['transfer_tax']['county_rate']
            print(f'{c[\"county_name\"]:<22} | {pt:.4f} ({pt*100:.2f}%) | {tt:.4f}')
"
```

### View data quality metrics
```bash
python3 -c "
import json
with open('tests/maryland_counties_complete.json') as f:
    data = json.load(f)
    print('COUNTY                 | COMPLETENESS | CONFIDENCE | DURATION')
    print('-' * 65)
    for c in sorted(data['counties'], key=lambda x: x.get('data_completeness', 0), reverse=True):
        if c.get('success'):
            comp = c.get('data_completeness', 0)
            conf = c.get('scraper_confidence', 0)
            dur = c.get('scrape_duration_seconds', 0)
            print(f'{c[\"county_name\"]:<22} | {comp:>3}%         | {conf:>3}%       | {dur:>4.1f}s')
"
```

### Export to CSV
```bash
python3 << 'EOF'
import json
import csv

with open('tests/maryland_counties_complete.json') as f:
    data = json.load(f)

with open('tests/maryland_tax_rates.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['County', 'Property Tax Rate', 'Property Tax %', 'State Transfer Tax',
                     'County Transfer Tax', 'Recording Fee (Deed)', 'Completeness', 'Confidence'])

    for c in sorted(data['counties'], key=lambda x: x['county_name']):
        if c.get('success'):
            writer.writerow([
                c['county_name'],
                c['property_tax']['total_rate'],
                f"{c['property_tax']['total_rate'] * 100:.2f}%",
                c['transfer_tax']['state_rate'],
                c['transfer_tax']['county_rate'],
                c['recording_fees']['deed']['flat'],
                f"{c['data_completeness']}%",
                f"{c['scraper_confidence']}%"
            ])

print('✅ Exported to tests/maryland_tax_rates.csv')
EOF
```

## JSON Structure

The complete JSON file contains:

```json
{
  "test_timestamp": "2025-11-08T...",
  "state": "Maryland",
  "state_code": "MD",
  "total_counties": 24,
  "scraped_successfully": 23,
  "failed_counties": [...],
  "counties": [
    {
      "county_name": "...",
      "state": "MD",
      "success": true,
      "data_completeness": 100,
      "scraper_confidence": 85,

      "property_tax": {
        "total_rate": 0.011234,
        "components": {
          "county": 0.00643,
          "state": 0.0,
          "school": 0.00368
        },
        "billing_schedule": {...}
      },

      "transfer_tax": {
        "state_rate": 0.005,
        "county_rate": 0.01,
        "buyer_seller_split": "..."
      },

      "recordation_tax": {
        "tiers": [...]
      },

      "recording_fees": {
        "deed": {"flat": 50, "per_page": 5},
        "mortgage": {"flat": 80, "per_page": 5}
      },

      "insurance_estimate": {
        "base_premium_per_100k": 650
      },

      "sources_used": [...]
    }
  ]
}
```

## Field Definitions

### Property Tax
- `total_rate`: Total property tax rate as decimal (e.g., 0.011234 = 1.1234%)
- `assessment_ratio`: Percentage of assessed value (typically 100)
- `components`: Breakdown by county, state, municipality, school
- `homestead_cap`: Cap on annual assessment increases
- `reassessment_cycle`: How often properties are reassessed
- `billing_schedule`: When taxes are due

### Transfer Tax
- `state_rate`: State transfer tax rate (usually 0.005 = 0.5%)
- `county_rate`: County transfer tax rate (varies)
- `first_time_buyer_threshold`: Maximum price for exemption
- `first_time_buyer_exemption`: Type of exemption available
- `buyer_seller_split`: Who typically pays

### Recordation Tax
- `tiers`: Different rates based on property value
- `tiers_source`: Where the information came from
- `notes`: Additional details

### Recording Fees
- `deed.flat`: Base fee for recording deed
- `deed.per_page`: Additional cost per page
- `mortgage.flat`: Base fee for recording mortgage
- `mortgage.per_page`: Additional cost per page
- `surcharge`: Additional technology or filing fees

### Insurance Estimate
- `base_premium_per_100k`: Estimated annual premium per $100k of coverage
- `insurance_source`: Source of estimate
- `insurance_confidence`: Confidence in estimate (0-100)

## Example Queries

### Find counties with highest property tax
```bash
python3 -c "
import json
with open('tests/maryland_counties_complete.json') as f:
    data = json.load(f)
    counties = [c for c in data['counties'] if c.get('success')]
    sorted_counties = sorted(counties,
                            key=lambda x: x['property_tax']['total_rate'],
                            reverse=True)
    print('TOP 5 HIGHEST PROPERTY TAX RATES:')
    for c in sorted_counties[:5]:
        rate = c['property_tax']['total_rate']
        print(f'{c[\"county_name\"]}: {rate:.4f} ({rate*100:.2f}%)')
"
```

### Find counties with transfer tax
```bash
python3 -c "
import json
with open('tests/maryland_counties_complete.json') as f:
    data = json.load(f)
    counties = [c for c in data['counties']
                if c.get('success') and c['transfer_tax']['county_rate'] > 0]
    print('COUNTIES WITH COUNTY TRANSFER TAX:')
    for c in sorted(counties, key=lambda x: x['transfer_tax']['county_rate'], reverse=True):
        rate = c['transfer_tax']['county_rate']
        print(f'{c[\"county_name\"]}: {rate:.4f} ({rate*100:.2f}%)')
"
```

### Calculate total closing costs estimate
```bash
python3 -c "
import json
property_value = 500000  # $500k property

with open('tests/maryland_counties_complete.json') as f:
    data = json.load(f)

print(f'ESTIMATED CLOSING COSTS FOR \${property_value:,} PROPERTY')
print('=' * 70)

for c in data['counties']:
    if c.get('success') and c['county_name'] == 'Montgomery':
        # Transfer taxes
        state_transfer = property_value * c['transfer_tax']['state_rate']
        county_transfer = property_value * c['transfer_tax']['county_rate']

        # Recordation tax
        recordation = property_value * 0.0041  # Simplified

        # Recording fees
        deed_fee = c['recording_fees']['deed']['flat'] + (c['recording_fees']['deed']['per_page'] * 3)
        mortgage_fee = c['recording_fees']['mortgage']['flat'] + (c['recording_fees']['mortgage']['per_page'] * 8)

        total = state_transfer + county_transfer + recordation + deed_fee + mortgage_fee

        print(f'State Transfer Tax:     \${state_transfer:>10,.2f}')
        print(f'County Transfer Tax:    \${county_transfer:>10,.2f}')
        print(f'Recordation Tax:        \${recordation:>10,.2f}')
        print(f'Deed Recording:         \${deed_fee:>10,.2f}')
        print(f'Mortgage Recording:     \${mortgage_fee:>10,.2f}')
        print('-' * 70)
        print(f'TOTAL:                  \${total:>10,.2f}')
"
```

## Pretty Print Entire File
```bash
cat tests/maryland_counties_complete.json | python3 -m json.tool | less
```

## Browse Interactively
```bash
python3 << 'EOF'
import json

with open('tests/maryland_counties_complete.json') as f:
    data = json.load(f)

print("Available counties:")
for i, c in enumerate(data['counties'], 1):
    status = "✅" if c.get('success') else "❌"
    print(f"{i:2}. {status} {c['county_name']}")

choice = input("\nEnter county number to view details (or 'q' to quit): ")
if choice.isdigit() and 1 <= int(choice) <= len(data['counties']):
    county = data['counties'][int(choice) - 1]
    print(f"\n{county['county_name']} County, Maryland")
    print("=" * 60)
    if county.get('success'):
        print(f"Completeness: {county['data_completeness']}%")
        print(f"Confidence: {county['scraper_confidence']}%")
        print(f"\nProperty Tax: {county['property_tax']['total_rate']:.4f} ({county['property_tax']['total_rate']*100:.2f}%)")
        print(f"Transfer Tax (State): {county['transfer_tax']['state_rate']:.4f}")
        print(f"Transfer Tax (County): {county['transfer_tax']['county_rate']:.4f}")
        print(f"\nRecording Fees:")
        print(f"  Deed: ${county['recording_fees']['deed']['flat']} + ${county['recording_fees']['deed']['per_page']}/page")
        print(f"  Mortgage: ${county['recording_fees']['mortgage']['flat']} + ${county['recording_fees']['mortgage']['per_page']}/page")
    else:
        print(f"Error: {county.get('error', 'Unknown')}")
EOF
```
