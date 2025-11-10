# Enhanced Tax Data Schema
## Comprehensive Data Model for Mortgage Calculations

Based on feedback for complete property tax, transfer/recordation fees, insurance, and escrow/proration logic.

---

## Complete JSON Schema

```json
{
  "state": "MD",
  "county": "Montgomery",
  "effective_date": "2025-01-01",
  "data_version": "2.0",
  "last_verified": "2025-11-09T00:00:00Z",
  "data_completeness": 95,
  "scraper_confidence": 90,

  "property_tax": {
    "composite_rate_per_100": 1.2012,
    "assessment_ratio": 1.00,
    "homestead_cap_rule": "10% annual cap if primary residence",
    "reassessment_rule": "reassessed at sale and every 3 years",
    "reassessment_cycle": "3 years",

    "components": {
      "county": 0.7123,
      "state": 0.1120,
      "fire": 0.0856,
      "school": 0.2135,
      "special_district": 0.0778
    },

    "billing_cycle": "semi_annual",
    "tax_year_type": "fiscal",
    "fiscal_year_start": "07-01",

    "installments": [
      {
        "name": "1st Half",
        "bill_issue_date": "2025-07-01",
        "due_date": "2025-09-30",
        "covers_period": "2025-07-01 to 2025-12-31"
      },
      {
        "name": "2nd Half",
        "bill_issue_date": "2026-01-01",
        "due_date": "2026-03-31",
        "covers_period": "2026-01-01 to 2026-06-30"
      }
    ],

    "early_payment_discounts": [
      {
        "window": "07-01 to 09-30",
        "discount_pct": 0
      }
    ],

    "penalties_interest": "1.5% per month after due date",

    "municipalities": [
      {
        "name": "Rockville",
        "zip_codes": ["20850", "20851", "20852"],
        "municipality_rate_per_100": 0.05,
        "composite_rate_per_100": 1.2512,
        "billing_integration": "separate_bill"
      },
      {
        "name": "Gaithersburg",
        "zip_codes": ["20877", "20878", "20879"],
        "municipality_rate_per_100": 0.04,
        "composite_rate_per_100": 1.2412,
        "billing_integration": "combined_bill"
      }
    ],

    "special_assessments": [
      {
        "name": "Front Foot Benefit",
        "type": "linear",
        "annual_amount": 250,
        "expires_year": 2032,
        "due_date": "2025-09-30",
        "description": "Street improvement assessment"
      },
      {
        "name": "Stormwater Management",
        "type": "flat",
        "annual_amount": 120,
        "ongoing": true,
        "due_date": "2025-09-30",
        "description": "Impervious surface fee"
      }
    ],

    "exemptions": {
      "homestead": {
        "available": true,
        "max_credit": 0,
        "annual_increase_cap_pct": 10,
        "requirements": "Primary residence, owner-occupied"
      },
      "senior": {
        "available": true,
        "max_credit": 50000,
        "age_requirement": 65,
        "income_limit": 60000
      },
      "disabled": {
        "available": true,
        "max_credit": 50000,
        "requirements": "100% disabled veteran or Social Security disability"
      }
    }
  },

  "transfer_tax": {
    "state_rate": 0.005,
    "county_rate": 0.01,
    "total_rate": 0.015,

    "payer_split": {
      "buyer": 0.5,
      "seller": 0.5,
      "note": "Customarily split 50/50, negotiable"
    },

    "first_time_buyer": {
      "available": true,
      "threshold": 500000,
      "state_rate_reduction": 0.0025,
      "effective_state_rate": 0.0025,
      "payer_split_override": {
        "buyer": 0.0,
        "seller": 1.0,
        "note": "Seller pays state portion for FTHB"
      },
      "requirements": [
        "No ownership of principal residence in last 3 years",
        "Purchase price under $500,000",
        "Must be primary residence"
      ]
    },

    "calculation_basis": "purchase_price",
    "notes": "Transfer tax calculated on consideration/purchase price"
  },

  "recordation_tax": {
    "tiers": [
      {
        "min_value": 0,
        "max_value": 500000,
        "rate_per_500": 4.45,
        "description": "First $500K"
      },
      {
        "min_value": 500000,
        "max_value": null,
        "rate_per_500": 6.75,
        "description": "$500K and above"
      }
    ],

    "school_increment": {
      "included": true,
      "rate_per_500": 0.50,
      "description": "One-time school construction fee"
    },

    "payer_split": {
      "buyer": 1.0,
      "seller": 0.0,
      "note": "Typically paid by buyer"
    },

    "calculation_basis": "loan_amount",
    "notes": "Recordation tax on mortgage/deed of trust"
  },

  "recording_fees": {
    "deed": {
      "base_fee": 50,
      "per_page": 5,
      "surcharge": 40,
      "tech_fee": 10,
      "total_typical": 110,
      "payer": "buyer"
    },

    "mortgage": {
      "base_fee": 80,
      "per_page": 5,
      "surcharge": 40,
      "tech_fee": 10,
      "total_typical": 145,
      "payer": "buyer"
    },

    "release": {
      "base_fee": 30,
      "per_page": 3,
      "surcharge": 0,
      "tech_fee": 5,
      "total_typical": 41,
      "payer": "seller"
    },

    "page_assumptions": {
      "deed_pages": 4,
      "mortgage_pages": 15,
      "release_pages": 2
    },

    "notes": "Fees collected by clerk of court for recording documents"
  },

  "title_fees": {
    "title_search": {
      "typical_fee": 250,
      "description": "Title search and examination",
      "payer": "buyer"
    },

    "title_insurance": {
      "lenders_policy": {
        "rate_per_1000": 3.50,
        "minimum": 300,
        "description": "Required by lender",
        "payer": "buyer"
      },
      "owners_policy": {
        "rate_per_1000": 5.00,
        "minimum": 500,
        "description": "Protects buyer's equity",
        "payer": "buyer",
        "optional": true
      },
      "simultaneous_issue_discount": 0.10
    },

    "settlement_fee": {
      "typical_fee": 750,
      "description": "Title company closing fee",
      "payer": "split"
    }
  },

  "insurance_estimate": {
    "homeowners": {
      "base_premium_per_100k": 650,
      "avg_rate_per_1000": 6.50,
      "source": "NAIC state average 2024",

      "risk_modifiers": {
        "flood_zone": 0.15,
        "coastal": 0.20,
        "urban": 0.00,
        "high_crime": 0.05,
        "wildfire_zone": 0.25
      },

      "dwelling_coverage_multiplier": 1.0,
      "deductible_standard": 1000,

      "escrow_months": 12,
      "initial_deposit_months": 2
    },

    "flood": {
      "required_if": "FEMA flood zone A, AE, VE",
      "avg_annual_premium": 700,
      "avg_rate_per_1000": 2.00,
      "source": "NFIP average",
      "payer": "buyer",
      "escrowed": false
    },

    "pmi": {
      "required_ltv": 80,
      "rate_range": "0.3% to 1.5% of loan amount annually",
      "note": "Required if down payment < 20%"
    }
  },

  "escrow_rules": {
    "cushion_months": 2,
    "analysis_frequency": "annual",
    "shortage_payment_months": 12,
    "surplus_threshold": 50,

    "items_escrowed": [
      "property_tax",
      "homeowners_insurance",
      "flood_insurance",
      "mortgage_insurance"
    ],

    "respa_compliance": {
      "aggregate_limit": "1/6 of annual escrow items",
      "initial_deposit_max": "2 months of escrow payments + amount needed to cover bills until first payment"
    }
  },

  "proration_rules": {
    "property_tax": {
      "basis": "365_day_year",
      "seller_responsible_through": "day_before_closing",
      "calculation_method": "daily_rate",

      "paid_status_scenarios": {
        "unpaid": "Buyer receives credit for full year, pays at due date",
        "partially_paid": "Prorate based on period paid",
        "paid_in_full": "Seller receives credit for unused portion"
      }
    },

    "hoa_fees": {
      "proration_basis": "monthly",
      "paid_in_advance": true
    },

    "utilities": {
      "final_reading_responsibility": "seller",
      "proration": "to_closing_date"
    }
  },

  "sources": [
    {
      "url": "https://www.montgomerycountymd.gov/finance/",
      "type": "official_government",
      "accessed": "2025-11-09",
      "section": "Property Tax Information"
    },
    {
      "url": "https://www.dat.state.md.us/",
      "type": "state_agency",
      "accessed": "2025-11-09",
      "section": "Transfer & Recordation Tax Rates"
    },
    {
      "url": "https://montgomerycountymd.gov/dgs/Resources/Files/SDU/recording_fees.pdf",
      "type": "fee_schedule",
      "accessed": "2025-11-09",
      "section": "Recording Fees"
    }
  ],

  "metadata": {
    "scraper_version": "2.0",
    "extraction_timestamp": "2025-11-09T00:00:00Z",
    "validation_status": "verified",
    "next_review_date": "2026-01-01",
    "compliance_notes": "RESPA compliant, CFPB Loan Estimate compatible"
  }
}
```

