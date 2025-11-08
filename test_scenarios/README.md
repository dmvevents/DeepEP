# Test Scenarios for Mortgage Qualification System

**Created:** November 8, 2025
**Purpose:** Comprehensive test scenarios for validation and demo purposes

---

## 📋 Test Scenario Categories

1. **Positive Scenarios** - Should qualify
2. **Negative Scenarios** - Should not qualify
3. **Edge Cases** - Borderline qualifications
4. **Multi-Guideline Comparison** - Different outcomes per loan type
5. **Document Extraction** - OCR testing

---

## ✅ Positive Scenarios (Should Qualify)

### Scenario 1: High Income, Low DTI - Strong Candidate
**Profile:**
- Monthly Income: $12,000
- Credit Score: 780
- Property Value: $500,000
- Loan Amount: $400,000 (20% down)
- Interest Rate: 6.5%
- Other Debts: $500/month

**Property Costs:**
- Property Tax: $500/month
- Insurance: $150/month
- HOA: $0

**Expected Results:**
- ✅ Qualifies for: Fannie Mae, FHA, VA
- Front-End DTI: ~22%
- Back-End DTI: ~26%
- Housing Payment: $2,530/month

**Use Case:** Ideal borrower demo

---

### Scenario 2: First-Time Buyer - FHA Loan
**Profile:**
- Monthly Income: $6,500
- Credit Score: 680
- Property Value: $300,000
- Loan Amount: $289,500 (3.5% down - FHA minimum)
- Interest Rate: 6.75%
- Other Debts: $450/month

**Property Costs:**
- Property Tax: $300/month
- Insurance: $100/month
- HOA: $0

**Expected Results:**
- ✅ Qualifies for: FHA
- ❌ May not qualify for: Fannie Mae (tight margins)
- Front-End DTI: ~38%
- Back-End DTI: ~45%

**Use Case:** Demonstrates FHA flexibility for first-time buyers

---

### Scenario 3: VA Loan - Veteran with Strong Profile
**Profile:**
- Monthly Income: $8,000
- Credit Score: 720
- Property Value: $400,000
- Loan Amount: $400,000 (0% down - VA)
- Interest Rate: 6.25%
- Other Debts: $600/month

**Property Costs:**
- Property Tax: $400/month
- Insurance: $120/month
- HOA: $150/month

**Expected Results:**
- ✅ Qualifies for: VA, Fannie Mae
- Front-End DTI: ~35%
- Back-End DTI: ~43%
- No PMI/MIP required (VA benefit)

**Use Case:** Shows VA loan advantages

---

## ❌ Negative Scenarios (Should Not Qualify)

### Scenario 4: High DTI - Excessive Debt
**Profile:**
- Monthly Income: $5,000
- Credit Score: 650
- Property Value: $400,000
- Loan Amount: $380,000 (5% down)
- Interest Rate: 7.5%
- Other Debts: $2,000/month (high debt load)

**Property Costs:**
- Property Tax: $400/month
- Insurance: $150/month
- HOA: $0

**Expected Results:**
- ❌ Does not qualify for any loan type
- Back-End DTI: ~85% (way over limits)
- Recommendation: Pay down debt or increase income

**Use Case:** Shows system properly rejects unqualified borrowers

---

### Scenario 5: Low Credit Score - Insufficient History
**Profile:**
- Monthly Income: $7,000
- Credit Score: 580
- Property Value: $350,000
- Loan Amount: $332,500 (5% down)
- Interest Rate: 8.0%
- Other Debts: $800/month

**Expected Results:**
- ❌ Does not qualify (credit score below FHA minimum 580)
- Even with acceptable DTI, credit score is disqualifying

**Use Case:** Demonstrates credit score requirements

---

## ⚖️ Edge Cases (Borderline Qualifications)

### Scenario 6: Right at DTI Limit - 50% Back-End
**Profile:**
- Monthly Income: $7,500
- Credit Score: 740
- Property Value: $450,000
- Loan Amount: $360,000 (20% down)
- Interest Rate: 6.5%
- Other Debts: $1,000/month

**Property Costs:**
- Property Tax: $450/month
- Insurance: $135/month
- HOA: $200/month

**Expected Results:**
- ✅ Qualifies for: Fannie Mae (exactly at 50% limit)
- ❌ Does not qualify for: VA (exceeds 41% limit)
- Back-End DTI: ~50.0%

