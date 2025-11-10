# Pricing Adapter - Usage Guide

## Overview

The Pricing Adapter provides a plug-in interface for investor bot/API pricing with **3 rails logic**:
1. **Rate** - Interest rate variations
2. **Points** - Origination points (cost to borrower)
3. **Credit** - Lender credits (rebate to borrower)

## Architecture

```
PricingAdapter (Abstract Base)
    ├── MockPricingAdapter (Testing)
    ├── OptimalBluePricingAdapter (Production - not implemented yet)
    └── CustomPricingAdapter (Your implementation)

PricingService
    ├── Primary Adapter
    └── Fallback Adapter (optional)
```

## Quick Start

### 1. Basic Usage with Mock Adapter

```python
from decimal import Decimal
from calculator.pricing_adapter import (
    LoanParameters,
    MockPricingAdapter,
    PricingService,
)

# Create loan parameters
loan_params = LoanParameters(
    loan_amount=Decimal('400000'),
    property_value=Decimal('500000'),
    credit_score=720,
    loan_type='conventional',
    occupancy='primary',
    property_type='single_family',
    loan_term_months=360,
    loan_purpose='purchase',
    documentation_type='full_doc',
)

# Initialize adapter
adapter = MockPricingAdapter()

# Get pricing
response = adapter.get_pricing(loan_params)

# Check for errors
if response.error:
    print(f"Error: {response.error}")
else:
    print(f"Found {len(response.options)} pricing options")

    # Get best rate option
    best_rate = response.get_best_rate_option()
    print(f"Best rate: {best_rate.rate}% with {best_rate.points}% points")

    # Get zero cost option
    zero_cost = response.get_zero_cost_option()
    print(f"Zero cost rate: {zero_cost.rate}%")

    # Get max credit option
    max_credit = response.get_max_credit_option()
    print(f"Max credit: ${max_credit.credit} at {max_credit.rate}%")
```

### 2. Using PricingService with Fallback

```python
from calculator.pricing_adapter import PricingService

# Setup with fallback
primary = MockPricingAdapter()
fallback = MockPricingAdapter()

service = PricingService(
    primary_adapter=primary,
    fallback_adapter=fallback
)

# Get pricing (automatically falls back if primary fails)
response = service.get_pricing(loan_params)
```

### 3. Storing Scenarios in Database

```python
from api.models import PricingScenario, PricingAuditLog
from django.contrib.auth.models import User

# Get pricing
response = adapter.get_pricing(loan_params)

# Save to database
user = User.objects.get(username='loan_officer')

scenario = PricingScenario.objects.create(
    user=user,
    loan_amount=loan_params.loan_amount,
    property_value=loan_params.property_value,
    credit_score=loan_params.credit_score,
    loan_type=loan_params.loan_type,
    occupancy=loan_params.occupancy,
    property_type=loan_params.property_type,
    loan_term_months=loan_params.loan_term_months,
    loan_purpose=loan_params.loan_purpose,
    documentation_type=loan_params.documentation_type,
    pricing_options=[
        {
            'rate': str(opt.rate),
            'points': str(opt.points),
            'credit': str(opt.credit),
            'lock_days': opt.lock_days,
            'program_name': opt.program_name,
            'notes': opt.notes,
        }
        for opt in response.options
    ],
    pricing_provider=response.provider,
    execution_time_ms=response.execution_time_ms,
    name="Primary Residence Conventional 30yr",
)

# Optionally log audit trail
if settings.PRICING_ENABLE_AUDIT_LOG:
    PricingAuditLog.objects.create(
        user=user,
        pricing_scenario=scenario,
        pricing_provider=response.provider,
        request_parameters={
            'loan_amount': str(loan_params.loan_amount),
            'credit_score': loan_params.credit_score,
            'ltv': str(loan_params.ltv_ratio),
        },
        response_data={
            'option_count': len(response.options),
            'execution_time_ms': response.execution_time_ms,
        },
        execution_time_ms=response.execution_time_ms,
        status='success',
    )
```

## Understanding the 3 Rails

The pricing adapter generates multiple options demonstrating the trade-off between rate, points, and credit:

| Rail | Description | Example |
|------|-------------|---------|
| **Best Rate** | Lowest rate, highest points | 6.500% with 2.0% points |
| **Par Rate** | No points, no credit | 7.000% with 0% points |
| **Max Credit** | Highest credit, highest rate | 7.500% with $8,000 credit |

**Trade-offs:**
- Lower rate = Pay more upfront (points)
- Higher rate = Receive lender credit
- Zero cost = Middle rate, no upfront cost