---

## Calculation Formulas

### 1. Annual Property Tax
```python
assessed_value = purchase_price * assessment_ratio
annual_property_tax = assessed_value * (composite_rate_per_100 / 100)

# With municipality overlay
if municipality:
    annual_property_tax = assessed_value * (municipality_composite_rate / 100)

# Add special assessments
annual_property_tax += sum(special_assessments)
```

### 2. Transfer Taxes
```python
# Standard calculation
state_transfer = price * state_rate
county_transfer = price * county_rate
total_transfer = state_transfer + county_transfer

# First-time homebuyer
if first_time_buyer and price <= threshold:
    state_transfer = price * effective_state_rate
    # Seller pays state portion
    buyer_pays = county_transfer
    seller_pays = state_transfer
else:
    # Standard 50/50 split (or as negotiated)
    buyer_pays = total_transfer * payer_split.buyer
    seller_pays = total_transfer * payer_split.seller
```

### 3. Recordation Tax (Tiered)
```python
total_recordation = 0
remaining = loan_amount

for tier in tiers:
    if tier.max_value:
        taxable = min(remaining, tier.max_value - tier.min_value)
    else:
        taxable = remaining

    increments = ceil(taxable / 500)
    total_recordation += increments * tier.rate_per_500
    remaining -= taxable

    if remaining <= 0:
        break

# Add school increment
if school_increment.included:
    increments = ceil(loan_amount / 500)
    total_recordation += increments * school_increment.rate_per_500
```