**Use Case:** Tests system accuracy at exact thresholds

---

### Scenario 7: PMI Threshold - 79.9% LTV vs 80.1% LTV
**Profile A (No PMI):**
- Property Value: $500,000
- Loan Amount: $399,500 (79.9% LTV)

**Profile B (With PMI):**
- Property Value: $500,000
- Loan Amount: $400,500 (80.1% LTV)

**Expected Results:**
- Profile A: No PMI required
- Profile B: PMI required (~$167/month)
- DTI difference affects qualification

**Use Case:** Shows importance of 20% down payment threshold

---

## 🏦 Multi-Guideline Comparison Scenarios

### Scenario 8: Qualifies for Some, Not All
**Profile:**
- Monthly Income: $6,000
- Credit Score: 700
- Property Value: $400,000
- Loan Amount: $380,000 (5% down)
- Interest Rate: 6.75%
- Other Debts: $900/month

**Expected Results:**
- ✅ FHA: Qualifies (56% max DTI with compensating factors)
- ⚖️ Fannie Mae: Borderline (needs automated underwriting)
- ❌ VA: Does not qualify (exceeds 41% limit)
- Back-End DTI: ~52%

**Use Case:** Perfect for demonstrating multi-guideline analysis feature

---

### Scenario 9: Self-Employed with Variable Income
**Profile:**
- Monthly Income: $9,000 (averaged from Schedule C)
- Credit Score: 730
- Property Value: $550,000
- Loan Amount: $440,000 (20% down)
- Interest Rate: 6.5%
- Other Debts: $1,200/month

**Documents Required:**
- Schedule C (2 years)
- Personal tax returns (2 years)
- Bank statements (2 months)
- Profit & Loss statement (YTD)

**Expected Results:**
- Qualification depends on income stability
- May require additional documentation
- Demonstrates OCR extraction for Schedule C

**Use Case:** Tests self-employment income calculation

---

## 📄 Document Extraction Test Scenarios

### Scenario 10: Pay Stub Extraction Test
**Documents:**
- `test_paystub_biweekly.pdf` - Biweekly paycheck
- `test_paystub_monthly.pdf` - Monthly salary

**Fields to Extract:**
- Employee name
- Employer name
- Pay period dates
- Gross income (current period)
- YTD gross income
- Deductions (federal, state, FICA)
- Net pay

**Validation:**
- Confidence score > 85%
- All required fields populated
- Gross income matches YTD calculation

---

### Scenario 11: W-2 Extraction Test
**Documents:**
- `test_w2_2024.pdf` - Current year W-2
- `test_w2_2023.pdf` - Previous year W-2

**Fields to Extract:**
- Employee SSN (redacted in demo)
- Employer EIN
- Box 1: Wages, tips, compensation
- Box 2: Federal income tax withheld
- Box 3-6: Social Security/Medicare
- Box 16-17: State wages and tax

**Validation:**
- Confidence score > 90%
- Two-year income comparison
- Income trend analysis

---

### Scenario 12: Bank Statement Extraction Test
**Documents:**
- `test_bank_statement_checking.pdf` - Checking account
- `test_bank_statement_savings.pdf` - Savings account

**Fields to Extract:**
- Account holder name
- Account number (last 4 digits)
- Statement period
- Beginning balance
- Ending balance
- Total deposits
- Total withdrawals
- Average balance

**Validation:**
- Sufficient reserves (2-6 months PITI)
- No NSF fees or overdrafts
- Regular income deposits

---

## 🎯 Demo Scenarios for Presentations

### Demo 1: 60-Second Complete Qualification
**Use:** Investor pitch, client demo

**Flow:**
1. Start timer
2. Load qualification page
3. Auto-fill loan details (via Skyvern)
4. Upload 2 documents
5. Auto-fill property costs
6. Auto-fill debts
7. Submit
8. Display results
9. Stop timer (target: <60 seconds)

**Talking Points:**
- "Watch as our AI completes qualification in under a minute"
- "No manual data entry - OCR extracts everything"
- "Instant multi-guideline comparison"

---

### Demo 2: Document Upload Showcase
**Use:** Feature demonstration

**Flow:**
1. Show blank upload page
2. Drag-drop paystub
3. Watch extraction (real-time)
4. Display confidence score
5. Show extracted data fields
6. Repeat for W-2
7. Compare income sources