## Implementing Custom Adapter

```python
from calculator.pricing_adapter import PricingAdapter, PricingResponse
from typing import Tuple, List
import requests

class OptimalBluePricingAdapter(PricingAdapter):
    """
    Production adapter for OptimalBlue API.
    """

    def get_pricing(self, loan_params: LoanParameters) -> PricingResponse:
        """
        Get pricing from OptimalBlue API.
        """
        # Validate first
        is_valid, errors = self.validate_parameters(loan_params)
        if not is_valid:
            return PricingResponse(
                options=[],
                loan_parameters=loan_params,
                timestamp=datetime.now(),
                provider="OptimalBlue",
                error="; ".join(errors),
            )

        try:
            # Call external API
            response = requests.post(
                f"{self.api_url}/pricing",
                headers={'Authorization': f'Bearer {self.api_key}'},
                json={
                    'loan_amount': float(loan_params.loan_amount),
                    'credit_score': loan_params.credit_score,
                    'ltv': float(loan_params.ltv_ratio),
                    # ... more fields
                },
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()

            data = response.json()

            # Convert to PricingOption objects
            options = [
                PricingOption(
                    rate=Decimal(str(opt['rate'])),
                    points=Decimal(str(opt['points'])),
                    credit=Decimal(str(opt['credit'])),
                    lock_days=opt.get('lock_days', 30),
                    program_name=opt.get('program_name', ''),
                )
                for opt in data['options']
            ]

            return PricingResponse(
                options=options,
                loan_parameters=loan_params,
                timestamp=datetime.now(),
                provider="OptimalBlue",
                request_id=data.get('request_id', ''),
            )

        except Exception as e:
            logger.error(f"OptimalBlue API error: {e}", exc_info=True)
            raise PricingError(str(e), code="API_ERROR")

    def validate_parameters(self, loan_params: LoanParameters) -> Tuple[bool, List[str]]:
        """
        Validate loan parameters for OptimalBlue.
        """
        errors = []

        if loan_params.loan_amount < 50000:
            errors.append("Minimum loan amount is $50,000")

        if loan_params.credit_score < 580:
            errors.append("Minimum credit score is 580")

        # Add more validation...

        return (len(errors) == 0, errors)
```

## Configuration

Add to `.env` or environment variables:

```bash
# Pricing Adapter Configuration
PRICING_PROVIDER=mock  # or 'optimal_blue', 'encompass', etc.
PRICING_API_KEY=your_api_key_here
PRICING_API_URL=https://api.optimalblue.com/v1
PRICING_API_TIMEOUT=30

# Enable audit logging
PRICING_ENABLE_AUDIT_LOG=true

# Cache pricing results (seconds)
PRICING_CACHE_TTL=300
```

## Testing

Run unit tests:

```bash
# Via Docker
docker-compose exec backend python -m pytest calculator/test_pricing_adapter.py -v

# Local (with venv activated)
pytest calculator/test_pricing_adapter.py -v
```

All 27 tests should pass.

## Models

### PricingScenario
Stores loan parameters and pricing options for a specific scenario.

**Key Fields:**
- `loan_amount`, `property_value`, `credit_score` - Loan parameters
- `pricing_options` - JSON array of pricing options
- `selected_option_index` - User's selected option
- `pricing_provider` - Adapter name (e.g., "MockInvestor")

### PricingAuditLog
Audit trail for all pricing API calls.

**Key Fields:**
- `request_parameters` - Full request sent to API
- `response_data` - Full API response
- `execution_time_ms` - API latency
- `status` - success/error/timeout

## Security Considerations

1. **API Keys**: Store in environment variables, never commit to code
2. **Rate Limiting**: Implement throttling to avoid API overuse
3. **PII Protection**: Pricing parameters may contain sensitive borrower data
4. **Audit Logging**: All pricing requests are logged for compliance
5. **Input Validation**: Always validate loan parameters before API calls

## Production Checklist

- [ ] Implement production adapter (OptimalBlue, Encompass, etc.)
- [ ] Configure API keys in secure environment variables
- [ ] Set up pricing result caching (Redis recommended)
- [ ] Enable audit logging for compliance
- [ ] Configure fallback adapter for high availability
- [ ] Set up monitoring/alerting for API failures
- [ ] Test with production API in staging environment
- [ ] Document adapter-specific configuration

## Support

For questions or issues:
- Check logs: `docker-compose logs backend`
- Review audit logs: `PricingAuditLog.objects.filter(status='error')`
- Run Django check: `python manage.py check`