### 4. Recording Fees
```python
deed_fee = deed.base_fee + (deed_pages * deed.per_page) + deed.surcharge + deed.tech_fee
mortgage_fee = mortgage.base_fee + (mortgage_pages * mortgage.per_page) + mortgage.surcharge + mortgage.tech_fee
total_recording = deed_fee + mortgage_fee
```

### 5. Homeowners Insurance
```python
dwelling_coverage = purchase_price * dwelling_coverage_multiplier
base_premium = (dwelling_coverage / 1000) * avg_rate_per_1000

# Apply risk modifiers
risk_multiplier = 1.0
for modifier, increase in risk_modifiers.items():
    if property_has_risk(modifier):
        risk_multiplier += increase

annual_premium = base_premium * risk_multiplier
monthly_escrow = annual_premium / 12
```

### 6. Tax Proration at Closing
```python
# Determine seller's responsibility
tax_year_start = datetime(year, 7, 1)  # Fiscal year
closing_date = ...
seller_days = (closing_date - tax_year_start).days
seller_proration = (annual_tax * seller_days) / 365

# Check paid status
if taxes_paid_status == "unpaid":
    buyer_credit = 0
    buyer_pays_full_year = annual_tax
elif taxes_paid_status == "paid_in_full":
    days_remaining = 365 - seller_days
    buyer_credit = (annual_tax * days_remaining) / 365
else:  # partially_paid
    # Calculate based on which installment paid
    ...
```

### 7. Initial Escrow Deposit
```python
# Find next due date
next_due = find_next_due_date(closing_date, installments)
months_to_due = months_between(closing_date, next_due)

# Calculate monthly escrow
monthly_tax_escrow = annual_tax / 12
monthly_insurance_escrow = annual_insurance / 12
monthly_total = monthly_tax_escrow + monthly_insurance_escrow

# Amount needed at due date
installment_amount = get_installment_amount(next_due)
already_collected = months_to_due * monthly_tax_escrow
shortage = max(installment_amount - already_collected, 0)

# Add RESPA cushion (2 months)
initial_escrow = shortage + (2 * monthly_total)

# RESPA aggregate limit check
max_allowed = (annual_tax + annual_insurance) / 6
initial_escrow = min(initial_escrow, max_allowed)
```

---

## Implementation Checklist

### Phase 1: Schema Enhancement
- [ ] Update `TaxData` model to support new JSON structure
- [ ] Add database migration for schema version
- [ ] Update scraper prompts to extract all new fields
- [ ] Add validation for required vs optional fields

### Phase 2: Scraper Updates
- [ ] Extract assessment details (ratio, homestead cap, reassessment)
- [ ] Capture buyer/seller split rules
- [ ] Scrape municipality overlays with ZIP mapping
- [ ] Extract billing cycle and tax year metadata
- [ ] Capture special assessments
- [ ] Get detailed insurance rates with risk modifiers
- [ ] Extract title and clerk fees

### Phase 3: Calculator Enhancement
- [ ] Implement enhanced property tax calculation
- [ ] Add municipality overlay logic
- [ ] Implement buyer/seller transfer tax splits
- [ ] Add FTHB transfer tax exemption logic
- [ ] Implement tiered recordation tax
- [ ] Add dynamic insurance calculation with risk factors
- [ ] Implement proper tax proration logic
- [ ] Calculate initial escrow with RESPA compliance

### Phase 4: Testing & Validation
- [ ] Test with Montgomery County, MD data
- [ ] Test with 3-5 additional counties
- [ ] Validate against manual calculations
- [ ] Test edge cases (FTHB, municipality overlays, special assessments)
- [ ] Verify RESPA compliance

### Phase 5: Documentation
- [ ] Update API documentation
- [ ] Add calculation examples
- [ ] Document all formulas
- [ ] Create compliance notes

---

## Multi-County Test Plan

Test the enhanced schema with these counties:

1. **Montgomery County, MD** - Complex with municipalities, FTHB exemptions
2. **Cook County, IL** - High transfer taxes, different billing cycle
3. **Miami-Dade County, FL** - No state income tax, different assessment rules
4. **Harris County, TX** - Multiple taxing jurisdictions, MUD districts
5. **Los Angeles County, CA** - Prop 13 rules, supplemental assessments

---

## Compliance Notes

- **RESPA**: Initial escrow deposit limits enforced
- **CFPB Loan Estimate**: All fees properly categorized
- **TRID**: 3-day disclosure timeline supported
- **State-specific**: Handles state-by-state variations

---

## Version History

- **v1.0**: Basic property tax, transfer, recordation
- **v2.0**: Added assessment details, billing cycles, municipality overlays, special assessments, enhanced insurance, title fees, proration rules, RESPA compliance