**Talking Points:**
- "AI reads documents just like a human underwriter"
- "Confidence scoring ensures accuracy"
- "Handles all major document types"

---

### Demo 3: Multi-Guideline Intelligence
**Use:** Value proposition demonstration

**Flow:**
1. Enter borderline scenario (Scenario 8)
2. Show qualification results
3. Highlight: "Qualifies for FHA, not VA"
4. Explain why
5. Show DTI comparison chart
6. Demonstrate system intelligence

**Talking Points:**
- "Traditional systems test one loan type at a time"
- "Our system analyzes all options simultaneously"
- "Helps borrowers find best loan product"

---

## 📊 Test Data Templates

### Template 1: CSV Format for Bulk Testing
```csv
scenario_id,name,property_value,loan_amount,interest_rate,credit_score,monthly_income,car_payments,student_loans,credit_cards,expected_result
1,High Income Low DTI,500000,400000,6.5,780,12000,300,200,0,qualified
2,FHA First Time,300000,289500,6.75,680,6500,200,250,0,qualified_fha
3,VA Veteran,400000,400000,6.25,720,8000,400,200,0,qualified_va
4,High DTI Reject,400000,380000,7.5,650,5000,1000,500,500,not_qualified
```

### Template 2: JSON Format for API Testing
```json
{
  "scenario": "High Income Low DTI",
  "loan_details": {
    "property_value": 500000,
    "loan_amount": 400000,
    "interest_rate": 6.5,
    "loan_term": 30,
    "loan_type": "fannie_mae",
    "credit_score": 780
  },
  "income": {
    "monthly_gross": 12000,
    "sources": ["w2_salary"]
  },
  "property_costs": {
    "property_tax_monthly": 500,
    "insurance_monthly": 150,
    "hoa_fees_monthly": 0
  },
  "debts": {
    "car_payments": 300,
    "student_loans": 200,
    "credit_cards": 0,
    "personal_loans": 0,
    "other_debts": 0
  },
  "expected_results": {
    "qualified": true,
    "qualified_loan_types": ["fannie_mae", "fha", "va"],
    "back_end_dti_range": [25, 27]
  }
}
```

---

## 🔧 Testing Checklist

### Manual Testing
- [ ] All 12 scenarios tested manually
- [ ] Results match expected outcomes
- [ ] UI displays correctly
- [ ] Error handling works
- [ ] Edge cases handled properly

### Automated Testing (Skyvern)
- [ ] Skyvern configured and running
- [ ] All workflows execute successfully
- [ ] Screenshots captured
- [ ] Videos recorded
- [ ] Test reports generated

### Document OCR Testing
- [ ] Paystub extraction (5 samples)
- [ ] W-2 extraction (5 samples)
- [ ] Tax return extraction (3 samples)
- [ ] Bank statement extraction (3 samples)
- [ ] Confidence scores validated

### Integration Testing
- [ ] OCR → Income Engine → DTI → Results
- [ ] Multi-document processing
- [ ] Error recovery
- [ ] Concurrent requests
- [ ] Database persistence

### Performance Testing
- [ ] Load time < 2 seconds
- [ ] OCR extraction < 5 seconds per document
- [ ] Qualification calculation < 1 second
- [ ] Supports 10 concurrent users
- [ ] No memory leaks

---

## 📈 Success Metrics

**Accuracy Targets:**
- OCR confidence: > 85% average
- Qualification accuracy: 100% (vs manual underwriting)
- DTI calculation precision: ±0.01%

**Performance Targets:**
- Page load: < 2 seconds
- OCR processing: < 5 seconds per document
- Complete workflow: < 60 seconds
- System uptime: > 99.5%

**User Experience Targets:**
- Completion rate: > 90%
- Error rate: < 2%
- User satisfaction: > 4.5/5

---

## 🚀 Next Steps

1. **This Week:**
   - Test all 12 scenarios manually
   - Create sample documents
   - Validate OCR extractions
   - Record demo videos

2. **Next Week:**
   - Deploy Skyvern automation
   - Run regression test suite
   - Performance benchmarking
   - Create investor presentation

3. **Production Prep:**
   - Security audit
   - Load testing
   - Error monitoring
   - Backup procedures

---

**Last Updated:** November 8, 2025
**Owner:** Anton Alexander
**Status:** Ready for Testing
